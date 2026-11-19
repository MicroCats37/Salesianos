"""Shared HTTP envelope for the Salesianos FEST backend.

Freeze: `FREEZE-ENV-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-01-envelope-error-pagination.md`

This module owns ONE envelope for the whole target backend:

    success -> {"success": True,  "data": T | None, "error": None, "message": str | None}
    error   -> {"success": False, "data": None,
                "error": {"code": str, "message": str,
                          "details": dict | None, "field_errors": list | None},
                "message": None}

Rules that travel with the envelope (FR-01 §4):

- `error.code` is a stable, machine-readable code. It lives in the public error
  catalog (`core.exceptions.PUBLIC_ERROR_MESSAGES`) and is NEVER built by a
  controller.
- `error.message` is public Spanish prose that comes from that catalog. It
  never contains UUIDs, internal ids, SQL, traces, paths, provider payloads,
  secrets or raw exception text.
- `error.details` carries NON-FIELD context only.
- `error.field_errors` is the ONLY channel for field-level errors.
- Pagination has ONE shape and it lives inside `data`:
  `{"items": [...], "total": n, "page": n, "page_size": n, "total_pages": n}`.
  The historical `PaginatedApiResponse` + `meta` form is deprecated and was
  removed from the target (FR-01 §4.3 rule 1).
"""

from decimal import Decimal
from typing import Any, Optional, Generic, TypeVar
from pydantic import Field, BaseModel
from ninja import Schema

from .pagination import PaginatedData

T = TypeVar("T")

# ── Paginación (FR-01 §4.3) ───────────────────────────────────────────────────

#: Página por defecto. La numeración de páginas es base 1.
DEFAULT_PAGE_SIZE = 25

#: Tope de `page_size` aceptado por el contrato.
MAX_PAGE_SIZE = 100


def _decimal_to_float(obj: Any) -> Any:
    """Recursively convert all Decimal values to float in a nested structure.

    Ensures JSON serialization produces numeric values (not strings) for Decimal fields.
    """
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_decimal_to_float(item) for item in obj]
    if isinstance(obj, BaseModel):
        # Serialize via model_dump then convert (model_dump returns plain dict with Decimals intact)
        return _decimal_to_float(obj.model_dump())
    return obj


class FieldError(Schema):
    """A single field-level error.

    FR-01 §4.2: `field_errors` is the ONLY channel for field-level errors.
    `details` must never be used for that purpose.
    """

    field: str = Field(
        ...,
        description="Ruta del campo. Anidado con punto: 'beneficiarios.0.documento'",
    )
    code: str = Field(
        "INVALID_VALUE",
        description="Código estable del error de campo. Por defecto 'INVALID_VALUE'",
    )
    message: str = Field(
        ...,
        description="Prosa pública segura del error de campo",
    )


class ErrorDetail(Schema):
    """Standardized error detail."""

    code: str = Field(..., description="Unique machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(
        None,
        description="Contexto NO-campo opcional. Prohibido usarlo como canal de errores por campo",
    )
    field_errors: Optional[list[FieldError]] = Field(
        None,
        description="Único canal de error por campo",
    )


class ApiResponse(Schema, Generic[T]):
    """Standard API response envelope."""

    success: bool = Field(..., description="Indicates if the API request was successful")
    data: Optional[T] = Field(None, description="The payload of the response")
    error: Optional[ErrorDetail] = Field(None, description="Error details if the request failed")
    message: Optional[str] = Field(
        None,
        description="Human-readable message for the response (e.g. 'Inscripción creada correctamente.')",
    )


def success_response(data: Any = None, message: str | None = None) -> dict:
    """Wrap data in a standard success envelope.

    Pydantic models are serialized via model_dump(mode='json'), which applies
    ser_json_decimal_to_float config to convert Decimals to JSON floats.
    Nested schemas are also serialized via model_dump(mode='json') to ensure
    consistent numeric output throughout the response tree.

    The optional `message` carries a human-readable string that the frontend
    can surface directly to the user (e.g. via a toast). It is None by default
    so silent read endpoints stay quiet. It is FIXED prose declared by the
    controller: it never interpolates ids, UUIDs, amounts or technical text.
    """
    if isinstance(data, BaseModel):
        # mode='json' applies ser_json_decimal_to_float and serializes nested schemas
        data = data.model_dump(mode="json")
    # _decimal_to_float as belt-and-suspenders for any remaining Decimals
    # (e.g., if mode='json' didn't fully recurse for some reason)
    data = _decimal_to_float(data)
    return {"success": True, "data": data, "error": None, "message": message}


def paginated_response(
    items: list,
    total: int,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    message: str | None = None,
) -> dict:
    """Wrap a page of results in the single frozen pagination shape.

    The pagination metadata lives INSIDE `data` (FR-01 §4.3). There is no
    `meta` key at the root of the envelope and no second pagination shape.

    - `page` is 1-based.
    - `page_size` defaults to 25 and is capped at 100.
    - `total_pages` is `ceil(total / page_size)` and is 0 when there are no rows.
    """
    page = max(1, int(page))
    page_size = max(1, min(int(page_size), MAX_PAGE_SIZE))
    total = max(0, int(total))
    total_pages = (total + page_size - 1) // page_size if total else 0

    data = PaginatedData(
        items=list(items),
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
    return success_response(data.model_dump(mode="json"), message=message)


def error_response(
    code: str,
    message: str,
    details: dict | None = None,
    status: int = 400,
    field_errors: list | None = None,
) -> tuple[dict, int]:
    """Return a standard error envelope with HTTP status code.

    `message` MUST be public prose taken from the error catalog
    (`core.exceptions.PUBLIC_ERROR_MESSAGES`). The caller is responsible for
    never passing raw exception text here.

    `details` carries non-field context only. Field-level errors travel in
    `field_errors`, each entry being `{field, code, message}`.
    """
    body = {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "field_errors": field_errors,
        },
        "message": None,
    }
    return body, status


__all__ = [
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "ApiResponse",
    "ErrorDetail",
    "FieldError",
    "PaginatedData",
    "error_response",
    "paginated_response",
    "success_response",
]
