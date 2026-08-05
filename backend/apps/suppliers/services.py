"""ALL business logic for suppliers. Public function surface of the app (see architecture-spec.md §2.1)."""
from django.db import transaction

from apps.audit import services as audit
from apps.catalog.models import Product, Variant
from apps.core.exceptions import DomainError
from apps.inventory import services as inventory_services

from .models import Delivery, DeliveryLine, ProductSupplier, Supplier


class EmptyDeliveryError(DomainError):
    code = "empty_delivery"
    message = "A delivery must have at least one line."
    status_code = 400


class UnknownVariantError(DomainError):
    code = "unknown_variant"
    message = "One or more variants do not exist."
    status_code = 400


class UnknownSupplierError(DomainError):
    code = "unknown_supplier"
    message = "That supplier does not exist."
    status_code = 400


class UnknownProductError(DomainError):
    code = "unknown_product"
    message = "That product does not exist."
    status_code = 400


def create_supplier(*, actor, name: str, **fields) -> Supplier:
    supplier = Supplier.objects.create(name=name, **fields)
    audit.record(actor=actor, action="suppliers.supplier_create", object_type="supplier",
                 object_id=str(supplier.id))
    return supplier


def update_supplier(*, actor, supplier: Supplier, **changes) -> Supplier:
    before = {field: getattr(supplier, field) for field in changes}
    for field, value in changes.items():
        setattr(supplier, field, value)
    supplier.save(update_fields=[*changes.keys(), "updated_at"])
    diff = {f: {"from": before[f], "to": changes[f]} for f in changes if before[f] != changes[f]}
    if diff:
        audit.record(actor=actor, action="suppliers.supplier_update", object_type="supplier",
                      object_id=str(supplier.id), changes=diff)
    return supplier


def set_product_supplier_cost(*, actor, product_id: int, supplier_id: int, cost_price: int,
                               currency: str = "EUR") -> ProductSupplier:
    """Upserts one row of the vendor catalog — a product can be sourced from several suppliers
    at different quoted costs (see the models module docstring)."""
    if not Product.objects.filter(id=product_id).exists():
        raise UnknownProductError(product_id=product_id)
    if not Supplier.objects.filter(id=supplier_id).exists():
        raise UnknownSupplierError(supplier_id=supplier_id)

    link, created = ProductSupplier.objects.update_or_create(
        product_id=product_id, supplier_id=supplier_id,
        defaults={"cost_price": cost_price, "currency": currency},
    )
    audit.record(
        actor=actor, action="suppliers.cost_set", object_type="product_supplier", object_id=str(link.id),
        changes={"cost_price": cost_price, "currency": currency, "created": created},
    )
    return link


@transaction.atomic
def receive_delivery(*, actor, supplier_id: int, lines: list[dict], reference: str = "", note: str = "",
                      location_id: int | None = None) -> Delivery:
    """
    Records a delivery and adds the stock immediately — no draft/ordered/partial-received
    stages (deliberately simpler than a formal Purchase Order; see the models module
    docstring). `lines` is [{"variant_id": int, "quantity": int, "unit_cost": int}, ...].
    """
    if not lines:
        raise EmptyDeliveryError()
    if not Supplier.objects.filter(id=supplier_id).exists():
        raise UnknownSupplierError(supplier_id=supplier_id)

    variant_ids = sorted({line["variant_id"] for line in lines})  # sorted to avoid lock-order deadlocks
    variants = {v.id: v for v in Variant.objects.filter(id__in=variant_ids)}
    if len(variants) != len(variant_ids):
        raise UnknownVariantError(missing=[vid for vid in variant_ids if vid not in variants])

    location_id = location_id or inventory_services.default_location_id()
    currency = next(iter(variants.values())).currency

    delivery = Delivery.objects.create(
        supplier_id=supplier_id, location_id=location_id, reference=reference, note=note,
        currency=currency, received_by=actor,
    )

    DeliveryLine.objects.bulk_create([
        DeliveryLine(delivery=delivery, variant_id=line["variant_id"], quantity=line["quantity"],
                     unit_cost=line["unit_cost"])
        for line in lines
    ])

    for line in lines:
        inventory_services.record_movement(
            variant_id=line["variant_id"], delta=line["quantity"], reason="receipt",
            reference=f"DEL-{delivery.id}", actor=actor, location_id=location_id,
        )

    total_cost = sum(line["quantity"] * line["unit_cost"] for line in lines)
    audit.record(actor=actor, action="suppliers.delivery_received", object_type="delivery",
                 object_id=str(delivery.id), changes={"supplier_id": supplier_id, "total_cost": total_cost})
    return delivery
