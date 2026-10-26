"""
AdminListadoResult — generic container of a paginated admin read.

Every list endpoint of the administrative surface answers the SAME shape:

    ApiResponse[PaginatedData[ItemOut]]
    → data = { items[], total, page, page_size, total_pages }

The pagination parameters travel inside the result so the presenter can build
the canonical container in ONE place (`AdminPaginacionPresenter`), and the
`total` is the number of MATCHING rows — never the size of the page
(`contract/api-wrapper-presenter-contract.md` §7).
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)

T = TypeVar("T")


class AdminListadoResult(BaseModel, Generic[T]):
    """A page of rows plus the total number of matching rows."""

    items: list[T]
    total: int
    params: AdminPaginacionParams


__all__ = ["AdminListadoResult"]
