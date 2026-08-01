from rest_framework import serializers

from ..models import Category, Product, ProductMedia, Variant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["slug", "name", "parent", "position"]


class ProductMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMedia
        fields = ["url", "alt_text", "position", "is_primary"]


class VariantPublicSerializer(serializers.ModelSerializer):
    """Buyer-facing: boolean availability only, never exact stock (Layer 3, see architecture-spec.md §6.2)."""

    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Variant
        fields = ["public_id", "sku", "size", "color", "color_hex", "price_amount", "currency",
                   "compare_at_amount", "in_stock"]

    def get_in_stock(self, variant: Variant) -> bool:
        availability = self.context.get("availability", {})
        return availability.get(variant.id, 0) > 0


class VariantStaffSerializer(VariantPublicSerializer):
    """Staff-facing: exact stock figures (Layer 3, see architecture-spec.md §6.2)."""

    available = serializers.SerializerMethodField()

    class Meta(VariantPublicSerializer.Meta):
        fields = VariantPublicSerializer.Meta.fields + ["available", "barcode", "is_active"]

    def get_available(self, variant: Variant) -> int:
        return self.context.get("availability", {}).get(variant.id, 0)


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["public_id", "slug", "name", "brand", "gender", "category"]


class ProductDetailSerializer(serializers.ModelSerializer):
    variants = VariantPublicSerializer(many=True)
    media = ProductMediaSerializer(many=True)

    class Meta:
        model = Product
        fields = ["public_id", "slug", "name", "description", "brand", "gender", "season",
                   "category", "variants", "media"]
