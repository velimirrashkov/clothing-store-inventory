"""Phase 1 stub — schema only, per architecture-spec.md §4.6."""
from django.conf import settings
from django.db import models


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile")
    phone = models.CharField(max_length=32, blank=True)
    marketing_opt_in = models.BooleanField(default=False)
    opt_in_at = models.DateTimeField(null=True, blank=True)
    anonymized_at = models.DateTimeField(null=True, blank=True)  # GDPR anonymization, see architecture-spec.md §7.2


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=60, blank=True)
    recipient_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32, blank=True)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    postcode = models.CharField(max_length=20)
    country = models.CharField(max_length=2)
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)
