import pytest
from django.contrib.auth.models import Permission

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import VariantFactory
from apps.inventory import services as inventory_services
from apps.orders import selectors, services
from apps.orders.models import Order

SHIPPING_ADDRESS = {"recipient_name": "Ada Lovelace", "line1": "1 Analytical Engine Way",
                    "city": "Sofia", "postcode": "1000", "country": "BG"}


def _confirmed_order(owner):
    variant = VariantFactory()
    inventory_services.record_movement(variant_id=variant.id, delta=5, reason="receipt")
    cart = services.get_or_create_cart(user=owner)
    services.add_line(cart=cart, variant_id=variant.id, quantity=1)
    services.start_checkout(cart)
    return services.confirm_order(cart=cart, user=owner, email="x@example.com",
                                   shipping_address=SHIPPING_ADDRESS)


@pytest.mark.django_db
def test_owner_can_fetch_their_own_order(default_location):
    owner = UserFactory()
    order = _confirmed_order(owner)

    fetched = selectors.get_order_for_user(public_id=order.public_id, user=owner)

    assert fetched.id == order.id


@pytest.mark.django_db
def test_buyer_cannot_fetch_another_buyers_order(default_location):
    """IDOR case from architecture-spec.md §10.2/§6.2 — buyer A requesting buyer B's order must
    raise DoesNotExist so the API layer can turn it into a 404, never a 403 that would confirm
    the order exists."""
    owner = UserFactory()
    other_buyer = UserFactory()
    order = _confirmed_order(owner)

    with pytest.raises(Order.DoesNotExist):
        selectors.get_order_for_user(public_id=order.public_id, user=other_buyer)


@pytest.mark.django_db
def test_staff_with_view_any_order_can_fetch_any_order(default_location):
    owner = UserFactory()
    staff = UserFactory()
    staff.user_permissions.add(Permission.objects.get(codename="view_any_order", content_type__app_label="orders"))
    order = _confirmed_order(owner)

    fetched = selectors.get_order_for_user(public_id=order.public_id, user=staff)

    assert fetched.id == order.id
