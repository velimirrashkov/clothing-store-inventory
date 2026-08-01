"""
ALL business logic for catalog. Public function surface of the app (see architecture-spec.md §2.1).

Dependency direction (§2.3): catalog is depended on by inventory/orders/pricing, never the reverse —
this module must not import from those apps. Availability composition (on_hand - reserved) happens in
apps/catalog/api/views.py, which calls apps.inventory.selectors directly as the read-path composition
layer described in §8.1, not here.
"""
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.audit import services as audit

from .models import Product, Variant


@transaction.atomic
def create_product(*, actor, name: str, category_id: int, gender: str, **fields) -> Product:
    slug = fields.pop("slug", None) or _unique_slug(name)
    product = Product.objects.create(name=name, slug=slug, category_id=category_id, gender=gender, **fields)
    audit.record(actor=actor, action="catalog.product_create", object_type="product", object_id=str(product.id))
    return product


@transaction.atomic
def update_product(*, actor, product: Product, **changes) -> Product:
    before = {field: getattr(product, field) for field in changes}
    for field, value in changes.items():
        setattr(product, field, value)
    product.save(update_fields=[*changes.keys(), "updated_at"])
    diff = {f: {"from": before[f], "to": changes[f]} for f in changes if before[f] != changes[f]}
    if diff:
        audit.record(actor=actor, action="catalog.product_update", object_type="product",
                      object_id=str(product.id), changes=diff)
    return product


@transaction.atomic
def archive_product(*, actor, product: Product) -> Product:
    """Archive never deletes — order lines reference variants (see architecture-spec.md §8.1)."""
    product.status = "archived"
    product.archived_at = timezone.now()
    product.save(update_fields=["status", "archived_at", "updated_at"])
    Variant.objects.filter(product=product).update(is_active=False)
    audit.record(actor=actor, action="catalog.product_archive", object_type="product", object_id=str(product.id))
    return product


@transaction.atomic
def generate_variant_matrix(*, actor, product: Product, sizes: list[str], colors: list[str],
                             base_price_amount: int, currency: str = "EUR") -> list[Variant]:
    """Creates the full size x colour grid in one call, auto-generating SKUs (see architecture-spec.md §8.1)."""
    prefix = product.slug.upper().replace("-", "")[:12]
    created = []
    for color in colors:
        for size in sizes:
            sku = f"{prefix}-{_slug_part(color)}-{_slug_part(size)}"
            variant, _ = Variant.objects.get_or_create(
                product=product, size=size, color=color,
                defaults={"sku": sku, "price_amount": base_price_amount, "currency": currency},
            )
            created.append(variant)
    audit.record(actor=actor, action="catalog.variant_matrix_generate", object_type="product",
                  object_id=str(product.id), changes={"variants_created": len(created)})
    return created


@transaction.atomic
def update_variant(*, actor, variant: Variant, **changes) -> Variant:
    before = {field: getattr(variant, field) for field in changes}
    for field, value in changes.items():
        setattr(variant, field, value)
    variant.save(update_fields=[*changes.keys(), "updated_at"])
    diff = {f: {"from": before[f], "to": changes[f]} for f in changes if before[f] != changes[f]}
    if diff:
        audit.record(actor=actor, action="catalog.variant_update", object_type="variant",
                      object_id=str(variant.id), changes=diff)
    return variant


def assign_barcodes(variant_ids: list[int]) -> list[Variant]:
    """EAN-13 with checksum (see architecture-spec.md §8.1)."""
    variants = list(Variant.objects.filter(id__in=variant_ids, barcode__isnull=True))
    for variant in variants:
        variant.barcode = _generate_ean13(variant.id)
    Variant.objects.bulk_update(variants, ["barcode"])
    return variants


def _unique_slug(name: str) -> str:
    base = slugify(name)
    slug = base
    n = 1
    while Product.objects.filter(slug=slug).exists():
        n += 1
        slug = f"{base}-{n}"
    return slug


def _slug_part(value: str) -> str:
    return slugify(value).upper().replace("-", "")[:6] or "X"


def _generate_ean13(seed: int) -> str:
    body = str(seed).rjust(12, "0")[-12:]
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(body))
    check = (10 - total % 10) % 10
    return body + str(check)
