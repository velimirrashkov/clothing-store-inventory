"""Thin. Parse -> call service -> serialize (see architecture-spec.md §2.1, §7.2)."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import HasPerm

from .. import services
from .serializers import OrderSerializer, PosOrderCreateSerializer


class PosOrderCreateView(APIView):
    """POST /api/v1/admin/orders/pos {lines: [{variant_id, quantity}], payment_method}"""

    permission_classes = [HasPerm("orders.create_pos_order")]

    def post(self, request):
        serializer = PosOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.create_pos_order(
            lines=serializer.validated_data["lines"],
            payment_method=serializer.validated_data["payment_method"],
            actor=request.user,
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
