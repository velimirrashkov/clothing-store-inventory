"""Inventory invariants — highest priority (see architecture-spec.md §10.1)."""
import threading

import pytest
from django.db import connection

from apps.catalog.tests.factories import VariantFactory
from apps.core.exceptions import InsufficientStock
from apps.inventory import services
from apps.inventory.models import StockLevel


@pytest.mark.django_db(transaction=True)
def test_concurrent_reservations_cannot_oversell(default_location):
    variant = VariantFactory()
    services.record_movement(variant_id=variant.id, delta=1, reason="initial_load")

    results = []
    lock = threading.Lock()

    def try_reserve():
        try:
            services.reserve(variant_id=variant.id, quantity=1, cart_id=None)
            outcome = True
        except InsufficientStock:
            outcome = False
        finally:
            connection.close()  # each thread needs its own DB connection
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=try_reserve) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(results) == 1
    assert services.get_available(variant.id) == 0


@pytest.mark.django_db
def test_record_movement_rejects_negative_on_hand(default_location):
    variant = VariantFactory()
    with pytest.raises(InsufficientStock):
        services.record_movement(variant_id=variant.id, delta=-1, reason="sale_pos")


@pytest.mark.django_db
def test_ledger_matches_cache_after_movements(default_location):
    variant = VariantFactory()
    services.record_movement(variant_id=variant.id, delta=10, reason="receipt")
    services.record_movement(variant_id=variant.id, delta=-3, reason="sale_pos")
    services.record_movement(variant_id=variant.id, delta=-2, reason="damage")

    level = StockLevel.objects.get(variant=variant, location=default_location)
    assert level.on_hand == 5

    mismatches = services.reconcile_levels()
    assert mismatches == []


@pytest.mark.django_db
def test_reserve_then_commit_creates_sale_movement_and_clears_reservation(default_location):
    variant = VariantFactory()
    services.record_movement(variant_id=variant.id, delta=5, reason="receipt")

    reservation = services.reserve(variant_id=variant.id, quantity=2, cart_id=None)
    assert services.get_available(variant.id) == 3

    services.commit_reservation(reservation.id, order_ref="ORD-TEST-1")
    reservation.refresh_from_db()

    level = StockLevel.objects.get(variant=variant, location=default_location)
    assert reservation.status == "committed"
    assert level.on_hand == 3
    assert level.reserved == 0


@pytest.mark.django_db
def test_release_returns_reserved_stock(default_location):
    variant = VariantFactory()
    services.record_movement(variant_id=variant.id, delta=5, reason="receipt")

    reservation = services.reserve(variant_id=variant.id, quantity=2, cart_id=None)
    services.release(reservation.id)

    assert services.get_available(variant.id) == 5


@pytest.mark.django_db
def test_expire_stale_reservations_is_idempotent(default_location):
    from django.utils import timezone

    variant = VariantFactory()
    services.record_movement(variant_id=variant.id, delta=5, reason="receipt")
    reservation = services.reserve(variant_id=variant.id, quantity=2, cart_id=None)
    reservation.expires_at = timezone.now() - timezone.timedelta(minutes=1)
    reservation.save(update_fields=["expires_at"])

    first_pass = services.expire_stale_reservations()
    second_pass = services.expire_stale_reservations()

    assert first_pass == 1
    assert second_pass == 0
    assert services.get_available(variant.id) == 5
