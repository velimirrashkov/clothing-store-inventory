"""
ALL business logic for inventory. Public function surface of the app (see architecture-spec.md §2.1).

Rule that keeps this trustworthy (§5.2): there is exactly one way stock changes — record_movement().
No view, no task, no admin action ever does `stock_level.on_hand = X` directly.
"""
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.audit import services as audit
from apps.core.exceptions import InsufficientStock, ReservedStockConflict

from . import selectors
from .events import stock_depleted, stock_replenished
from .models import Reservation, StockCount, StockCountLine, StockLevel, StockMovement

get_available = selectors.get_available
bulk_availability = selectors.bulk_availability
low_stock_variants = selectors.low_stock_variants
default_location_id = selectors.default_location_id


@transaction.atomic
def record_movement(*, variant_id, delta: int, reason: str, actor=None, reference: str | None = None,
                     note: str | None = None, location_id: int | None = None) -> StockMovement:
    """select_for_update() is not optional — it is the lock that stops two concurrent checkouts from both
    selling the last item (see architecture-spec.md §5.2)."""
    location_id = location_id or selectors.default_location_id()

    level, _ = StockLevel.objects.select_for_update().get_or_create(
        variant_id=variant_id, location_id=location_id
    )

    previous_on_hand = level.on_hand
    new_on_hand = previous_on_hand + delta
    if new_on_hand < 0:
        raise InsufficientStock(variant_id=variant_id, requested=abs(delta), available=level.available)
    if new_on_hand < level.reserved:
        raise ReservedStockConflict(variant_id=variant_id, reserved=level.reserved, new_on_hand=new_on_hand)

    movement = StockMovement.objects.create(
        variant_id=variant_id, location_id=location_id, delta=delta,
        reason=reason, reference=reference, note=note, actor=actor,
    )

    level.on_hand = new_on_hand
    level.save(update_fields=["on_hand", "updated_at"])

    audit.record(actor=actor, action=f"stock.{reason}", object_type="variant", object_id=str(variant_id),
                 changes={"on_hand": {"from": previous_on_hand, "to": new_on_hand}})

    if new_on_hand - level.reserved <= 0:
        stock_depleted.send(sender=None, variant_id=variant_id, location_id=location_id)
    elif previous_on_hand - level.reserved <= 0 < new_on_hand - level.reserved:
        stock_replenished.send(sender=None, variant_id=variant_id, location_id=location_id)

    return movement


def receive_stock(*, lines: list[dict], reference: str, actor=None) -> list[StockMovement]:
    """Bulk delivery intake (see architecture-spec.md §8.2). Each line: {variant_id, quantity}."""
    return [
        record_movement(variant_id=line["variant_id"], delta=line["quantity"], reason="receipt",
                         reference=reference, actor=actor)
        for line in lines
    ]


@transaction.atomic
def reserve(*, variant_id, quantity: int, cart_id=None, order_id=None, location_id=None,
            ttl=None) -> Reservation:
    """Reserve at checkout start, not at add-to-cart (see architecture-spec.md §5.3)."""
    location_id = location_id or selectors.default_location_id()
    ttl = ttl or settings.RESERVATION_TTL

    level, _ = StockLevel.objects.select_for_update().get_or_create(
        variant_id=variant_id, location_id=location_id
    )
    if level.available < quantity:
        raise InsufficientStock(variant_id=variant_id, requested=quantity, available=level.available)

    level.reserved = level.reserved + quantity
    level.save(update_fields=["reserved", "updated_at"])

    return Reservation.objects.create(
        variant_id=variant_id, location_id=location_id, quantity=quantity,
        cart_id=cart_id, order_id=order_id, status="active",
        expires_at=timezone.now() + ttl,
    )


@transaction.atomic
def release(reservation_id: int) -> Reservation:
    reservation = Reservation.objects.select_for_update().get(id=reservation_id, status="active")
    level = StockLevel.objects.select_for_update().get(
        variant_id=reservation.variant_id, location_id=reservation.location_id
    )
    level.reserved = max(0, level.reserved - reservation.quantity)
    level.save(update_fields=["reserved", "updated_at"])

    reservation.status = "released"
    reservation.save(update_fields=["status", "updated_at"])
    return reservation


@transaction.atomic
def commit_reservation(reservation_id: int, order_ref: str, actor=None) -> Reservation:
    """Converts reservation -> movement in a single transaction (see architecture-spec.md §5.3)."""
    reservation = Reservation.objects.select_for_update().get(id=reservation_id, status="active")

    record_movement(
        variant_id=reservation.variant_id, delta=-reservation.quantity, reason="sale_online",
        reference=order_ref, actor=actor, location_id=reservation.location_id,
    )

    level = StockLevel.objects.select_for_update().get(
        variant_id=reservation.variant_id, location_id=reservation.location_id
    )
    level.reserved = max(0, level.reserved - reservation.quantity)
    level.save(update_fields=["reserved", "updated_at"])

    reservation.status = "committed"
    reservation.save(update_fields=["status", "updated_at"])
    return reservation


def expire_stale_reservations() -> int:
    """Celery Beat, every 2 min. Must be idempotent and lock rows — races with real checkouts (§5.3, §8.6)."""
    expired_ids = list(
        Reservation.objects.filter(status="active", expires_at__lt=timezone.now())
        .values_list("id", flat=True)
    )
    count = 0
    for reservation_id in expired_ids:
        with transaction.atomic():
            try:
                reservation = Reservation.objects.select_for_update().get(id=reservation_id, status="active")
            except Reservation.DoesNotExist:
                continue  # already handled by a real checkout — that's the race this guards against
            level = StockLevel.objects.select_for_update().get(
                variant_id=reservation.variant_id, location_id=reservation.location_id
            )
            level.reserved = max(0, level.reserved - reservation.quantity)
            level.save(update_fields=["reserved", "updated_at"])
            reservation.status = "expired"
            reservation.save(update_fields=["status", "updated_at"])
            count += 1
    return count


@transaction.atomic
def open_count(*, location_id: int, actor) -> StockCount:
    """Open a count -> snapshot expected for every active variant (see architecture-spec.md §5.6)."""
    from apps.catalog.models import Variant

    count = StockCount.objects.create(location_id=location_id, started_by=actor)
    levels = {
        level.variant_id: level.on_hand
        for level in StockLevel.objects.filter(location_id=location_id)
    }
    lines = [
        StockCountLine(count=count, variant_id=variant_id, expected=levels.get(variant_id, 0))
        for variant_id in Variant.objects.filter(is_active=True).values_list("id", flat=True)
    ]
    StockCountLine.objects.bulk_create(lines)
    return count


def submit_count_line(*, count_id: int, variant_id: int, counted: int, actor) -> StockCountLine:
    line = StockCountLine.objects.get(count_id=count_id, variant_id=variant_id)
    line.counted = counted
    line.counted_by = actor
    line.counted_at = timezone.now()
    line.save(update_fields=["counted", "counted_by", "counted_at"])
    return line


@transaction.atomic
def close_count(*, count_id: int, actor) -> StockCount:
    """Generates one count_adjustment movement per discrepancy. Never overwrite levels directly (§5.6)."""
    count = StockCount.objects.select_for_update().get(id=count_id, status="open")
    for line in count.lines.exclude(counted__isnull=True).select_related("variant"):
        discrepancy = line.counted - line.expected
        if discrepancy != 0:
            record_movement(
                variant_id=line.variant_id, delta=discrepancy, reason="count_adjustment",
                reference=str(count.id), actor=actor, location_id=count.location_id,
            )
    count.status = "closed"
    count.closed_at = timezone.now()
    count.save(update_fields=["status", "closed_at"])
    return count


def reconcile_levels() -> list[dict]:
    """Nightly, ledger vs cache (see architecture-spec.md §5.1, §8.6). Returns any mismatches found."""
    from django.db.models import Sum

    ledger_totals = {
        (row["variant_id"], row["location_id"]): row["total"]
        for row in StockMovement.objects.values("variant_id", "location_id").annotate(total=Sum("delta"))
    }

    mismatches = []
    for level in StockLevel.objects.all():
        ledger_total = ledger_totals.get((level.variant_id, level.location_id), 0)
        if ledger_total != level.on_hand:
            mismatches.append({
                "variant_id": level.variant_id, "location_id": level.location_id,
                "cache_on_hand": level.on_hand, "ledger_total": ledger_total,
            })
            level.on_hand = ledger_total
            level.save(update_fields=["on_hand", "updated_at"])
    return mismatches
