"""
AdminPaginacionPresenter — builder of the canonical paginated payload.

The administrative surface uses ONE envelope shape for every list:

    ApiResponse[PaginatedData[ItemOut]]
    → data = { items[], total, page, page_size, total_pages }

`PaginatedData` (`core/pagination.py`) is the canonical container; this
presenter is the single place that fills it, so `total_pages` can never drift
between endpoints and the frontend can mirror the shape 1:1 in Zod
(`contract/api-wrapper-presenter-contract.md` §7).

Pure transformer: no ORM access, no selector calls.
"""
from math import ceil
from typing import TypeVar

from core.pagination import PaginatedData
from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)

T = TypeVar("T")


class AdminPaginacionPresenter:
    """Builder of the canonical `PaginatedData` payload."""

    @staticmethod
    def present_paginado(
        items: list[T],
        total: int,
        params: AdminPaginacionParams,
    ) -> PaginatedData[T]:
        """Build the canonical paginated container.

        Args:
            items: the rows of the requested page.
            total: the TOTAL number of matching rows (not the page size).
            params: the normalized pagination parameters.

        Returns:
            PaginatedData with the items and the pagination metadata.
        """
        total_pages = ceil(total / params.page_size) if params.page_size else 0

        return PaginatedData(
            items=list(items),
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )


__all__ = ["AdminPaginacionPresenter"]
