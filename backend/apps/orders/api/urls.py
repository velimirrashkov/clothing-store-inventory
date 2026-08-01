from django.urls import path

from . import views

urlpatterns = [
    path("orders/pos", views.PosOrderCreateView.as_view(), name="orders-pos-create"),
]
