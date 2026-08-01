"""ALL business logic for orders. Public function surface of the app (see architecture-spec.md §2.1)."""
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalog.models import Variant
from apps.core.exceptions import DomainError
from apps.inventory import services as inventory_services
from apps.pricing import services as pricing_services

from .models import Order, OrderLine

_MAX_REFERENCE_ATTEMPTS = 5


class EmptyOrderError(DomainError):
    code = "empty_order"
    message = "An order must have at least one line."
    status_code = 400


class UnknownVariantError(DomainError):
    code = "unknown_variant"
    message = "One or more variants do not exist."
    status_code = 400


def _next_order_reference(year: int) -> str:
    """e.g. ORD-2026-00417 (see architecture-spec.md §4.7). Must be called inside the same atomic
    block that creates the Order — select_for_update() locks the year's rows against concurrent
    tills; create_pos_order additionally retries on IntegrityError to cover the first-order-of-the-year
    race, where there is nothing yet to lock."""
    prefix = f"ORD-{year}-"
    last = Order.objects.select_for_update().filter(reference__startswith=prefix).order_by("-reference").first()
    next_seq = int(last.reference.removeprefix(prefix)) + 1 if last else 1
    return f"{prefix}{next_seq:05d}"


@transaction.atomic
def create_pos_order(*, lines: list[dict], payment_method: str, actor) -> Order:
    """
    In-store, immediate sale movement (see architecture-spec.md §5.4, §8.3). `lines` is
    [{"variant_id": int, "quantity": int}, ...].

    Unlike online checkout there is no reservation step — the customer is holding the item, so
    stock leaves the ledger immediately via the same record_movement() the online path uses
    (reason="sale_pos"), which is what keeps the shared pool correct with zero reconciliation
    logic between channels (§5.4). Status jumps straight to paid/delivered: a till sale has no
    separate fulfilment or shipping step.
    """
    if not lines:
        raise EmptyOrderError()

    variant_ids = sorted({line["variant_id"] for line in lines})  # sorted to avoid lock-order deadlocks, §8.3
    variants = {v.id: v for v in Variant.objects.select_related("product").filter(id__in=variant_ids)}
    if len(variants) != len(variant_ids):
        raise UnknownVariantError(missing=[vid for vid in variant_ids if vid not in variants])

    subtotal = 0
    line_specs = []
    for line in lines:
        variant = variants[line["variant_id"]]
        quantity = line["quantity"]
        line_total = variant.price_amount * quantity
        subtotal += line_total
        line_specs.append((variant, quantity, line_total))

    currency = next(iter(variants.values())).currency
    tax_amount = pricing_services.extract_vat(subtotal)  # informational only — prices are VAT-inclusive

    order = None
    for attempt in range(_MAX_REFERENCE_ATTEMPTS):
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    reference=_next_order_reference(timezone.now().year),
                    channel="pos",
                    status="delivered",
                    payment_status="paid",
                    payment_method=payment_method,
                    subtotal_amount=subtotal,
                    tax_amount=tax_amount,
                    total_amount=subtotal,
                    currency=currency,
                )
            break
        except IntegrityError:
            if attempt == _MAX_REFERENCE_ATTEMPTS - 1:
                raise

    OrderLine.objects.bulk_create([
        OrderLine(
            order=order, variant=variant, sku=variant.sku, product_name=variant.product.name,
            size=variant.size, color=variant.color, quantity=quantity,
            unit_amount=variant.price_amount, line_total=line_total,
        )
        for variant, quantity, line_total in line_specs
    ])

    for variant, quantity, _ in line_specs:
        inventory_services.record_movement(
            variant_id=variant.id, delta=-quantity, reason="sale_pos",
            reference=order.reference, actor=actor,
        )

    return order
