"""Storefront: cart, checkout, buyer account (see architecture-spec.md §7.2)."""
from django.urls import path

from . import views

urlpatterns = [
    path("cart", views.CartView.as_view(), name="cart"),
    path("cart/lines", views.CartLineListCreateView.as_view(), name="cart-lines"),
    path("cart/lines/<int:line_id>", views.CartLineDetailView.as_view(), name="cart-line-detail"),
    path("checkout/start", views.CheckoutStartView.as_view(), name="checkout-start"),
    path("checkout/confirm", views.CheckoutConfirmView.as_view(), name="checkout-confirm"),
    path("me/orders", views.MyOrderListView.as_view(), name="my-orders"),
    path("me/orders/<uuid:public_id>", views.MyOrderDetailView.as_view(), name="my-order-detail"),
]
