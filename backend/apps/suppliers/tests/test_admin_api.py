import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import VariantFactory


@pytest.fixture
def manager(db):
    call_command("seed_roles")
    user = UserFactory()
    user.groups.add(Group.objects.get(name="manager"))
    return user


@pytest.fixture
def worker(db):
    call_command("seed_roles")
    user = UserFactory()
    user.groups.add(Group.objects.get(name="worker"))
    return user


@pytest.mark.django_db
def test_full_supplier_and_delivery_flow(client, manager, default_location):
    client.force_login(manager)

    supplier_resp = client.post("/api/v1/admin/suppliers", {"name": "Acme Textiles"},
                                 content_type="application/json")
    assert supplier_resp.status_code == 201
    supplier_id = supplier_resp.json()["id"]

    variant = VariantFactory()
    cost_resp = client.post(
        f"/api/v1/admin/products/{variant.product_id}/suppliers",
        {"supplier_id": supplier_id, "cost_price": 1200, "currency": "EUR"},
        content_type="application/json",
    )
    assert cost_resp.status_code == 201
    assert cost_resp.json()["cost_price"] == 1200

    catalog_resp = client.get(f"/api/v1/admin/products/{variant.product_id}/suppliers")
    assert catalog_resp.status_code == 200
    assert len(catalog_resp.json()) == 1

    delivery_resp = client.post(
        "/api/v1/admin/deliveries",
        {"supplier_id": supplier_id, "reference": "INV-42",
         "lines": [{"variant_id": variant.id, "quantity": 5, "unit_cost": 1150}]},
        content_type="application/json",
    )
    assert delivery_resp.status_code == 201
    delivery_id = delivery_resp.json()["id"]
    assert delivery_resp.json()["lines"][0]["line_total"] == 5750

    list_resp = client.get("/api/v1/admin/deliveries")
    assert list_resp.status_code == 200
    assert any(d["id"] == delivery_id for d in list_resp.json()["results"])

    detail_resp = client.get(f"/api/v1/admin/deliveries/{delivery_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["supplier_name"] == "Acme Textiles"

    from apps.inventory import services as inventory_services
    assert inventory_services.get_available(variant.id) == 5


@pytest.mark.django_db
def test_worker_can_receive_delivery_but_not_manage_suppliers(client, worker, default_location):
    client.force_login(worker)

    create_resp = client.post("/api/v1/admin/suppliers", {"name": "Blocked Co"}, content_type="application/json")
    assert create_resp.status_code == 403

    list_resp = client.get("/api/v1/admin/suppliers")
    assert list_resp.status_code == 200

    variant = VariantFactory()
    delivery_resp = client.post(
        "/api/v1/admin/deliveries",
        {"supplier_id": 1, "lines": [{"variant_id": variant.id, "quantity": 1, "unit_cost": 100}]},
        content_type="application/json",
    )
    # supplier_id=1 won't exist yet in this test's isolated DB — expect a clean 400, not a 500
    assert delivery_resp.status_code in (400, 404)


@pytest.mark.django_db
def test_worker_cannot_view_vendor_cost_catalog(client, worker, manager, default_location):
    client.force_login(manager)
    supplier = client.post("/api/v1/admin/suppliers", {"name": "Acme"}, content_type="application/json").json()
    variant = VariantFactory()
    client.post(f"/api/v1/admin/products/{variant.product_id}/suppliers",
                {"supplier_id": supplier["id"], "cost_price": 999}, content_type="application/json")

    client.force_login(worker)
    resp = client.get(f"/api/v1/admin/products/{variant.product_id}/suppliers")
    assert resp.status_code == 403
