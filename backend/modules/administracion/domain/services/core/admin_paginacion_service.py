"""
AdminPaginacionService — the canonical pagination / search / sort rules of the
administrative surface.

This service owns the ONE contract every admin list endpoint shares
(`sdd/administracion-operativa-fest/admin-surface` §4.1):

| Param       | Default | Rule                                                       |
|-------------|---------|------------------------------------------------------------|
| `page`      | 1       | 1-based; values below 1 are clamped to 1                   |
| `page_size` | 25      | max 100; values ABOVE the max are CLAMPED, never an error  |
| `q`         | —       | free text over the DOCUMENTED fields of the resource; the    |
|             |         | term is trimmed and capped at 120 characters                |
| `ordering`  | per     | SERVER-SIDE WHITELIST; format `field` / `-field`; an       |
|             | resource| unknown value is rejected with 422 `INVALID_REQUEST`        |

The ordering whitelist is the important one: the client never sends an ORM
expression. It sends a PUBLIC field name and the server maps it to the
authorized expression. An unknown name raises `InvalidOrderingError` — the
raw client text is NEVER interpolated into a queryset.

Sync by contract (`contract/django-app-architecture-contract.md` §4.3): no
`async def`, no ORM access, no `transaction.atomic`.
"""
from collections.abc import Mapping

from modules.administracion.domain.exceptions import InvalidOrderingError
from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)


class AdminPaginacionService:
    """Canonical pagination, search and ordering rules for the admin area."""

    PAGE_POR_DEFECTO = 1
    PAGE_SIZE_POR_DEFECTO = 25
    PAGE_SIZE_MAXIMO = 100
    Q_MAXIMO = 120

    def normalizar_page(self, page: int | None) -> int:
        """Return a 1-based page number (values below 1 are clamped to 1)."""
        if page is None:
            return self.PAGE_POR_DEFECTO
        try:
            value = int(page)
        except (TypeError, ValueError):
            return self.PAGE_POR_DEFECTO
        return max(value, 1)

    def normalizar_page_size(self, page_size: int | None) -> int:
        """Return the page size, clamped to [1, PAGE_SIZE_MAXIMO].

        A value ABOVE the maximum is clamped, NOT rejected: the contract says
        "max 100; values above the max are clamped (not an error)".
        """
        if page_size is None:
            return self.PAGE_SIZE_POR_DEFECTO
        try:
            value = int(page_size)
        except (TypeError, ValueError):
            return self.PAGE_SIZE_POR_DEFECTO
        return min(max(value, 1), self.PAGE_SIZE_MAXIMO)

    def normalizar_q(self, q: str | None) -> str | None:
        """Return the normalized free-text term, or None when there is none.

        The term is whitespace-collapsed and capped at `Q_MAXIMO` characters:
        an unbounded term is an unbounded scan over indexed PII columns.
        """
        if q is None:
            return None
        limpio = " ".join(str(q).split())
        if not limpio:
            return None
        return limpio[: self.Q_MAXIMO]

    def resolver_ordering(
        self,
        ordering: str | None,
        permitidos: Mapping[str, str],
        default: str,
    ) -> str:
        """Translate a public ordering field into the authorized ORM expression.

        Args:
            ordering: the raw client value (`field` or `-field`), or None.
            permitidos: whitelist mapping PUBLIC field name -> ORM expression.
            default: the ordering expression used when the client asks for
                nothing.

        Returns:
            The ORM ordering expression, ready for `QuerySet.order_by(...)`.

        Raises:
            InvalidOrderingError: when the requested field is not whitelisted.
        """
        if ordering is None or not str(ordering).strip():
            return default

        crudo = str(ordering).strip()
        descendente = crudo.startswith("-")
        campo = crudo[1:] if descendente else crudo

        if campo not in permitidos:
            raise InvalidOrderingError()

        expresion = permitidos[campo]
        return f"-{expresion}" if descendente else expresion

    def construir_paginacion(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        q: str | None = None,
        ordering: str | None = None,
        permitidos: Mapping[str, str],
        default_ordering: str,
    ) -> AdminPaginacionParams:
        """Apply every rule at once and return the normalized parameters."""
        page_normalizada = self.normalizar_page(page)
        page_size_normalizado = self.normalizar_page_size(page_size)

        return AdminPaginacionParams(
            page=page_normalizada,
            page_size=page_size_normalizado,
            offset=(page_normalizada - 1) * page_size_normalizado,
            q=self.normalizar_q(q),
            ordering=self.resolver_ordering(
                ordering, permitidos, default_ordering
            ),
        )


__all__ = ["AdminPaginacionService"]
