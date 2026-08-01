from django.contrib import admin

from .models import Cart, CartLine, Order, OrderLine, Return, ReturnLine, Shipment


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "email", "channel", "status", "payment_status", "total_amount", "placed_at")
    list_filter = ("status", "channel", "payment_status")
    search_fields = ("reference", "email")
    inlines = [OrderLineInline]


admin.site.register(Cart)
admin.site.register(CartLine)
admin.site.register(Shipment)
admin.site.register(Return)
admin.site.register(ReturnLine)
