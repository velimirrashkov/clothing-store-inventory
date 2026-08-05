"""Thin. Parse -> call service/selector -> serialize (see architecture-spec.md §2.1)."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasPerm

from .. import selectors, services
from ..models import Delivery, Supplier
from .serializers import (
    DeliveryCreateSerializer,
    DeliverySerializer,
    ProductSupplierSerializer,
    SetProductSupplierCostSerializer,
    SupplierSerializer,
)


class SupplierListCreateView(ListAPIView):
    """GET /api/v1/admin/suppliers?all=true  POST create (see §7.2-style back-office CRUD)."""

    serializer_class = SupplierSerializer
    pagination_class = None

    def get_permissions(self):
        # Any worker who can receive a delivery needs to pick a supplier from this list; only
        # managers create/edit supplier records.
        perm = "suppliers.manage_suppliers" if self.request.method == "POST" else "suppliers.receive_delivery"
        return [HasPerm(perm)]

    def get_queryset(self):
        return selectors.suppliers(active_only=self.request.query_params.get("all") != "true")

    def post(self, request):
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = services.create_supplier(actor=request.user, **serializer.validated_data)
        return Response(SupplierSerializer(supplier).data, status=status.HTTP_201_CREATED)


class SupplierDetailView(APIView):
    """PATCH /api/v1/admin/suppliers/{id}"""

    permission_classes = [HasPerm("suppliers.manage_suppliers")]

    def patch(self, request, supplier_id):
        supplier = get_object_or_404(Supplier, id=supplier_id)
        serializer = SupplierSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        supplier = services.update_supplier(actor=request.user, supplier=supplier, **serializer.validated_data)
        return Response(SupplierSerializer(supplier).data)


class ProductVendorCatalogView(APIView):
    """
    GET/POST /api/v1/admin/products/{id}/suppliers — a product's vendor cost catalog.
    Manager+ only in both directions: quoted supplier costs are pricing/margin data, closer in
    sensitivity to "change prices" (manager+ in the role matrix, §6.3) than day-to-day receiving.
    """

    permission_classes = [HasPerm("suppliers.manage_suppliers")]

    def get(self, request, product_id):
        links = selectors.vendor_catalog_for_product(product_id)
        return Response(ProductSupplierSerializer(links, many=True).data)

    def post(self, request, product_id):
        serializer = SetProductSupplierCostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link = services.set_product_supplier_cost(actor=request.user, product_id=product_id,
                                                    **serializer.validated_data)
        return Response(ProductSupplierSerializer(link).data, status=status.HTTP_201_CREATED)


class DeliveryListCreateView(ListAPIView):
    """GET /api/v1/admin/deliveries?supplier=  POST receive a delivery — stock lands immediately."""

    serializer_class = DeliverySerializer
    permission_classes = [HasPerm("suppliers.receive_delivery")]

    def get_queryset(self):
        return selectors.deliveries(supplier_id=self.request.query_params.get("supplier"))

    def post(self, request):
        serializer = DeliveryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delivery = services.receive_delivery(actor=request.user, **serializer.validated_data)
        return Response(DeliverySerializer(delivery).data, status=status.HTTP_201_CREATED)


class DeliveryDetailView(APIView):
    """GET /api/v1/admin/deliveries/{id}"""

    permission_classes = [HasPerm("suppliers.receive_delivery")]

    def get(self, request, delivery_id):
        delivery = get_object_or_404(
            Delivery.objects.select_related("supplier").prefetch_related("lines", "lines__variant"),
            id=delivery_id,
        )
        return Response(DeliverySerializer(delivery).data)
