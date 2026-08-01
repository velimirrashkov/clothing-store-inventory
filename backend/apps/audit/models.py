from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Append only. Revoke UPDATE/DELETE on this table from the app DB role (see architecture-spec.md §4.8)."""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    actor_email = models.EmailField(null=True, blank=True)  # frozen, survives user deletion
    action = models.CharField(max_length=60)  # stock.adjust, price.change, role.assign...
    object_type = models.CharField(max_length=60)
    object_id = models.CharField(max_length=64)
    changes = models.JSONField(null=True, blank=True)  # {"field": {"from": x, "to": y}}
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["object_type", "object_id", "-created_at"]),
            models.Index(fields=["actor", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} {self.object_type}:{self.object_id}"
