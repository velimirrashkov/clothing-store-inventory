from rest_framework.permissions import BasePermission


class HasPerm(BasePermission):
    """Layer 1 endpoint permission (see architecture-spec.md §6.2). Always check permissions, never group names."""

    def __init__(self, perm: str):
        self.perm = perm

    def __call__(self):
        return self

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.has_perm(self.perm))
