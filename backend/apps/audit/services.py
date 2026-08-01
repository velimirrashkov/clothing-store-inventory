"""
Called explicitly from services rather than via signals — signals make it too easy to lose the
actor and the intent (see architecture-spec.md §8.5).
"""
from .models import AuditLog


def record(*, actor=None, action: str, object_type: str, object_id: str, changes: dict | None = None, request=None):
    ip_address = None
    user_agent = None
    if request is not None:
        ip_address = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

    return AuditLog.objects.create(
        actor=actor if actor and getattr(actor, "is_authenticated", False) else None,
        actor_email=getattr(actor, "email", None),
        action=action,
        object_type=object_type,
        object_id=object_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
