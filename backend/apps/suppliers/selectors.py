"""Read queries. Nothing here writes (see architecture-spec.md §2.1)."""
from django.db.models import QuerySet

from .models import Delivery, ProductSupplier, Supplier


def suppliers(*, active_only: bool = True) -> QuerySet[Supplier]:
    qs = Supplier.objects.all()
    return qs.filter(is_active=True) if active_only else qs


def vendor_catalog_for_product(product_id: int) -> QuerySet[ProductSupplier]:
    return ProductSupplier.objects.filter(product_id=product_id).select_related("supplier")


def deliveries(*, supplier_id: int | None = None) -> QuerySet[Delivery]:
    qs = Delivery.objects.select_related("supplier").prefetch_related("lines", "lines__variant")
    if supplier_id:
        qs = qs.filter(supplier_id=supplier_id)
    return qs
