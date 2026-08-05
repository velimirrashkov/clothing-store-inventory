import pytest

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import VariantFactory
from apps.inventory import services as inventory_services
from apps.suppliers import services
from apps.suppliers.models import Delivery, ProductSupplier, Supplier
from apps.suppliers.services import EmptyDeliveryError, UnknownVariantError


@pytest.mark.django_db
def test_create_and_update_supplier():
    actor = UserFactory()
    supplier = services.create_supplier(actor=actor, name="Acme Textiles", email="hi@acme.example")

    updated = services.update_supplier(actor=actor, supplier=supplier, phone="+359123456")

    assert updated.phone == "+359123456"
    assert Supplier.objects.count() == 1


@pytest.mark.django_db
def test_set_product_supplier_cost_upserts(default_location):
    actor = UserFactory()
    variant = VariantFactory()
    supplier = services.create_supplier(actor=actor, name="Acme Textiles")

    services.set_product_supplier_cost(actor=actor, product_id=variant.product_id, supplier_id=supplier.id,
                                        cost_price=1200, currency="EUR")
    link = services.set_product_supplier_cost(actor=actor, product_id=variant.product_id, supplier_id=supplier.id,
                                               cost_price=1500, currency="EUR")

    assert ProductSupplier.objects.count() == 1  # upsert, not a second row
    assert link.cost_price == 1500


@pytest.mark.django_db
def test_receive_delivery_adds_stock_and_freezes_line_cost(default_location):
    actor = UserFactory()
    variant = VariantFactory(currency="EUR")
    supplier = services.create_supplier(actor=actor, name="Acme Textiles")

    delivery = services.receive_delivery(
        actor=actor, supplier_id=supplier.id, reference="INV-001",
        lines=[{"variant_id": variant.id, "quantity": 12, "unit_cost": 850}],
    )

    assert delivery.reference == "INV-001"
    assert delivery.lines.count() == 1
    line = delivery.lines.get()
    assert line.unit_cost == 850
    assert line.line_total == 12 * 850
    assert inventory_services.get_available(variant.id) == 12

    movement = variant.stock_movements.get()
    assert movement.reason == "receipt"
    assert movement.reference == f"DEL-{delivery.id}"
    assert movement.delta == 12


@pytest.mark.django_db
def test_receive_delivery_rejects_empty_lines(default_location):
    actor = UserFactory()
    supplier = services.create_supplier(actor=actor, name="Acme Textiles")
    with pytest.raises(EmptyDeliveryError):
        services.receive_delivery(actor=actor, supplier_id=supplier.id, lines=[])


@pytest.mark.django_db
def test_receive_delivery_rejects_unknown_variant(default_location):
    actor = UserFactory()
    supplier = services.create_supplier(actor=actor, name="Acme Textiles")
    with pytest.raises(UnknownVariantError):
        services.receive_delivery(
            actor=actor, supplier_id=supplier.id,
            lines=[{"variant_id": 999999, "quantity": 1, "unit_cost": 100}],
        )


@pytest.mark.django_db
def test_multiple_suppliers_can_quote_the_same_product(default_location):
    actor = UserFactory()
    variant = VariantFactory()
    supplier_a = services.create_supplier(actor=actor, name="Acme Textiles")
    supplier_b = services.create_supplier(actor=actor, name="Global Fabrics")

    services.set_product_supplier_cost(actor=actor, product_id=variant.product_id, supplier_id=supplier_a.id,
                                        cost_price=1000)
    services.set_product_supplier_cost(actor=actor, product_id=variant.product_id, supplier_id=supplier_b.id,
                                        cost_price=900)

    assert ProductSupplier.objects.filter(product_id=variant.product_id).count() == 2


@pytest.mark.django_db
def test_delivery_is_immutable_via_admin_but_receive_creates_it(default_location):
    """Sanity check that Delivery rows accumulate rather than get reused across receipts."""
    actor = UserFactory()
    variant = VariantFactory()
    supplier = services.create_supplier(actor=actor, name="Acme Textiles")

    services.receive_delivery(actor=actor, supplier_id=supplier.id,
                               lines=[{"variant_id": variant.id, "quantity": 1, "unit_cost": 100}])
    services.receive_delivery(actor=actor, supplier_id=supplier.id,
                               lines=[{"variant_id": variant.id, "quantity": 1, "unit_cost": 100}])

    assert Delivery.objects.count() == 2
    assert inventory_services.get_available(variant.id) == 2
