from django.contrib import admin

from .models import Location, Reservation, StockCount, StockCountLine, StockLevel, StockMovement


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("variant", "location", "delta", "reason", "reference", "actor", "created_at")
    list_filter = ("reason", "location")
    search_fields = ("reference",)

    def has_change_permission(self, request, obj=None):
        return False  # append-only ledger — see architecture-spec.md §5.2

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Location)
admin.site.register(StockLevel)
admin.site.register(Reservation)
admin.site.register(StockCount)
admin.site.register(StockCountLine)
