from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Break-glass Django admin — superuser + MFA only, not a daily interface (see architecture-spec.md §9).
    path("django-admin-x7q/", admin.site.urls),
    path("api/v1/", include("config.api_urls")),
]
