"""ALL business logic for orders. Public function surface of the app (see architecture-spec.md §2.1)."""
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit import services as audit
from apps.catalog.models import Variant
from apps.core.exceptions import DomainError, InsufficientStock
from apps.inventory import selectors as inventory_selectors
from apps.inventory import services as inventory_services
from apps.pricing import services as pricing_services

from .models import Cart, CartLine, Order, OrderLine, Return, ReturnLine, Shipment

_MAX_REFERENCE_ATTEMPTS = 5

# Order status machine (see the Order model's docstring and architecture-spec.md §8.3). Enforced
# here, and only here — never allow a view or admin action to write order.status directly.
_ALLOWED_TRANSITIONS = {
    "pending_payment": {"paid", "cancelled"},
    "paid": {"processing", "cancelled", "refunded"},
    "processing": {"shipped", "cancelled", "refunded"},
    "shipped": {"delivered", "refunded"},
    "delivered": {"refunded"},
}


class EmptyOrderError(DomainError):
    code = "empty_order"
    message = "An order must have at least one line."
    status_code = 400


class UnknownVariantError(DomainError):
    code = "unknown_variant"
    message = "One or more variants do not exist."
    status_code = 400


class InvalidOrderTransition(DomainError):
    code = "invalid_order_transition"
    message = "That order status transition isn't allowed."
    status_code = 409


class RefundExceedsOrderedQuantity(DomainError):
    code = "refund_exceeds_ordered_quantity"
    message = "Cannot refund more than was ordered."
    status_code = 400


def _next_order_reference(year: int) -> str:
    """e.g. ORD-2026-00417 (see architecture-spec.md §4.7). Must be called inside the same atomic
    block that creates the Order — select_for_update() locks the year's rows against concurrent
    tills/checkouts; _create_order additionally retries on IntegrityError to cover the
    first-order-of-the-year race, where there is nothing yet to lock."""
    prefix = f"ORD-{year}-"
    last = Order.objects.select_for_update().filter(reference__startswith=prefix).order_by("-reference").first()
    next_seq = int(last.reference.removeprefix(prefix)) + 1 if last else 1
    return f"{prefix}{next_seq:05d}"


def _create_order(**fields) -> Order:
    """Shared by create_pos_order and confirm_order — retries on reference collision (see
    _next_order_reference's docstring for why the first order of a year can race)."""
    for attempt in range(_MAX_REFERENCE_ATTEMPTS):
        try:
            with transaction.atomic():
                return Order.objects.create(reference=_next_order_reference(timezone.now().year), **fields)
        except IntegrityError:
            if attempt == _MAX_REFERENCE_ATTEMPTS - 1:
                raise


def _validate_transition(order: Order, to_status: str) -> None:
    allowed = _ALLOWED_TRANSITIONS.get(order.status, set())
    if to_status not in allowed:
        raise InvalidOrderTransition(order_id=order.id, from_status=order.status, to_status=to_status)


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

    order = _create_order(
        channel="pos", status="delivered", payment_status="paid", payment_method=payment_method,
        subtotal_amount=subtotal, tax_amount=tax_amount, total_amount=subtotal, currency=currency,
    )

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


def get_or_create_cart(*, user=None, session_key: str | None = None) -> Cart:
    if user is not None and user.is_authenticated:
        cart = Cart.objects.filter(user=user, status="active").first()
        return cart or Cart.objects.create(user=user, status="active")

    cart = Cart.objects.filter(session_key=session_key, status="active").first()
    return cart or Cart.objects.create(session_key=session_key, status="active")


def add_line(*, cart: Cart, variant_id: int, quantity: int) -> CartLine:
    """
    Validates availability, no reserve (see architecture-spec.md §8.3) — reserving happens at
    checkout start, not add-to-cart (§5.3), so an indecisive shopper doesn't block stock for
    hours. This check is advisory: the authoritative check is the select_for_update() inside
    inventory.services.reserve() at checkout time.
    """
    try:
        variant = Variant.objects.get(id=variant_id)
    except Variant.DoesNotExist:
        raise UnknownVariantError(variant_id=variant_id) from None

    existing = CartLine.objects.filter(cart=cart, variant_id=variant_id).first()
    total_requested = quantity + (existing.quantity if existing else 0)
    available = inventory_services.get_available(variant_id)
    if available < total_requested:
        raise InsufficientStock(variant_id=variant_id, requested=total_requested, available=available)

    if existing:
        existing.quantity = total_requested
        existing.unit_amount = variant.price_amount
        existing.save(update_fields=["quantity", "unit_amount"])
        return existing

    return CartLine.objects.create(
        cart=cart, variant_id=variant_id, quantity=quantity, unit_amount=variant.price_amount,
    )


def update_line(*, cart: Cart, line_id: int, quantity: int) -> CartLine:
    line = CartLine.objects.get(id=line_id, cart=cart)
    available = inventory_services.get_available(line.variant_id)
    if available < quantity:
        raise InsufficientStock(variant_id=line.variant_id, requested=quantity, available=available)
    line.quantity = quantity
    line.save(update_fields=["quantity"])
    return line


def remove_line(*, cart: Cart, line_id: int) -> None:
    CartLine.objects.filter(id=line_id, cart=cart).delete()


@transaction.atomic
def start_checkout(cart: Cart) -> list:
    """
    Reserves all lines atomically — all or none, sorted by variant id to avoid lock-order
    deadlocks between concurrent checkouts (see architecture-spec.md §8.3). Restarting checkout
    on the same cart (e.g. a double-clicked "proceed to checkout") first clears any reservations
    left over from a previous attempt rather than piling up duplicates — a lighter-weight
    substitute for full Idempotency-Key support, which §7.1 scopes to POST /checkout/confirm and
    isn't implemented yet.
    """
    lines = list(cart.lines.select_related("variant").order_by("variant_id"))
    if not lines:
        raise EmptyOrderError()

    for reservation in inventory_selectors.active_reservations_for_cart(cart.id):
        inventory_services.release(reservation.id)

    return [
        inventory_services.reserve(variant_id=line.variant_id, quantity=line.quantity, cart_id=cart.id)
        for line in lines
    ]


@transaction.atomic
def confirm_order(*, cart: Cart, email: str, shipping_address: dict, billing_address: dict | None = None,
                   payment_ref: str | None = None, user=None) -> Order:
    """
    Creates the order, commits reservations (see architecture-spec.md §8.3). `payment_ref` is a
    placeholder until real payment integration lands (§12) — accepted now so the signature won't
    need to change later, recorded on the audit entry, but not yet validated against anything.
    """
    reservations = list(inventory_selectors.active_reservations_for_cart(cart.id))
    if not reservations:
        raise EmptyOrderError()

    subtotal = sum(r.variant.price_amount * r.quantity for r in reservations)
    currency = reservations[0].variant.currency
    tax_amount = pricing_services.extract_vat(subtotal)

    order = _create_order(
        user=user, email=email, channel="online", status="paid", payment_status="paid",
        subtotal_amount=subtotal, tax_amount=tax_amount, total_amount=subtotal, currency=currency,
        shipping_address=shipping_address, billing_address=billing_address,
    )

    OrderLine.objects.bulk_create([
        OrderLine(
            order=order, variant=r.variant, sku=r.variant.sku, product_name=r.variant.product.name,
            size=r.variant.size, color=r.variant.color, quantity=r.quantity,
            unit_amount=r.variant.price_amount, line_total=r.variant.price_amount * r.quantity,
        )
        for r in reservations
    ])

    for r in reservations:
        inventory_services.commit_reservation(r.id, order_ref=order.reference, actor=user)

    cart.status = "converted"
    cart.save(update_fields=["status", "updated_at"])

    audit.record(actor=user, action="orders.confirm", object_type="order", object_id=str(order.id),
                 changes={"payment_ref": payment_ref})
    return order


@transaction.atomic
def cancel_order(*, order: Order, actor, reason: str = "") -> Order:
    """
    Every Order row that exists has already been paid and had its stock committed (see
    confirm_order/create_pos_order — Phase 1 has no real payment gateway, so "confirmed" already
    means "paid"). Cancelling therefore always means reversing the ledger via a return movement,
    never releasing a reservation — there isn't one left by the time an Order exists (§8.3).
    """
    _validate_transition(order, "cancelled")

    for line in order.lines.all():
        inventory_services.record_movement(
            variant_id=line.variant_id, delta=line.quantity, reason="return",
            reference=order.reference, actor=actor, note=reason,
        )

    order.status = "cancelled"
    order.save(update_fields=["status", "updated_at"])
    audit.record(actor=actor, action="orders.cancel", object_type="order", object_id=str(order.id),
                 changes={"reason": reason})
    return order


def fulfil_order(*, order: Order, actor) -> Order:
    _validate_transition(order, "processing")
    order.status = "processing"
    order.save(update_fields=["status", "updated_at"])
    audit.record(actor=actor, action="orders.fulfil", object_type="order", object_id=str(order.id))
    return order


@transaction.atomic
def ship_order(*, order: Order, actor, carrier: str, tracking_number: str | None = None) -> Order:
    _validate_transition(order, "shipped")
    order.status = "shipped"
    order.save(update_fields=["status", "updated_at"])
    Shipment.objects.create(
        order=order, carrier=carrier, tracking_number=tracking_number,
        status="shipped", shipped_at=timezone.now(),
    )
    audit.record(actor=actor, action="orders.ship", object_type="order", object_id=str(order.id),
                 changes={"carrier": carrier, "tracking_number": tracking_number})
    return order


@transaction.atomic
def refund_order(*, order: Order, lines: list[dict], restock: bool, actor) -> Order:
    """lines: [{"order_line_id": int, "quantity": int}, ...] — partial or full refund (§8.3, §4.7)."""
    _validate_transition(order, "refunded")

    return_request = Return.objects.create(order=order, status="approved")
    refund_total = 0
    for line_spec in lines:
        order_line = OrderLine.objects.get(id=line_spec["order_line_id"], order=order)
        quantity = line_spec["quantity"]
        if quantity > order_line.quantity:
            raise RefundExceedsOrderedQuantity(order_line_id=order_line.id, ordered=order_line.quantity,
                                                requested=quantity)
        refund_total += order_line.unit_amount * quantity
        ReturnLine.objects.create(
            return_request=return_request, order_line=order_line, quantity=quantity, restock=restock,
        )
        if restock:
            inventory_services.record_movement(
                variant_id=order_line.variant_id, delta=quantity, reason="return",
                reference=order.reference, actor=actor,
            )

    return_request.status = "refunded"
    return_request.resolved_at = timezone.now()
    return_request.save(update_fields=["status", "resolved_at"])

    order.status = "refunded"
    order.payment_status = "refunded"
    order.save(update_fields=["status", "payment_status", "updated_at"])

    audit.record(actor=actor, action="orders.refund", object_type="order", object_id=str(order.id),
                 changes={"refund_total": refund_total, "restock": restock})
    return order
