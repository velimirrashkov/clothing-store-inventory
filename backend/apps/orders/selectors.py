"""Read queries. Nothing here writes (see architecture-spec.md §2.1)."""
from django.db.models import QuerySet

from .models import Order


def get_order_for_user(*, public_id, user) -> Order:
    """
    Layer 2 object ownership check (see architecture-spec.md §6.2) — a buyer requesting an order
    is checked against ownership, not merely against "is a buyer". Raises Order.DoesNotExist for
    both "doesn't exist" and "exists but isn't yours" — callers must turn that into 404, never 403,
    so a 403 response never confirms the object exists.
    """
    qs = Order.objects.prefetch_related("lines")
    if not user.has_perm("orders.view_any_order"):
        qs = qs.filter(user=user)
    return qs.get(public_id=public_id)


def orders_for_user(user) -> QuerySet[Order]:
    return Order.objects.filter(user=user).prefetch_related("lines").order_by("-placed_at")


def search_orders(*, status: str | None = None, channel: str | None = None,
                   date_from=None, date_to=None) -> QuerySet[Order]:
    """GET /api/v1/admin/orders?status=&channel=&from=&to= (see architecture-spec.md §7.2)."""
    qs = Order.objects.prefetch_related("lines").order_by("-placed_at")
    if status:
        qs = qs.filter(status=status)
    if channel:
        qs = qs.filter(channel=channel)
    if date_from:
        qs = qs.filter(placed_at__gte=date_from)
    if date_to:
        qs = qs.filter(placed_at__lte=date_to)
    return qs
