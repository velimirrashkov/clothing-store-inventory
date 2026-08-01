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
