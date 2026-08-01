import pytest

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import VariantFactory
from apps.core.exceptions import InsufficientStock
from apps.inventory import services as inventory_services
from apps.orders import services
from apps.orders.models import Order, OrderLine
from apps.orders.services import EmptyOrderError, UnknownVariantError


@pytest.mark.django_db
def test_create_pos_order_decrements_stock_and_freezes_line_data(default_location):
    variant = VariantFactory(price_amount=6000, currency="EUR", size="M", color="black")
    inventory_services.record_movement(variant_id=variant.id, delta=5, reason="receipt")
    actor = UserFactory()

    order = services.create_pos_order(
        lines=[{"variant_id": variant.id, "quantity": 2}], payment_method="cash", actor=actor,
    )

    assert order.channel == "pos"
    assert order.status == "delivered"
    assert order.payment_status == "paid"
    assert order.payment_method == "cash"
    assert order.subtotal_amount == 12000
    assert order.total_amount == 12000
    assert order.reference.startswith("ORD-")

    line = OrderLine.objects.get(order=order)
    assert line.sku == variant.sku
    assert line.size == "M"
    assert line.color == "black"
    assert line.quantity == 2
    assert line.line_total == 12000

    assert inventory_services.get_available(variant.id) == 3


@pytest.mark.django_db
def test_create_pos_order_computes_vat_inclusive_tax(default_location, settings):
    settings.VAT_RATE = 0.20
    variant = VariantFactory(price_amount=1200)
    inventory_services.record_movement(variant_id=variant.id, delta=1, reason="receipt")

    order = services.create_pos_order(
        lines=[{"variant_id": variant.id, "quantity": 1}], payment_method="card", actor=UserFactory(),
    )

    assert order.tax_amount == 200  # 1200 * 0.20 / 1.20 = 200
    assert order.total_amount == 1200  # VAT-inclusive — tax is informational, not additive


@pytest.mark.django_db
def test_create_pos_order_raises_on_insufficient_stock(default_location):
    variant = VariantFactory()
    inventory_services.record_movement(variant_id=variant.id, delta=1, reason="receipt")

    with pytest.raises(InsufficientStock):
        services.create_pos_order(
            lines=[{"variant_id": variant.id, "quantity": 2}], payment_method="cash", actor=UserFactory(),
        )
    # the whole function is @transaction.atomic — a failed stock movement rolls back the Order too
    assert Order.objects.count() == 0


@pytest.mark.django_db
def test_create_pos_order_rejects_empty_lines(default_location):
    with pytest.raises(EmptyOrderError):
        services.create_pos_order(lines=[], payment_method="cash", actor=UserFactory())


@pytest.mark.django_db
def test_create_pos_order_rejects_unknown_variant(default_location):
    with pytest.raises(UnknownVariantError):
        services.create_pos_order(
            lines=[{"variant_id": 999999, "quantity": 1}], payment_method="cash", actor=UserFactory(),
        )


@pytest.mark.django_db
def test_pos_order_references_increment_sequentially_within_a_year(default_location):
    variant = VariantFactory()
    inventory_services.record_movement(variant_id=variant.id, delta=10, reason="receipt")
    actor = UserFactory()

    first = services.create_pos_order(lines=[{"variant_id": variant.id, "quantity": 1}],
                                       payment_method="cash", actor=actor)
    second = services.create_pos_order(lines=[{"variant_id": variant.id, "quantity": 1}],
                                        payment_method="cash", actor=actor)

    first_seq = int(first.reference.rsplit("-", 1)[1])
    second_seq = int(second.reference.rsplit("-", 1)[1])
    assert second_seq == first_seq + 1
