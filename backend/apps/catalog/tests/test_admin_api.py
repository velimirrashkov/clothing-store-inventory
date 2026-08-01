"""
Integration coverage for the back-office catalog API added to support the React app (see
architecture-spec.md §7.2 "Back-office": CRUD /products, CRUD /variants).
"""
import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import CategoryFactory


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
def test_full_admin_catalog_flow(client, manager, default_location):
    client.force_login(manager)

    category_resp = client.post("/api/v1/admin/categories", {"name": "Tees"}, content_type="application/json")
    assert category_resp.status_code == 201
    category_id = category_resp.json()["id"]
    assert category_resp.json()["slug"] == "tees"

    product_resp = client.post(
        "/api/v1/admin/products",
        {"name": "Classic Tee", "category": category_id, "gender": "unisex"},
        content_type="application/json",
    )
    assert product_resp.status_code == 201
    product_id = product_resp.json()["id"]
    assert product_resp.json()["variants"] == []

    matrix_resp = client.post(
        f"/api/v1/admin/products/{product_id}/variants/matrix",
        {"sizes": ["S", "M"], "colors": ["black"], "base_price_amount": 2999},
        content_type="application/json",
    )
    assert matrix_resp.status_code == 201
    variants = matrix_resp.json()
    assert len(variants) == 2
    assert all(v["available"] == 0 for v in variants)  # brand new — nothing received yet

    variant_id = variants[0]["id"]
    update_resp = client.patch(
        f"/api/v1/admin/variants/{variant_id}", {"price_amount": 3499}, content_type="application/json",
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["price_amount"] == 3499

    barcode_resp = client.post(
        "/api/v1/admin/variants/assign-barcodes",
        {"variant_ids": [v["id"] for v in variants]},
        content_type="application/json",
    )
    assert barcode_resp.status_code == 200
    assert all(v["barcode"] for v in barcode_resp.json())

    detail_resp = client.get(f"/api/v1/admin/products/{product_id}")
    assert detail_resp.status_code == 200
    assert len(detail_resp.json()["variants"]) == 2


@pytest.mark.django_db
def test_admin_product_detail_reflects_real_stock(client, manager, default_location):
    """
    Regression test: GET /admin/products/{id} must compute real availability via
    inventory.selectors, the same read-path composition the public ProductDetailView uses
    (§8.1) — an earlier version hardcoded an empty availability context, which silently made
    every variant look like it had zero stock everywhere in the back office (Products page,
    Sell page) regardless of what record_movement had actually recorded.
    """
    from apps.catalog import services as catalog_services
    from apps.inventory import services as inventory_services

    category = CategoryFactory()
    product = catalog_services.create_product(actor=manager, name="Classic Tee", category_id=category.id,
                                               gender="unisex")
    variants = catalog_services.generate_variant_matrix(actor=manager, product=product, sizes=["M"],
                                                          colors=["black"], base_price_amount=2999)
    inventory_services.record_movement(variant_id=variants[0].id, delta=7, reason="receipt")

    client.force_login(manager)
    resp = client.get(f"/api/v1/admin/products/{product.id}")

    assert resp.status_code == 200
    assert resp.json()["variants"][0]["available"] == 7


@pytest.mark.django_db
def test_worker_cannot_create_product_but_can_view(client, worker):
    """Role matrix: "Create / edit products" is manager+ only; worker can still browse (§6.3)."""
    client.force_login(worker)
    category = CategoryFactory()

    create_resp = client.post(
        "/api/v1/admin/products",
        {"name": "Blocked", "category": category.id, "gender": "unisex"},
        content_type="application/json",
    )
    assert create_resp.status_code == 403

    list_resp = client.get("/api/v1/admin/products")
    assert list_resp.status_code == 200


@pytest.mark.django_db
def test_generate_variant_matrix_requires_manager(client, worker):
    client.force_login(worker)
    category = CategoryFactory()
    product_resp_owner = UserFactory()
    from apps.catalog import services as catalog_services

    product = catalog_services.create_product(actor=product_resp_owner, name="X", category_id=category.id,
                                               gender="unisex")

    resp = client.post(
        f"/api/v1/admin/products/{product.id}/variants/matrix",
        {"sizes": ["M"], "colors": ["red"], "base_price_amount": 1000},
        content_type="application/json",
    )
    assert resp.status_code == 403
