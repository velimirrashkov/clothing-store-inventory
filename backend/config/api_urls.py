from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.accounts.api.urls")),
    path("", include("apps.catalog.api.urls")),
    path("admin/", include("apps.inventory.api.urls")),
    path("admin/", include("apps.audit.api.urls")),
]
