"""Thin. Parse -> call service/selector -> serialize (see architecture-spec.md §2.1)."""
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from apps.core.pagination import CursorPagination
from apps.inventory import selectors as inventory_selectors

from .. import selectors
from ..models import Category
from .serializers import CategorySerializer, ProductDetailSerializer, ProductListSerializer


class ProductListView(ListAPIView):
    """GET /api/v1/products?category=&size=&color=&q=&sort=&cursor= (see architecture-spec.md §7.2)."""

    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    pagination_class = CursorPagination

    def get_queryset(self):
        params = self.request.query_params
        qs = selectors.search_products(params.get("q", ""), category_slug=params.get("category"))
        if size := params.get("size"):
            qs = qs.filter(variants__size=size)
        if color := params.get("color"):
            qs = qs.filter(variants__color=color)
        return qs.distinct()


class ProductDetailView(RetrieveAPIView):
    """GET /api/v1/products/{slug} — includes variants + availability booleans (see architecture-spec.md §7.2)."""

    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return selectors.active_products().prefetch_related("variants", "media")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        product = self.get_object()
        variant_ids = list(product.variants.values_list("id", flat=True))
        context["availability"] = inventory_selectors.bulk_availability(variant_ids)
        return context


class CategoryListView(ListAPIView):
    """GET /api/v1/categories (see architecture-spec.md §7.2)."""

    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None
    queryset = Category.objects.filter(is_active=True)
