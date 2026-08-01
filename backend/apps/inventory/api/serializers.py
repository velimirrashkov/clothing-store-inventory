from rest_framework import serializers

from ..models import Reservation, StockCount, StockCountLine, StockLevel, StockMovement


class StockLevelSerializer(serializers.ModelSerializer):
    available = serializers.IntegerField(read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)

    class Meta:
        model = StockLevel
        fields = ["variant", "sku", "location", "on_hand", "reserved", "available", "updated_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ["id", "variant", "location", "delta", "reason", "reference", "note", "actor", "created_at"]
        read_only_fields = ["id", "actor", "created_at"]


class MovementCreateSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    delta = serializers.IntegerField()
    reason = serializers.ChoiceField(choices=StockMovement.REASON_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)
    reference = serializers.CharField(required=False, allow_blank=True)


class BarcodeLookupSerializer(serializers.Serializer):
    barcode = serializers.CharField()


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["id", "variant", "location", "quantity", "order", "cart", "status", "expires_at", "created_at"]


class StockCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCount
        fields = ["id", "location", "status", "started_by", "started_at", "closed_at"]


class StockCountLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockCountLine
        fields = ["id", "count", "variant", "expected", "counted", "counted_by", "counted_at"]
