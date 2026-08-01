from rest_framework.generics import ListAPIView

from apps.core.pagination import CursorPagination
from apps.core.permissions import HasPerm

from .. import selectors
from .serializers import AuditLogSerializer


class AuditLogListView(ListAPIView):
    """GET /api/v1/admin/audit?object_type=&object_id=&actor= (see architecture-spec.md §7.2)."""

    serializer_class = AuditLogSerializer
    permission_classes = [HasPerm("audit.view_auditlog")]
    pagination_class = CursorPagination

    def get_queryset(self):
        params = self.request.query_params
        return selectors.search(
            object_type=params.get("object_type"),
            object_id=params.get("object_id"),
            actor_id=params.get("actor"),
        )
