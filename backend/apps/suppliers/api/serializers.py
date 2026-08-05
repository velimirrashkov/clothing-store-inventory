from rest_framework import serializers

from ..models import Delivery, DeliveryLine, ProductSupplier, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "contact_name", "email", "phone", "notes", "is_active"]
        extra_kwargs = {
            "contact_name": {"required": False}, "email": {"required": False},
            "phone": {"required": False}, "notes": {"required": False}, "is_active": {"required": False},
        }


class ProductSupplierSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = ProductSupplier
        fields = ["id", "product", "supplier", "supplier_name", "cost_price", "currency"]


class SetProductSupplierCostSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField()
    cost_price = serializers.IntegerField(min_value=0)
    currency = serializers.CharField(max_length=3, default="EUR")


class DeliveryLineSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source="variant.sku", read_only=True)
    line_total = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeliveryLine
        fields = ["id", "variant", "sku", "quantity", "unit_cost", "line_total"]


class DeliverySerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    lines = DeliveryLineSerializer(many=True, read_only=True)

    class Meta:
        model = Delivery
        fields = ["id", "supplier", "supplier_name", "location", "reference", "note", "currency",
                  "received_by", "created_at", "lines"]


class DeliveryLineInputSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_cost = serializers.IntegerField(min_value=0)


class DeliveryCreateSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField()
    reference = serializers.CharField(required=False, allow_blank=True, default="")
    note = serializers.CharField(required=False, allow_blank=True, default="")
    lines = DeliveryLineInputSerializer(many=True, allow_empty=False)
