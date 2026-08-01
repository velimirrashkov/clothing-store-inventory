import pytest

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import VariantFactory
from apps.core.exceptions import InsufficientStock
from apps.inventory import services as inventory_services
from apps.inventory.models import Reservation
from apps.orders import services
from apps.orders.services import EmptyOrderError, InvalidOrderTransition, RefundExceedsOrderedQuantity

SHIPPING_ADDRESS = {"recipient_name": "Ada Lovelace", "line1": "1 Analytical Engine Way",
                    "city": "Sofia", "postcode": "1000", "country": "BG"}


def _stocked_variant(quantity=10, **kwargs):
    variant = VariantFactory(**kwargs)
    inventory_services.record_movement(variant_id=variant.id, delta=quantity, reason="receipt")
    return variant


@pytest.mark.django_db
def test_get_or_create_cart_is_stable_per_session(default_location):
    cart1 = services.get_or_create_cart(session_key="abc")
    cart2 = services.get_or_create_cart(session_key="abc")
    assert cart1.id == cart2.id


@pytest.mark.django_db
def test_add_line_then_add_again_merges_quantity(default_location):
    variant = _stocked_variant(quantity=10)
    cart = services.get_or_create_cart(session_key="s1")

    services.add_line(cart=cart, variant_id=variant.id, quantity=2)
    line = services.add_line(cart=cart, variant_id=variant.id, quantity=3)

    assert line.quantity == 5
    assert cart.lines.count() == 1


@pytest.mark.django_db
def test_add_line_rejects_over_available_stock(default_location):
    variant = _stocked_variant(quantity=2)
    cart = services.get_or_create_cart(session_key="s2")

    with pytest.raises(InsufficientStock):
        services.add_line(cart=cart, variant_id=variant.id, quantity=3)


@pytest.mark.django_db
def test_update_line_and_remove_line(default_location):
    variant = _stocked_variant(quantity=10)
    cart = services.get_or_create_cart(session_key="s3")
    line = services.add_line(cart=cart, variant_id=variant.id, quantity=1)

    updated = services.update_line(cart=cart, line_id=line.id, quantity=4)
    assert updated.quantity == 4

    services.remove_line(cart=cart, line_id=line.id)
    assert cart.lines.count() == 0


@pytest.mark.django_db
def test_start_checkout_reserves_all_lines_atomically(default_location):
    v1 = _stocked_variant(quantity=5)
    v2 = _stocked_variant(quantity=5)
    cart = services.get_or_create_cart(session_key="s4")
    services.add_line(cart=cart, variant_id=v1.id, quantity=2)
    services.add_line(cart=cart, variant_id=v2.id, quantity=1)

    reservations = services.start_checkout(cart)

    assert len(reservations) == 2
    assert inventory_services.get_available(v1.id) == 3
    assert inventory_services.get_available(v2.id) == 4


@pytest.mark.django_db
def test_start_checkout_twice_does_not_double_reserve(default_location):
    variant = _stocked_variant(quantity=5)
    cart = services.get_or_create_cart(session_key="s5")
    services.add_line(cart=cart, variant_id=variant.id, quantity=2)

    services.start_checkout(cart)
    services.start_checkout(cart)  # simulates a double-clicked "proceed to checkout"

    assert inventory_services.get_available(variant.id) == 3
    assert Reservation.objects.filter(cart=cart, status="active").count() == 1


@pytest.mark.django_db
def test_start_checkout_rejects_empty_cart(default_location):
    cart = services.get_or_create_cart(session_key="s6")
    with pytest.raises(EmptyOrderError):
        services.start_checkout(cart)


@pytest.mark.django_db
def test_confirm_order_creates_order_commits_stock_and_converts_cart(default_location):
    variant = _stocked_variant(quantity=5, price_amount=4000)
    buyer = UserFactory()
    cart = services.get_or_create_cart(user=buyer)
    services.add_line(cart=cart, variant_id=variant.id, quantity=2)
    services.start_checkout(cart)

    order = services.confirm_order(
        cart=cart, user=buyer, email="ada@example.com", shipping_address=SHIPPING_ADDRESS,
    )

    assert order.channel == "online"
    assert order.status == "paid"
    assert order.payment_status == "paid"
    assert order.subtotal_amount == 8000
    assert order.lines.count() == 1

    cart.refresh_from_db()
    assert cart.status == "converted"
    assert inventory_services.get_available(variant.id) == 3  # committed, not just reserved


@pytest.mark.django_db
def test_confirm_order_without_checkout_start_raises(default_location):
    variant = _stocked_variant()
    cart = services.get_or_create_cart(session_key="s7")
    services.add_line(cart=cart, variant_id=variant.id, quantity=1)

    with pytest.raises(EmptyOrderError):
        services.confirm_order(cart=cart, email="x@example.com", shipping_address=SHIPPING_ADDRESS)


@pytest.mark.django_db
def test_cancel_order_reverses_committed_stock(default_location):
    variant = _stocked_variant(quantity=5)
    cart = services.get_or_create_cart(session_key="s8")
    services.add_line(cart=cart, variant_id=variant.id, quantity=2)
    services.start_checkout(cart)
    order = services.confirm_order(cart=cart, email="x@example.com", shipping_address=SHIPPING_ADDRESS)
    actor = UserFactory()

    services.cancel_order(order=order, actor=actor, reason="buyer changed their mind")
    order.refresh_from_db()

    assert order.status == "cancelled"
    assert inventory_services.get_available(variant.id) == 5  # fully returned to the ledger


@pytest.mark.django_db
def test_fulfil_then_ship_transitions_status_and_records_shipment(default_location):
    variant = _stocked_variant()
    cart = services.get_or_create_cart(session_key="s9")
    services.add_line(cart=cart, variant_id=variant.id, quantity=1)
    services.start_checkout(cart)
    order = services.confirm_order(cart=cart, email="x@example.com", shipping_address=SHIPPING_ADDRESS)
    actor = UserFactory()

    order = services.fulfil_order(order=order, actor=actor)
    assert order.status == "processing"

    order = services.ship_order(order=order, actor=actor, carrier="Speedy", tracking_number="TRK123")
    assert order.status == "shipped"
    assert order.shipments.get().tracking_number == "TRK123"


@pytest.mark.django_db
def test_ship_before_fulfil_raises_invalid_transition(default_location):
    variant = _stocked_variant()
    cart = services.get_or_create_cart(session_key="s10")
    services.add_line(cart=cart, variant_id=variant.id, quantity=1)
    services.start_checkout(cart)
    order = services.confirm_order(cart=cart, email="x@example.com", shipping_address=SHIPPING_ADDRESS)

    with pytest.raises(InvalidOrderTransition):
        services.ship_order(order=order, actor=UserFactory(), carrier="Speedy")


@pytest.mark.django_db
def test_refund_order_full_restocks_and_marks_refunded(default_location):
    variant = _stocked_variant(quantity=5)
    cart = services.get_or_create_cart(session_key="s11")
    services.add_line(cart=cart, variant_id=variant.id, quantity=2)
    services.start_checkout(cart)
    order = services.confirm_order(cart=cart, email="x@example.com", shipping_address=SHIPPING_ADDRESS)
    line = order.lines.get()

    order = services.refund_order(
        order=order, actor=UserFactory(), restock=True,
        lines=[{"order_line_id": line.id, "quantity": 2}],
    )

    assert order.status == "refunded"
    assert order.payment_status == "refunded"
    assert inventory_services.get_available(variant.id) == 5


@pytest.mark.django_db
def test_refund_order_without_restock_leaves_stock_untouched(default_location):
    variant = _stocked_variant(quantity=5)
    cart = services.get_or_create_cart(session_key="s12")
    services.add_line(cart=cart, variant_id=variant.id, quantity=2)
    services.start_checkout(cart)
    order = services.confirm_order(cart=cart, email="x@example.com", shipping_address=SHIPPING_ADDRESS)
    line = order.lines.get()

    services.refund_order(
        order=order, actor=UserFactory(), restock=False,
        lines=[{"order_line_id": line.id, "quantity": 2}],
    )

    assert inventory_services.get_available(variant.id) == 3  # not restocked


@pytest.mark.django_db
def test_refund_order_rejects_quantity_exceeding_ordered(default_location):
    variant = _stocked_variant(quantity=5)
    cart = services.get_or_create_cart(session_key="s13")
    services.add_line(cart=cart, variant_id=variant.id, quantity=2)
    services.start_checkout(cart)
    order = services.confirm_order(cart=cart, email="x@example.com", shipping_address=SHIPPING_ADDRESS)
    line = order.lines.get()

    with pytest.raises(RefundExceedsOrderedQuantity):
        services.refund_order(
            order=order, actor=UserFactory(), restock=True,
            lines=[{"order_line_id": line.id, "quantity": 99}],
        )
