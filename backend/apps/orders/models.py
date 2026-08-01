"""
Schema per architecture-spec.md §4.7. `inventory.Reservation` FKs into `Cart`/`Order` so these tables
exist from day one; online checkout/fulfilment services.py logic is still deferred to Phase 2 (§13).
POS order entry (`create_pos_order`, Phase 1) is implemented in services.py and needed two deliberate
deviations from the spec's literal schema: `email` and `shipping_address` are nullable here, because a
walk-in till sale has neither — the spec's NOT NULL assumes online guest checkout, which still collects
an email.
"""
import uuid

from django.conf import settings
from django.db import models


class Cart(models.Model):
    STATUS_CHOICES = [("active", "active"), ("converted", "converted"), ("abandoned", "abandoned")]

    public_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)


class CartLine(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey("catalog.Variant", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_amount = models.BigIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["cart", "variant"], name="uniq_cart_variant")]


class Order(models.Model):
    """
    Order status machine, enforced in services.py — never allow arbitrary status writes (§8.3):

        pending_payment -> paid -> processing -> shipped -> delivered
               |            |          |
               +-> cancelled <---------+
                            +-> refunded (partial or full)
    """

    CHANNEL_CHOICES = [("online", "online"), ("pos", "pos")]
    STATUS_CHOICES = [
        ("pending_payment", "pending_payment"), ("paid", "paid"), ("processing", "processing"),
        ("shipped", "shipped"), ("delivered", "delivered"), ("cancelled", "cancelled"),
        ("refunded", "refunded"),
    ]
    PAYMENT_STATUS_CHOICES = [
        ("pending", "pending"), ("paid", "paid"), ("refunded", "refunded"), ("failed", "failed"),
    ]
    PAYMENT_METHOD_CHOICES = [("cash", "cash"), ("card", "card")]

    public_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=20, unique=True)  # e.g. ORD-2026-00417
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(null=True, blank=True)  # POS sales rarely have one; see module docstring
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending_payment")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")
    # Recorded for till reconciliation/reporting only — no processor integration (see §12, deferred).
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    subtotal_amount = models.BigIntegerField()
    discount_amount = models.BigIntegerField(default=0)
    shipping_amount = models.BigIntegerField(default=0)
    tax_amount = models.BigIntegerField(default=0)
    total_amount = models.BigIntegerField()
    currency = models.CharField(max_length=3)
    discount = models.ForeignKey("pricing.Discount", null=True, blank=True, on_delete=models.SET_NULL)
    shipping_address = models.JSONField(null=True, blank=True)  # frozen snapshot, not a FK
    billing_address = models.JSONField(null=True, blank=True)
    placed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "-placed_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["reference"]),
        ]
        permissions = [
            ("create_pos_order", "Can ring up an in-store sale"),
            ("fulfil_order", "Can fulfil order"),
            ("view_any_order", "Can view any user's order"),
            ("refund_order", "Can issue refunds"),
            ("view_reports", "Can view sales/stock reports"),
        ]

    def __str__(self):
        return self.reference


class OrderLine(models.Model):
    """Freeze everything at purchase time (see architecture-spec.md §4.7)."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey("catalog.Variant", on_delete=models.RESTRICT)
    sku = models.CharField(max_length=64)
    product_name = models.CharField(max_length=255)
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=40)
    quantity = models.PositiveIntegerField()
    unit_amount = models.BigIntegerField()
    line_total = models.BigIntegerField()


class Shipment(models.Model):
    STATUS_CHOICES = [
        ("pending", "pending"), ("shipped", "shipped"), ("delivered", "delivered"), ("returned", "returned"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="shipments")
    carrier = models.CharField(max_length=40)
    tracking_number = models.CharField(max_length=80, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)


class Return(models.Model):
    STATUS_CHOICES = [("requested", "requested"), ("approved", "approved"), ("received", "received"),
                       ("refunded", "refunded"), ("rejected", "rejected")]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="returns")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
    reason = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)


class ReturnLine(models.Model):
    return_request = models.ForeignKey(Return, on_delete=models.CASCADE, related_name="lines")
    order_line = models.ForeignKey(OrderLine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    restock = models.BooleanField(default=True)
