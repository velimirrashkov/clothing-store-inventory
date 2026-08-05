"""Covers the count list/detail endpoints added for the stocktake UI (see architecture-spec.md §7.2)."""
import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import VariantFactory
from apps.inventory import services


@pytest.fixture
def worker(db):
    call_command("seed_roles")
    user = UserFactory()
    user.groups.add(Group.objects.get(name="worker"))
    return user


@pytest.mark.django_db
def test_open_list_and_view_count(client, worker, default_location):
    variant = VariantFactory()
    services.record_movement(variant_id=variant.id, delta=7, reason="receipt")
    client.force_login(worker)

    open_resp = client.post("/api/v1/admin/inventory/counts", content_type="application/json")
    assert open_resp.status_code == 201
    count_id = open_resp.json()["id"]

    list_resp = client.get("/api/v1/admin/inventory/counts?status=open")
    assert list_resp.status_code == 200
    assert any(c["id"] == count_id for c in list_resp.json())

    detail_resp = client.get(f"/api/v1/admin/inventory/counts/{count_id}")
    assert detail_resp.status_code == 200
    body = detail_resp.json()
    line = next(entry for entry in body["lines"] if entry["variant"] == variant.id)
    assert line["expected"] == 7
    assert line["sku"] == variant.sku

    submit_resp = client.post(
        f"/api/v1/admin/inventory/counts/{count_id}/lines",
        {"variant_id": variant.id, "counted": 5},
        content_type="application/json",
    )
    assert submit_resp.status_code == 200

    close_resp = client.post(f"/api/v1/admin/inventory/counts/{count_id}/close", content_type="application/json")
    assert close_resp.status_code == 200
    assert services.get_available(variant.id) == 5


@pytest.mark.django_db
def test_bulk_submit_count_lines(client, worker, default_location):
    v1 = VariantFactory()
    v2 = VariantFactory()
    services.record_movement(variant_id=v1.id, delta=10, reason="receipt")
    services.record_movement(variant_id=v2.id, delta=4, reason="receipt")
    client.force_login(worker)

    count_id = client.post("/api/v1/admin/inventory/counts", content_type="application/json").json()["id"]

    resp = client.post(
        f"/api/v1/admin/inventory/counts/{count_id}/lines/bulk",
        {"lines": [{"variant_id": v1.id, "counted": 9}, {"variant_id": v2.id, "counted": 4}]},
        content_type="application/json",
    )
    assert resp.status_code == 200
    counted_by_variant = {line["variant"]: line["counted"] for line in resp.json()}
    assert counted_by_variant[v1.id] == 9
    assert counted_by_variant[v2.id] == 4

    close_resp = client.post(f"/api/v1/admin/inventory/counts/{count_id}/close", content_type="application/json")
    assert close_resp.status_code == 200
    assert services.get_available(v1.id) == 9
    assert services.get_available(v2.id) == 4


@pytest.mark.django_db
def test_reopen_closed_count_reverses_then_allows_recorrection(client, worker, default_location):
    variant = VariantFactory()
    services.record_movement(variant_id=variant.id, delta=10, reason="receipt")
    client.force_login(worker)

    count_id = client.post("/api/v1/admin/inventory/counts", content_type="application/json").json()["id"]
    client.post(
        f"/api/v1/admin/inventory/counts/{count_id}/lines",
        {"variant_id": variant.id, "counted": 8},  # data-entry mistake — should have been 9
        content_type="application/json",
    )
    client.post(f"/api/v1/admin/inventory/counts/{count_id}/close", content_type="application/json")
    assert services.get_available(variant.id) == 8

    reopen_resp = client.post(f"/api/v1/admin/inventory/counts/{count_id}/reopen", content_type="application/json")
    assert reopen_resp.status_code == 200
    assert reopen_resp.json()["status"] == "open"
    assert services.get_available(variant.id) == 10  # reversed back to pre-count reality

    detail = client.get(f"/api/v1/admin/inventory/counts/{count_id}").json()
    line = next(entry for entry in detail["lines"] if entry["variant"] == variant.id)
    assert line["expected"] == 10  # frozen snapshot untouched, still correct after reversal

    client.post(
        f"/api/v1/admin/inventory/counts/{count_id}/lines",
        {"variant_id": variant.id, "counted": 9},  # the correction
        content_type="application/json",
    )
    close_again = client.post(f"/api/v1/admin/inventory/counts/{count_id}/close", content_type="application/json")
    assert close_again.status_code == 200
    assert services.get_available(variant.id) == 9

    # the original (wrong) and reversing movements are still there — nothing was deleted
    from apps.inventory.models import StockMovement
    reasons = list(StockMovement.objects.filter(variant=variant).order_by("id").values_list("reason", flat=True))
    assert reasons == ["receipt", "count_adjustment", "correction", "count_adjustment"]
