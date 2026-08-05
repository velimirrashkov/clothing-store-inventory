from django.contrib import admin

from .models import Delivery, DeliveryLine, ProductSupplier, Supplier


class DeliveryLineInline(admin.TabularInline):
    model = DeliveryLine
    extra = 0


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier", "location", "reference", "received_by", "created_at")
    inlines = [DeliveryLineInline]

    def has_change_permission(self, request, obj=None):
        return False  # a delivery is a receiving record, not an editable document

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Supplier)
admin.site.register(ProductSupplier)
