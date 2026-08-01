from django.db.models import QuerySet

from .models import AuditLog


def search(
    *, object_type: str | None = None, object_id: str | None = None, actor_id: int | None = None
) -> QuerySet[AuditLog]:
    qs = AuditLog.objects.all()
    if object_type:
        qs = qs.filter(object_type=object_type)
    if object_id:
        qs = qs.filter(object_id=object_id)
    if actor_id:
        qs = qs.filter(actor_id=actor_id)
    return qs.order_by("-created_at")
