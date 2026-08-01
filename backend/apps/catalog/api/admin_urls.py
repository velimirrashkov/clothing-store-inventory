"""Back-office catalog management (see architecture-spec.md §7.2)."""
from django.urls import path

from . import admin_views as views

urlpatterns = [
    path("products", views.AdminProductListCreateView.as_view(), name="admin-product-list-create"),
    path("products/<int:product_id>", views.AdminProductDetailView.as_view(), name="admin-product-detail"),
    path("products/<int:product_id>/archive", views.AdminProductArchiveView.as_view(),
         name="admin-product-archive"),
    path("products/<int:product_id>/variants/matrix", views.VariantMatrixGenerateView.as_view(),
         name="admin-variant-matrix"),
    path("variants/<int:variant_id>", views.VariantUpdateView.as_view(), name="admin-variant-update"),
    path("variants/assign-barcodes", views.BarcodeAssignView.as_view(), name="admin-variant-barcodes"),
    path("categories", views.AdminCategoryCreateView.as_view(), name="admin-category-create"),
    path("categories/<int:category_id>", views.AdminCategoryDetailView.as_view(), name="admin-category-detail"),
]
