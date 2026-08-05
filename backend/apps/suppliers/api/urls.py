"""Back-office supplier/delivery management (see architecture-spec.md-style §7.2 conventions)."""
from django.urls import path

from . import views

urlpatterns = [
    path("suppliers", views.SupplierListCreateView.as_view(), name="supplier-list-create"),
    path("suppliers/<int:supplier_id>", views.SupplierDetailView.as_view(), name="supplier-detail"),
    path("products/<int:product_id>/suppliers", views.ProductVendorCatalogView.as_view(),
         name="product-vendor-catalog"),
    path("deliveries", views.DeliveryListCreateView.as_view(), name="delivery-list-create"),
    path("deliveries/<int:delivery_id>", views.DeliveryDetailView.as_view(), name="delivery-detail"),
]
