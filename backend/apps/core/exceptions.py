from rest_framework.views import exception_handler


class DomainError(Exception):
    """Base for business-rule violations raised from services.py. Never raise bare Exception from a service."""

    code = "domain_error"
    message = "A business rule was violated."
    status_code = 400

    def __init__(self, message: str | None = None, **details):
        self.message = message or self.message
        self.details = details
        super().__init__(self.message)


class InsufficientStock(DomainError):
    code = "insufficient_stock"
    message = "Not enough stock available."
    status_code = 409


class ReservedStockConflict(DomainError):
    code = "reserved_stock_conflict"
    message = "Reserved quantity would exceed on-hand quantity."
    status_code = 409


def api_exception_handler(exc, context):
    """Uniform error envelope: {"error": {"code", "message", "details"}} (see architecture-spec.md §7.1)."""
    if isinstance(exc, DomainError):
        from rest_framework.response import Response

        return Response(
            {"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
            status=exc.status_code,
        )

    response = exception_handler(exc, context)
    if response is not None:
        detail = response.data.get("detail", response.data) if isinstance(response.data, dict) else response.data
        response.data = {
            "error": {
                "code": getattr(exc, "default_code", "error"),
                "message": str(detail),
                "details": response.data if isinstance(response.data, dict) else {},
            }
        }
    return response
