from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

urlpatterns = [
    # Break-glass Django admin — superuser + MFA only, not a daily interface (see architecture-spec.md §9).
    path("django-admin-x7q/", admin.site.urls),
    path("api/v1/", include("config.api_urls")),
    # OpenAPI schema — the source for a generated TS client per §9. Frontend types are
    # hand-maintained for now (see frontend/src/api/types.ts); codegen is a follow-up.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
]
