from rest_framework import serializers

from ..models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "actor_email", "action", "object_type", "object_id", "changes", "created_at"]
