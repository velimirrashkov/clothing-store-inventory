from rest_framework import serializers

from ..models import Cart, CartLine, Order, OrderLine


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
            "subtotal_amount", "discount_amount", "shipping_amount", "tax_amount", "total_amount",
            "currency", "placed_at", "lines",
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


class CartLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartLine
        fields = ["id", "variant", "quantity", "unit_amount", "added_at"]


class CartSerializer(serializers.ModelSerializer):
    lines = CartLineSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["public_id", "status", "lines", "created_at", "updated_at"]


class AddLineSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class UpdateLineSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class ConfirmOrderSerializer(serializers.Serializer):
    """POST /api/v1/checkout/confirm (see architecture-spec.md §7.2)."""

    email = serializers.EmailField()
    shipping_address = serializers.JSONField()
    billing_address = serializers.JSONField(required=False, allow_null=True)
    payment_ref = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ShipOrderSerializer(serializers.Serializer):
    carrier = serializers.CharField(max_length=40)
    tracking_number = serializers.CharField(max_length=80, required=False, allow_null=True, allow_blank=True)


class RefundLineSerializer(serializers.Serializer):
    order_line_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class RefundOrderSerializer(serializers.Serializer):
    lines = RefundLineSerializer(many=True)
    restock = serializers.BooleanField(default=True)

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError("At least one line is required.")
        return value


class CancelOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
