"""Thin. Parse -> call service/selector -> serialize (see architecture-spec.md §2.1, §7.2)."""
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import CursorPagination
from apps.core.permissions import HasPerm

from .. import selectors, services
from ..models import CartLine, Order
from .serializers import (
    AddLineSerializer,
    CancelOrderSerializer,
    CartLineSerializer,
    CartSerializer,
    ConfirmOrderSerializer,
    OrderSerializer,
    PosOrderCreateSerializer,
    RefundOrderSerializer,
    ShipOrderSerializer,
    UpdateLineSerializer,
)


class OrderCursorPagination(CursorPagination):
    # Order has placed_at (auto_now_add), not created_at — see the model's field list in §4.7.
    ordering = "-placed_at"


def _current_cart(request):
    """Storefront cart identity: session for guests, user for logged-in buyers (see §6.1)."""
    if not request.session.session_key:
        request.session.save()
    return services.get_or_create_cart(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key,
    )


# --- Storefront: cart + checkout (public, session/user-scoped) -------------------------------

class CartView(APIView):
    """POST creates or fetches the current cart; GET returns its contents (see §7.2)."""

    permission_classes = [AllowAny]

    def post(self, request):
        cart = _current_cart(request)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        cart = _current_cart(request)
        return Response(CartSerializer(cart).data)


class CartLineListCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cart = _current_cart(request)
        serializer = AddLineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        line = services.add_line(cart=cart, **serializer.validated_data)
        return Response(CartLineSerializer(line).data, status=status.HTTP_201_CREATED)


class CartLineDetailView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, line_id):
        cart = _current_cart(request)
        serializer = UpdateLineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            line = services.update_line(cart=cart, line_id=line_id, **serializer.validated_data)
        except CartLine.DoesNotExist:
            raise Http404 from None
        return Response(CartLineSerializer(line).data)

    def delete(self, request, line_id):
        cart = _current_cart(request)
        services.remove_line(cart=cart, line_id=line_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckoutStartView(APIView):
    """POST /api/v1/checkout/start -> creates reservations, returns expiry (see §7.2)."""

    permission_classes = [AllowAny]

    def post(self, request):
        cart = _current_cart(request)
        reservations = services.start_checkout(cart)
        return Response(
            {"expires_at": reservations[0].expires_at, "reservation_ids": [r.id for r in reservations]},
            status=status.HTTP_201_CREATED,
        )


class CheckoutConfirmView(APIView):
    """POST /api/v1/checkout/confirm -> creates order, commits reservations (see §7.2)."""

    permission_classes = [AllowAny]

    def post(self, request):
        cart = _current_cart(request)
        serializer = ConfirmOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.confirm_order(
            cart=cart, user=request.user if request.user.is_authenticated else None,
            **serializer.validated_data,
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


# --- Buyer account -----------------------------------------------------------------------------

class MyOrderListView(ListAPIView):
    """GET /api/v1/me/orders (see §7.2)."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderCursorPagination

    def get_queryset(self):
        return selectors.orders_for_user(self.request.user)


class MyOrderDetailView(APIView):
    """GET /api/v1/me/orders/{public_id} (see §7.2, §6.2 for the IDOR-safe lookup)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        try:
            order = selectors.get_order_for_user(public_id=public_id, user=request.user)
        except Order.DoesNotExist:
            raise Http404 from None
        return Response(OrderSerializer(order).data)


# --- Back-office ---------------------------------------------------------------------------------

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


class AdminOrderListView(ListAPIView):
    """GET /api/v1/admin/orders?status=&channel=&from=&to= (see §7.2)."""

    serializer_class = OrderSerializer
    permission_classes = [HasPerm("orders.view_any_order")]
    pagination_class = OrderCursorPagination

    def get_queryset(self):
        params = self.request.query_params
        return selectors.search_orders(
            status=params.get("status"), channel=params.get("channel"),
            date_from=params.get("from"), date_to=params.get("to"),
        )


class AdminOrderDetailView(RetrieveAPIView):
    """GET /api/v1/admin/orders/{public_id}"""

    serializer_class = OrderSerializer
    permission_classes = [HasPerm("orders.view_any_order")]
    lookup_field = "public_id"
    queryset = Order.objects.prefetch_related("lines")


class OrderFulfilView(APIView):
    """POST /api/v1/admin/orders/{public_id}/fulfil"""

    permission_classes = [HasPerm("orders.fulfil_order")]

    def post(self, request, public_id):
        order = get_object_or_404(Order, public_id=public_id)
        order = services.fulfil_order(order=order, actor=request.user)
        return Response(OrderSerializer(order).data)


class OrderShipView(APIView):
    """POST /api/v1/admin/orders/{public_id}/ship {carrier, tracking_number}"""

    permission_classes = [HasPerm("orders.fulfil_order")]

    def post(self, request, public_id):
        order = get_object_or_404(Order, public_id=public_id)
        serializer = ShipOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.ship_order(order=order, actor=request.user, **serializer.validated_data)
        return Response(OrderSerializer(order).data)


class OrderRefundView(APIView):
    """POST /api/v1/admin/orders/{public_id}/refund {lines: [{order_line_id, quantity}], restock}"""

    permission_classes = [HasPerm("orders.refund_order")]

    def post(self, request, public_id):
        order = get_object_or_404(Order, public_id=public_id)
        serializer = RefundOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.refund_order(order=order, actor=request.user, **serializer.validated_data)
        return Response(OrderSerializer(order).data)


class OrderCancelView(APIView):
    """POST /api/v1/admin/orders/{public_id}/cancel {reason}"""

    permission_classes = [HasPerm("orders.refund_order")]

    def post(self, request, public_id):
        order = get_object_or_404(Order, public_id=public_id)
        serializer = CancelOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = services.cancel_order(order=order, actor=request.user, **serializer.validated_data)
        return Response(OrderSerializer(order).data)
