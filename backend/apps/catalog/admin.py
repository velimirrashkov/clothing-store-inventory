from django.contrib import admin

from .models import Category, Product, ProductMedia, Variant


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku_prefix", "category", "status", "gender")
    list_filter = ("status", "gender", "category")
    search_fields = ("name", "slug")
    inlines = [VariantInline]

    def sku_prefix(self, obj):
        return obj.slug


admin.site.register(Category)
admin.site.register(Variant)
admin.site.register(ProductMedia)
