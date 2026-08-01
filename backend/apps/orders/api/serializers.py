from rest_framework import serializers

from ..models import Order, OrderLine


class OrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLine
        fields = ["sku", "product_name", "size", "color", "quantity", "unit_amount", "line_total"]


class OrderSerializer(serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "public_id", "reference", "channel", "status", "payment_status", "payment_method",
            "subtotal_amount", "tax_amount", "total_amount", "currency", "placed_at", "lines",
        ]


class PosOrderLineInputSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class PosOrderCreateSerializer(serializers.Serializer):
    """POST /api/v1/admin/orders/pos — in-store sale entry (see architecture-spec.md §7.2)."""

    lines = PosOrderLineInputSerializer(many=True)
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHOD_CHOICES)

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError("At least one line is required.")
        return value
