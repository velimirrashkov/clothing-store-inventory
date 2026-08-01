"""Back-office order management (see architecture-spec.md §7.2)."""
from django.urls import path

from . import views

urlpatterns = [
    path("orders/pos", views.PosOrderCreateView.as_view(), name="orders-pos-create"),
    path("orders", views.AdminOrderListView.as_view(), name="admin-order-list"),
    path("orders/<uuid:public_id>", views.AdminOrderDetailView.as_view(), name="admin-order-detail"),
    path("orders/<uuid:public_id>/fulfil", views.OrderFulfilView.as_view(), name="admin-order-fulfil"),
    path("orders/<uuid:public_id>/ship", views.OrderShipView.as_view(), name="admin-order-ship"),
    path("orders/<uuid:public_id>/refund", views.OrderRefundView.as_view(), name="admin-order-refund"),
    path("orders/<uuid:public_id>/cancel", views.OrderCancelView.as_view(), name="admin-order-cancel"),
]
