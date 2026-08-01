from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.accounts.api.urls")),
    path("", include("apps.catalog.api.urls")),
    path("", include("apps.orders.api.urls")),
    path("admin/", include("apps.inventory.api.urls")),
    path("admin/", include("apps.audit.api.urls")),
    path("admin/", include("apps.orders.api.admin_urls")),
]
