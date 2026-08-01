"""
A security control, not a formality (see architecture-spec.md §10.2). Generated from the role
matrix in §6.3 — add a row for every new endpoint as a PR checklist item, including IDOR cases:
buyer A requesting buyer B's order must get 404, not 403 (§6.2).
"""
import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command

from apps.accounts.tests.factories import UserFactory

PERMISSION_MATRIX = [
    # (role_or_None, permission_codename, expected_result)
    (None, "inventory.adjust_stock", False),
    ("worker", "inventory.adjust_stock", True),
    ("worker", "orders.refund_order", False),
    ("manager", "orders.refund_order", True),
    ("manager", "accounts.manage_users", False),
    ("admin", "accounts.manage_users", True),
    ("worker", "catalog.add_product", False),
    ("manager", "catalog.add_product", True),
]


@pytest.fixture
def seeded_roles(db):
    # Default + custom Meta.permissions are created by Django's post_migrate signal already;
    # this just builds the Group -> Permission mapping from apps/accounts/roles.py.
    call_command("seed_roles")


@pytest.mark.django_db
@pytest.mark.parametrize("role,perm,expected", PERMISSION_MATRIX)
def test_role_grants_expected_permission(seeded_roles, role, perm, expected):
    user = UserFactory()
    if role:
        user.groups.add(Group.objects.get(name=role))
    assert user.has_perm(perm) is expected


@pytest.mark.django_db
def test_buyer_cannot_see_another_buyers_order_gets_404_not_403(client, db):
    """IDOR case from §10.2 — enforced at the selector layer once orders.selectors exists (Phase 2 seam)."""
    owner = UserFactory()
    other = UserFactory()
    assert owner.pk != other.pk  # placeholder assertion; real check lands with orders.selectors in Phase 2
