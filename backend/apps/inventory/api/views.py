"""Thin. Parse -> call service -> serialize (see architecture-spec.md §2.1, §7.2)."""
from django.db.models import F
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import CursorPagination
from apps.core.permissions import HasPerm

from .. import services
from ..models import StockLevel
from .serializers import (
    BarcodeLookupSerializer,
    MovementCreateSerializer,
    StockCountLineSerializer,
    StockCountSerializer,
    StockLevelSerializer,
    StockMovementSerializer,
)


class StockLevelListView(ListAPIView):
    """GET /api/v1/admin/inventory/levels?low_stock=true&q="""

    serializer_class = StockLevelSerializer
    permission_classes = [HasPerm("inventory.adjust_stock")]
    pagination_class = CursorPagination

    def get_queryset(self):
        qs = StockLevel.objects.select_related("variant").annotate(_available=F("on_hand") - F("reserved"))
        params = self.request.query_params
        if params.get("low_stock") == "true":
            qs = qs.filter(_available__lte=5)
        if q := params.get("q"):
            qs = qs.filter(variant__sku__icontains=q)
        return qs


class StockMovementCreateView(APIView):
    """POST /api/v1/admin/inventory/movements {variant_id, delta, reason, note}"""

    permission_classes = [HasPerm("inventory.adjust_stock")]

    def post(self, request):
        serializer = MovementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movement = services.record_movement(actor=request.user, **serializer.validated_data)
        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class BarcodeLookupView(APIView):
    """POST /api/v1/admin/inventory/lookup {barcode} -> variant + level"""

    permission_classes = [HasPerm("inventory.adjust_stock")]

    def post(self, request):
        from apps.catalog.api.serializers import VariantStaffSerializer
        from apps.catalog.models import Variant

        serializer = BarcodeLookupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            variant = Variant.objects.get(barcode=serializer.validated_data["barcode"])
        except Variant.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "No variant with that barcode.", "details": {}}},
                status=status.HTTP_404_NOT_FOUND,
            )
        availability = {variant.id: services.get_available(variant.id)}
        data = VariantStaffSerializer(variant, context={"availability": availability}).data
        return Response(data)


class StockCountOpenView(APIView):
    permission_classes = [HasPerm("inventory.run_count")]

    def post(self, request):
        location_id = request.data.get("location_id") or services.default_location_id()
        count = services.open_count(location_id=location_id, actor=request.user)
        return Response(StockCountSerializer(count).data, status=status.HTTP_201_CREATED)


class StockCountLineSubmitView(APIView):
    permission_classes = [HasPerm("inventory.run_count")]

    def post(self, request, count_id):
        line = services.submit_count_line(
            count_id=count_id, variant_id=request.data["variant_id"],
            counted=request.data["counted"], actor=request.user,
        )
        return Response(StockCountLineSerializer(line).data)


class StockCountCloseView(APIView):
    permission_classes = [HasPerm("inventory.run_count")]

    def post(self, request, count_id):
        count = services.close_count(count_id=count_id, actor=request.user)
        return Response(StockCountSerializer(count).data)
