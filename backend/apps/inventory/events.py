"""Domain signals emitted by this app (see architecture-spec.md §8.2). `catalog` listens for availability flips."""
import django.dispatch

stock_depleted = django.dispatch.Signal()  # kwargs: variant_id, location_id
stock_replenished = django.dispatch.Signal()  # kwargs: variant_id, location_id
low_stock_reached = django.dispatch.Signal()  # kwargs: variant_id, location_id, available, threshold
