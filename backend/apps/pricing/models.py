"""
Phase 1 stub — schema only, per architecture-spec.md §4.5. `calculate_cart_total` and discount
validation land in services.py in Phase 2 alongside orders.checkout.
"""
from django.db import models


class Discount(models.Model):
    TYPE_CHOICES = [("percent", "percent"), ("fixed", "fixed"), ("free_shipping", "free_shipping")]

    code = models.CharField(max_length=40, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    value = models.IntegerField()
    min_order_amount = models.BigIntegerField(null=True, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code or self.name


class DiscountTarget(models.Model):
    """Optional scoping (see architecture-spec.md §4.5)."""

    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name="targets")
    product = models.ForeignKey("catalog.Product", null=True, blank=True, on_delete=models.CASCADE)
    category = models.ForeignKey("catalog.Category", null=True, blank=True, on_delete=models.CASCADE)
