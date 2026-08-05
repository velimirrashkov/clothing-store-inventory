"""
Supplier records, a per-product vendor cost catalog, and a delivery log. Deliberately lighter
than a formal Purchase Order workflow (no draft/ordered/partial-received stages) — a Delivery
is receive-and-record-immediately; see services.receive_delivery.

Dependency direction (§2.3): this app depends on catalog (Product/Variant) and inventory
(record_movement, Location), never the reverse.
"""
from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Supplier(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    contact_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        permissions = [
            ("manage_suppliers", "Can create/edit suppliers and vendor pricing"),
            ("receive_delivery", "Can log a delivery / receive stock from a supplier"),
        ]

    def __str__(self):
        return self.name


class ProductSupplier(TimeStampedModel):
    """Vendor catalog: a product can be sourced from multiple suppliers at different costs."""

    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="supplier_links")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="product_links")
    cost_price = models.BigIntegerField()  # minor units — the quoted cost, not what any one delivery paid
    currency = models.CharField(max_length=3, default="EUR")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "supplier"], name="uniq_product_supplier"),
        ]

    def __str__(self):
        return f"{self.product} <- {self.supplier}"


class Delivery(TimeStampedModel):
    """One receiving event — stock lands the moment this is created (see services.receive_delivery)."""

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="deliveries")
    location = models.ForeignKey("inventory.Location", on_delete=models.PROTECT)
    reference = models.CharField(max_length=64, blank=True)  # supplier's invoice/delivery-note number
    note = models.TextField(blank=True)
    currency = models.CharField(max_length=3, default="EUR")
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Delivery #{self.id} from {self.supplier}"


class DeliveryLine(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name="lines")
    variant = models.ForeignKey("catalog.Variant", on_delete=models.RESTRICT)
    quantity = models.PositiveIntegerField()
    unit_cost = models.BigIntegerField()  # minor units, frozen at receive time

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name="delivery_line_qty_gt_0")]

    @property
    def line_total(self) -> int:
        return self.quantity * self.unit_cost
