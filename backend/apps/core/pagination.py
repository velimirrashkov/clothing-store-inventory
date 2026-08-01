from rest_framework.pagination import CursorPagination as DRFCursorPagination


class CursorPagination(DRFCursorPagination):
    """Cursor pagination on anything unbounded (see architecture-spec.md §7.1). Never offset/page-number."""

    page_size = 50
    max_page_size = 200
    ordering = "-created_at"
