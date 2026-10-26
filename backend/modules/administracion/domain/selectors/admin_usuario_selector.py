"""
AdminUsuarioSelector — read queries of the accounts (A13, A14).

The account surface REUSES the selector of the OWNING module
(`modules.usuarios.UsuarioSelector`): the admin module never re-implements
the admin rule (`is_staff OR is_superuser`) nor the free-text search over the
accounts (`contract/api-wrapper-presenter-contract.md` §1).

The surface is READ-ONLY and never carries a credential: no password, no
hash, no token, and no `is_superuser` — the break-glass tier is neither
surfaced nor manageable from here.

Read-only by construction: no method in this selector writes.
"""
from injector import inject

from modules.administracion.domain.exceptions import AdminResourceNotFoundError
from modules.administracion.domain.results.admin_usuario_results import (
    AdminUsuarioDetalleResult,
    AdminUsuarioInscripcionResult,
    AdminUsuarioListItemResult,
)
from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)
from modules.salesianos_fest.domain.models import Inscripcion
from modules.usuarios.domain.selectors import UsuarioSelector


class AdminUsuarioSelector:
    """Read-only queries for the accounts."""

    @inject
    def __init__(self, usuario_selector: UsuarioSelector):
        self.usuario_selector = usuario_selector

    # ── List (A13) ─────────────────────────────────────────────────────────

    def listar(
        self,
        *,
        activo: bool | None = None,
        es_admin: bool | None = None,
        q: str | None = None,
        params: AdminPaginacionParams,
    ) -> tuple[list[AdminUsuarioListItemResult], int]:
        """Return the page of accounts and the total of matching rows.

        Args:
            activo: only the active (or only the inactive) accounts.
            es_admin: only the administrators (or only the regular ones),
                using the project rule `is_staff OR is_superuser`.
            q: free text over username, email, document and civil name.
            params: the normalized pagination parameters.

        Returns:
            `(items, total)`.
        """
        qs = self.usuario_selector.listar(activo=activo, es_admin=es_admin, q=q)
        qs = qs.order_by(params.ordering)

        total = qs.count()
        filas = list(qs[params.offset: params.offset + params.page_size])

        return [self._map(fila) for fila in filas], total

    # ── Detail (A14) ───────────────────────────────────────────────────────

    def obtener_detalle(
        self,
        evento_id: str,
        usuario_id: str,
    ) -> AdminUsuarioDetalleResult:
        """Return the drilldown of one account.

        The registrations of the block are the ones of the ACTIVE event: the
        surface never mixes editions.

        Raises:
            AdminResourceNotFoundError: when the account does not exist.
        """
        usuario = self.usuario_selector.obtener_por_id(usuario_id)

        if usuario is None:
            raise AdminResourceNotFoundError("Usuario")

        persona = usuario.persona_fk

        inscripciones = (
            Inscripcion.objects
            .filter(responsable_id=persona.id, evento_id=evento_id)
            .order_by("-created_at")
        )

        return AdminUsuarioDetalleResult(
            **self._map(usuario).model_dump(),
            personas=[
                AdminUsuarioInscripcionResult(
                    inscripcion_id=str(inscripcion.id),
                    estado=inscripcion.estado,
                    created_at=inscripcion.created_at,
                )
                for inscripcion in inscripciones
            ],
        )

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _map(usuario) -> AdminUsuarioListItemResult:
        """Map an account into its result DTO (never a credential)."""
        persona = usuario.persona_fk

        return AdminUsuarioListItemResult(
            id=str(usuario.id),
            username=usuario.username,
            email=usuario.email,
            nombres=persona.nombres,
            apellidos=persona.apellidos,
            persona_id=str(persona.id),
            persona_documento=persona.numero_documento,
            es_admin=bool(usuario.is_staff or usuario.is_superuser),
            is_active=bool(usuario.is_active),
            last_login=usuario.last_login,
            created_at=usuario.created_at,
        )


__all__ = ["AdminUsuarioSelector"]
