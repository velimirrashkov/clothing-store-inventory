import pytest

from apps.accounts.tests.factories import UserFactory
from apps.catalog import services
from apps.catalog.models import Variant
from apps.catalog.tests.factories import CategoryFactory, ProductFactory


@pytest.mark.django_db
def test_generate_variant_matrix_creates_full_grid():
    product = ProductFactory()
    variants = services.generate_variant_matrix(
        actor=UserFactory(), product=product, sizes=["S", "M", "L"], colors=["black", "white"],
        base_price_amount=2999,
    )
    assert len(variants) == 6
    assert Variant.objects.filter(product=product).count() == 6


@pytest.mark.django_db
def test_generate_variant_matrix_is_idempotent_on_rerun():
    product = ProductFactory()
    actor = UserFactory()
    services.generate_variant_matrix(actor=actor, product=product, sizes=["S"], colors=["black"],
                                      base_price_amount=2999)
    services.generate_variant_matrix(actor=actor, product=product, sizes=["S"], colors=["black"],
                                      base_price_amount=2999)
    assert Variant.objects.filter(product=product).count() == 1


@pytest.mark.django_db
def test_archive_product_deactivates_variants_and_keeps_row():
    product = ProductFactory(status="active")
    services.generate_variant_matrix(actor=UserFactory(), product=product, sizes=["M"], colors=["red"],
                                      base_price_amount=1999)

    services.archive_product(actor=UserFactory(), product=product)
    product.refresh_from_db()

    assert product.status == "archived"
    assert product.archived_at is not None
    assert not Variant.objects.filter(product=product, is_active=True).exists()


@pytest.mark.django_db
def test_create_product_generates_unique_slug_on_name_collision():
    category = CategoryFactory()
    actor = UserFactory()
    first = services.create_product(actor=actor, name="Classic Tee", category_id=category.id, gender="unisex")
    second = services.create_product(actor=actor, name="Classic Tee", category_id=category.id, gender="unisex")
    assert first.slug != second.slug
