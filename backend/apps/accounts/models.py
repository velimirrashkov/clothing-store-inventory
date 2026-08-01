import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    See architecture-spec.md §4.2. Roles are Django Groups (buyer/worker/manager/admin),
    seeded by the accounts migrations — always check permissions, never group names.
    """

    public_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_collation="case_insensitive")
    email_verified_at = models.DateTimeField(null=True, blank=True)
    mfa_enabled = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        permissions = [
            ("manage_users", "Can create/deactivate users"),
            ("assign_roles", "Can assign roles to users"),
        ]

    def __str__(self):
        return self.email


class TOTPDevice(models.Model):
    """Mandatory for is_staff users (see architecture-spec.md §6.4). Wraps django-otp's TOTP device."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="totp_device")
    otp_secret = models.CharField(max_length=64)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LoginAttempt(models.Model):
    """Feeds the rate limits in architecture-spec.md §6.4 (5/min/IP, 10/hour/account)."""

    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField()
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["email", "at"]),
            models.Index(fields=["ip_address", "at"]),
        ]
