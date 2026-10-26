"""
AdminPaginacionParams — internal DTO of the normalized list parameters.

This is an INPUT DTO of the domain layer: it carries the pagination, search
and sort parameters ALREADY normalized by `AdminPaginacionService`, so every
admin list endpoint applies exactly the same rules.

Fields:
    page: 1-based page number.
    page_size: number of items per page (already clamped to the maximum).
    offset: absolute offset derived from page and page_size.
    q: normalized free-text search term, or None.
    ordering: the RESOLVED ORM ordering expression (server-side whitelist).
"""

from pydantic import BaseModel, Field


class AdminPaginacionParams(BaseModel):
    """Normalized pagination / search / sort parameters of an admin list."""

    page: int = Field(..., ge=1, description="1-based page number")
    page_size: int = Field(..., ge=1, description="Items per page (clamped)")
    offset: int = Field(..., ge=0, description="Absolute offset of the page")
    q: str | None = Field(None, description="Normalized free-text search term")
    ordering: str | None = Field(
        None,
        description="Resolved ORM ordering expression (server-side whitelist)",
    )


__all__ = ["AdminPaginacionParams"]
