"""Back-office catalog CRUD (see architecture-spec.md §7.2 "Back-office" endpoint list)."""
from django.utils.text import slugify
from rest_framework import serializers

from ..models import Category, Product, Variant
from .serializers import ProductMediaSerializer, VariantStaffSerializer


class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "position", "is_active"]
        extra_kwargs = {"slug": {"required": False}}

    def create(self, validated_data):
        validated_data.setdefault("slug", self._unique_slug(validated_data["name"]))
        return super().create(validated_data)

    @staticmethod
    def _unique_slug(name: str) -> str:
        base = slugify(name)
        slug = base
        n = 1
        while Category.objects.filter(slug=slug).exists():
            n += 1
            slug = f"{base}-{n}"
        return slug


class ProductAdminListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "public_id", "slug", "name", "brand", "gender", "status", "category"]


class ProductAdminDetailSerializer(serializers.ModelSerializer):
    variants = VariantStaffSerializer(many=True, read_only=True)
    media = ProductMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "public_id", "slug", "name", "description", "brand", "gender", "season",
                  "status", "category", "variants", "media"]


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["name", "slug", "description", "brand", "gender", "season", "category"]
        extra_kwargs = {
            "slug": {"required": False},
            "description": {"required": False},
            "brand": {"required": False},
            "season": {"required": False},
        }


class VariantMatrixSerializer(serializers.Serializer):
    sizes = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    colors = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    base_price_amount = serializers.IntegerField(min_value=0)
    currency = serializers.CharField(max_length=3, default="EUR")


class VariantUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        fields = ["size", "color", "color_hex", "price_amount", "currency", "compare_at_amount",
                  "barcode", "is_active"]
        extra_kwargs = {field: {"required": False} for field in fields}


class BarcodeAssignSerializer(serializers.Serializer):
    variant_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
