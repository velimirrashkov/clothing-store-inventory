import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Base for every table: created_at/updated_at, timestamptz, UTC (see architecture-spec.md §4.1)."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PublicIdModel(models.Model):
    """Adds a UUID for use in public-facing URLs. Internal PK stays BIGSERIAL (see architecture-spec.md §4.1)."""

    public_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
