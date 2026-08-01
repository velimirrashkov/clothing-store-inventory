from django.urls import path

from . import views

urlpatterns = [
    path("inventory/levels", views.StockLevelListView.as_view(), name="inventory-levels"),
    path("inventory/movements", views.StockMovementCreateView.as_view(), name="inventory-movements"),
    path("inventory/lookup", views.BarcodeLookupView.as_view(), name="inventory-lookup"),
    path("inventory/counts", views.StockCountListView.as_view(), name="inventory-counts-list-open"),
    path("inventory/counts/<int:count_id>", views.StockCountDetailView.as_view(), name="inventory-counts-detail"),
    path("inventory/counts/<int:count_id>/lines", views.StockCountLineSubmitView.as_view(),
         name="inventory-counts-lines"),
    path("inventory/counts/<int:count_id>/close", views.StockCountCloseView.as_view(),
         name="inventory-counts-close"),
]
