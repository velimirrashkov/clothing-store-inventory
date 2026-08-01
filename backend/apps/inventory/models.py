"""This is the heart of the system. Read architecture-spec.md §5 before changing anything here."""
from django.conf import settings
from django.db import models


class Location(models.Model):
    """Seeded with exactly one row for now (see architecture-spec.md §4.4)."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    """APPEND ONLY. Never UPDATE, never DELETE (see architecture-spec.md §4.4)."""

    REASON_CHOICES = [
        ("receipt", "receipt"), ("sale_online", "sale_online"), ("sale_pos", "sale_pos"),
        ("return", "return"), ("damage", "damage"), ("loss", "loss"),
        ("count_adjustment", "count_adjustment"), ("correction", "correction"), ("initial_load", "initial_load"),
    ]

    variant = models.ForeignKey("catalog.Variant", on_delete=models.RESTRICT, related_name="stock_movements")
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    delta = models.IntegerField()
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    reference = models.CharField(max_length=64, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~models.Q(delta=0), name="stock_movement_delta_nonzero"),
        ]
        permissions = [
            ("adjust_stock", "Can record stock movements"),
            ("run_count", "Can open/close stocktakes"),
        ]

    def __str__(self):
        return f"{self.variant_id} {self.delta:+d} ({self.reason})"


class StockLevel(models.Model):
    """Denormalized cache of the ledger. If it ever disagrees with the ledger, the ledger wins (see §5.1)."""

    variant = models.ForeignKey("catalog.Variant", on_delete=models.CASCADE, related_name="stock_levels")
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    on_hand = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["variant", "location"], name="uniq_stock_level_variant_location"),
            models.CheckConstraint(condition=models.Q(on_hand__gte=0), name="stock_level_on_hand_gte_0"),
            models.CheckConstraint(condition=models.Q(reserved__gte=0), name="stock_level_reserved_gte_0"),
            models.CheckConstraint(condition=models.Q(reserved__lte=models.F("on_hand")),
                                    name="stock_level_reserved_lte_on_hand"),
        ]

    @property
    def available(self) -> int:
        """Available to sell = on_hand - reserved. Never expose on_hand alone to the storefront (§4.4)."""
        return self.on_hand - self.reserved


class Reservation(models.Model):
    STATUS_CHOICES = [
        ("active", "active"), ("committed", "committed"), ("released", "released"), ("expired", "expired"),
    ]

    variant = models.ForeignKey("catalog.Variant", on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.SET_NULL)
    cart = models.ForeignKey("orders.Cart", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="reservation_quantity_gt_0"),
        ]
        indexes = [
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["variant", "status"]),
        ]


class StockCount(models.Model):
    """Physical stocktake session (see architecture-spec.md §5.6)."""

    STATUS_CHOICES = [("open", "open"), ("closed", "closed")]

    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="open")
    started_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    started_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)


class StockCountLine(models.Model):
    count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey("catalog.Variant", on_delete=models.PROTECT)
    expected = models.IntegerField()
    counted = models.IntegerField(null=True, blank=True)
    counted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="+")
    counted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["count", "variant"], name="uniq_count_variant")]
