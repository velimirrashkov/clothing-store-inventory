"""Read queries. Nothing here writes (see architecture-spec.md §2.1)."""
from django.db.models import F

from .models import Location, Reservation, StockLevel


def default_location_id() -> int:
    location = Location.objects.filter(is_default=True).first()
    if location is None:
        raise Location.DoesNotExist("No default location seeded — run the seed_default_location command.")
    return location.id


def get_available(variant_id: int, location_id: int | None = None) -> int:
    """Available to sell = on_hand - reserved (see architecture-spec.md §4.4)."""
    location_id = location_id or default_location_id()
    level = StockLevel.objects.filter(variant_id=variant_id, location_id=location_id).first()
    return level.available if level else 0


def bulk_availability(variant_ids: list[int], location_id: int | None = None) -> dict[int, int]:
    """Avoids N+1 (see architecture-spec.md §8.2)."""
    location_id = location_id or default_location_id()
    rows = (
        StockLevel.objects.filter(variant_id__in=variant_ids, location_id=location_id)
        .annotate(_available=F("on_hand") - F("reserved"))
        .values_list("variant_id", "_available")
    )
    availability = dict(rows)
    return {variant_id: availability.get(variant_id, 0) for variant_id in variant_ids}


def low_stock_variants(threshold: int, location_id: int | None = None):
    location_id = location_id or default_location_id()
    return (
        StockLevel.objects.filter(location_id=location_id)
        .annotate(_available=F("on_hand") - F("reserved"))
        .filter(_available__lte=threshold)
        .select_related("variant")
    )


def active_reservations_for_cart(cart_id: int):
    """
    Lets `orders` read reservation state without importing inventory's models directly
    (see architecture-spec.md §2.2 — apps talk to each other only through services/selectors).
    """
    return (
        Reservation.objects.filter(cart_id=cart_id, status="active")
        .select_related("variant", "variant__product")
    )
