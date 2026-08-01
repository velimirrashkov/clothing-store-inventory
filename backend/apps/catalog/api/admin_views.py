"""Thin. Parse -> call service -> serialize (see architecture-spec.md §2.1, §7.2)."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasPerm
from apps.inventory import selectors as inventory_selectors

from .. import services
from ..models import Category, Product, Variant
from .admin_serializers import (
    BarcodeAssignSerializer,
    CategoryCreateSerializer,
    ProductAdminDetailSerializer,
    ProductAdminListSerializer,
    ProductWriteSerializer,
    VariantMatrixSerializer,
    VariantUpdateSerializer,
)
from .serializers import VariantStaffSerializer


def _availability_context(variant_ids: list[int]) -> dict:
    """
    Real stock figures, same read-path composition as the public ProductDetailView (see §8.1) —
    every staff-facing variant response must go through this, never a hardcoded {} (which
    silently makes every variant look like it has zero stock — see the bug this fixed).
    """
    return {"availability": inventory_selectors.bulk_availability(variant_ids)}


class AdminProductListCreateView(ListAPIView):
    """GET /api/v1/admin/products?category=&status=  POST create (see §7.2)."""

    serializer_class = ProductAdminListSerializer

    def get_permissions(self):
        perm = "catalog.add_product" if self.request.method == "POST" else "catalog.view_product"
        return [HasPerm(perm)]

    def get_queryset(self):
        qs = Product.objects.select_related("category").order_by("-created_at")
        params = self.request.query_params
        if category_slug := params.get("category"):
            qs = qs.filter(category__slug=category_slug)
        if status_filter := params.get("status"):
            qs = qs.filter(status=status_filter)
        return qs

    def post(self, request):
        serializer = ProductWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = dict(serializer.validated_data)
        category = fields.pop("category")
        product = services.create_product(actor=request.user, category_id=category.id, **fields)
        return Response(ProductAdminDetailSerializer(product, context={"availability": {}}).data,
                         status=status.HTTP_201_CREATED)


class AdminProductDetailView(APIView):
    """GET/PATCH /api/v1/admin/products/{id}"""

    def get_permissions(self):
        perm = "catalog.change_product" if self.request.method == "PATCH" else "catalog.view_product"
        return [HasPerm(perm)]

    def get(self, request, product_id):
        product = get_object_or_404(Product.objects.prefetch_related("variants", "media"), id=product_id)
        context = _availability_context(list(product.variants.values_list("id", flat=True)))
        return Response(ProductAdminDetailSerializer(product, context=context).data)

    def patch(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        serializer = ProductWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = services.update_product(actor=request.user, product=product, **serializer.validated_data)
        context = _availability_context(list(product.variants.values_list("id", flat=True)))
        return Response(ProductAdminDetailSerializer(product, context=context).data)


class AdminProductArchiveView(APIView):
    """POST /api/v1/admin/products/{id}/archive — archive never deletes (see §8.1)."""

    permission_classes = [HasPerm("catalog.change_product")]

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        product = services.archive_product(actor=request.user, product=product)
        context = _availability_context(list(product.variants.values_list("id", flat=True)))
        return Response(ProductAdminDetailSerializer(product, context=context).data)


class VariantMatrixGenerateView(APIView):
    """POST /api/v1/admin/products/{id}/variants/matrix {sizes, colors, base_price_amount, currency}"""

    permission_classes = [HasPerm("catalog.change_product")]

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        serializer = VariantMatrixSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variants = services.generate_variant_matrix(actor=request.user, product=product,
                                                      **serializer.validated_data)
        # Usually brand-new (0 stock), but generate_variant_matrix's get_or_create means a
        # re-run that overlaps an existing size/colour can return a variant with real stock.
        context = _availability_context([v.id for v in variants])
        data = VariantStaffSerializer(variants, many=True, context=context).data
        return Response(data, status=status.HTTP_201_CREATED)


class VariantUpdateView(APIView):
    """PATCH /api/v1/admin/variants/{id} — price, colour, barcode, active flag (see §7.2 "CRUD /variants")."""

    permission_classes = [HasPerm("catalog.change_product")]

    def patch(self, request, variant_id):
        variant = get_object_or_404(Variant, id=variant_id)
        serializer = VariantUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        variant = services.update_variant(actor=request.user, variant=variant, **serializer.validated_data)
        context = _availability_context([variant.id])
        return Response(VariantStaffSerializer(variant, context=context).data)


class BarcodeAssignView(APIView):
    """POST /api/v1/admin/variants/assign-barcodes {variant_ids}"""

    permission_classes = [HasPerm("catalog.change_product")]

    def post(self, request):
        serializer = BarcodeAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variants = services.assign_barcodes(serializer.validated_data["variant_ids"])
        context = _availability_context([v.id for v in variants])
        data = VariantStaffSerializer(variants, many=True, context=context).data
        return Response(data)


class AdminCategoryCreateView(APIView):
    """POST /api/v1/admin/categories — bootstraps the tree; reads still go through the public endpoint."""

    permission_classes = [HasPerm("catalog.change_product")]

    def post(self, request):
        serializer = CategoryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        return Response(CategoryCreateSerializer(category).data, status=status.HTTP_201_CREATED)


class AdminCategoryDetailView(APIView):
    """PATCH /api/v1/admin/categories/{id}"""

    permission_classes = [HasPerm("catalog.change_product")]

    def patch(self, request, category_id):
        category = get_object_or_404(Category, id=category_id)
        serializer = CategoryCreateSerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
