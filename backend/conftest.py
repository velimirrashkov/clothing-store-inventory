import pytest

from apps.inventory.models import Location


@pytest.fixture
def default_location(db):
    return Location.objects.create(code="MAIN", name="Main Store", is_default=True)
