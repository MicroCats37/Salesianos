"""
AdminOperacionService — the operational read surface of the administration
(A3–A14).

This service owns three things:

1. the VALIDATION of the filter values — a value outside the vocabulary of
   the domain is rejected with 422 `INVALID_REQUEST` instead of reaching the
   queryset,
2. the CANONICAL pagination parameters — every list shares the contract of
   `AdminPaginacionService` (page, page_size, q, server-side ordering
   whitelist),
3. the COMPOSITION of the blocks of the drilldowns — the detail of a
   registration is assembled here out of the selectors that own each block.

Sync by contract (`contract/django-app-architecture-contract.md` §4.3): no
`async def`, no `transaction.atomic`, no write path.
"""
import uuid
from datetime import date

from injector import inject

from modules.administracion.domain.exceptions import (
    AdminResourceNotFoundError,
    InvalidFilterError,
)
from modules.administracion.domain.results.admin_acreditacion_results import (
    AdminAccesoListItemResult,
    AdminAcreditacionDetalleResult,
    AdminAcreditacionListItemResult,
)
from modules.administracion.domain.results.admin_inscripcion_results import (
    AdminInscripcionDetalleResult,
    AdminInscripcionListItemResult,
    AdminParticipacionListItemResult,
    AdminParticipanteListItemResult,
)
from modules.administracion.domain.results.admin_listado_results import (
    AdminListadoResult,
)
from modules.administracion.domain.results.admin_pago_results import (
    AdminPagoDetalleResult,
    AdminPagoListItemResult,
)
from modules.administracion.domain.results.admin_usuario_results import (
    AdminUsuarioDetalleResult,
    AdminUsuarioListItemResult,
)
from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)
from modules.administracion.domain.selectors.admin_acreditacion_selector import (
    AdminAcreditacionSelector,
)
from modules.administracion.domain.selectors.admin_equipo_selector import (
    AdminEquipoSelector,
)
from modules.administracion.domain.selectors.admin_inscripcion_selector import (
    AdminInscripcionSelector,
)
from modules.administracion.domain.selectors.admin_pago_selector import (
    AdminPagoSelector,
)
from modules.administracion.domain.selectors.admin_participante_selector import (
    AdminParticipanteSelector,
)
from modules.administracion.domain.selectors.admin_usuario_selector import (
    AdminUsuarioSelector,
)
from modules.administracion.domain.services.core.admin_paginacion_service import (
    AdminPaginacionService,
)
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.eventos.domain.models import Evento
from modules.pagos.domain.constants import OrdenPagoStatus
from modules.salesianos_fest.domain.constants import (
    AutorizacionFiestaChoices,
    EstadoAcreditacionChoices,
    EstadoEquipoChoices,
    EstadoInscripcionChoices,
    EstadoParticipacionChoices,
    EstadoPoolChoices,
    ResultadoAccesoChoices,
    RolParticipanteChoices,
    TipoCompraChoices,
)

# ── Ordering whitelists ───────────────────────────────────────────────────────
#
# The client sends a PUBLIC field name; the server maps it to the authorized
# ORM expression. The raw client text is NEVER interpolated into a queryset
# (`AdminPaginacionService.resolver_ordering`).

ORDERING_INSCRIPCIONES = {
    "created_at": "created_at",
    "estado": "estado",
    "responsable": "responsable__nombres",
    "paquete": "paquete__nombre",
}
DEFAULT_ORDERING_INSCRIPCIONES = "-created_at"

ORDERING_PAGOS = {
    "created_at": "created_at",
    "total": "total",
    "cantidad": "cantidad_linea",
    "estado_compra": "estado",
    "estado_orden": "orden_pago__estado",
    "pagada_en": "orden_pago__pagada_en",
}
DEFAULT_ORDERING_PAGOS = "-created_at"

ORDERING_EQUIPOS = {
    "created_at": "created_at",
    "nombre": "nombre",
    "disciplina": "disciplina__sigla",
    "estado": "estado",
}
DEFAULT_ORDERING_EQUIPOS = "-created_at"

ORDERING_PARTICIPANTES = {
    "created_at": "created_at",
    "persona": "persona__nombres",
    "estado": "estado",
}
DEFAULT_ORDERING_PARTICIPANTES = "-created_at"

ORDERING_PARTICIPACIONES = {
    "created_at": "created_at",
    "persona": "persona__nombres",
    "equipo": "equipo__nombre",
    "disciplina": "disciplina__sigla",
    "rol": "rol",
    "estado": "estado",
}
DEFAULT_ORDERING_PARTICIPACIONES = "-created_at"

ORDERING_ACREDITACIONES = {
    "persona": "persona__nombres",
    "estado": "estado",
    "autorizacion_fiesta": "autorizacion_fiesta",
}
DEFAULT_ORDERING_ACREDITACIONES = "persona__nombres"

ORDERING_ACCESOS = {
    "fecha_hora": "fecha_hora",
    "resultado": "resultado",
    "punto_acceso": "punto_acceso",
}
DEFAULT_ORDERING_ACCESOS = "-fecha_hora"

ORDERING_USUARIOS = {
    "created_at": "created_at",
    "username": "username",
    "nombres": "persona_fk__nombres",
    "last_login": "last_login",
}
DEFAULT_ORDERING_USUARIOS = "-created_at"

# ── Filter vocabularies ───────────────────────────────────────────────────────

ESTADO_USUARIO_ACTIVO = "activo"
ESTADO_USUARIO_INACTIVO = "inactivo"
ROSTER_COMPLETO = "COMPLETO"
ROSTER_INCOMPLETO = "INCOMPLETO"


def _valores(choices) -> frozenset[str]:
    """Return the values of a domain vocabulary."""
    return frozenset(valor for valor, _etiqueta in choices.choices)


#: The commercial kinds a purchase row can carry in the administrative
#: payments table: the two SPORTS kinds (INICIAL / AMPLIACION) plus the
#: independent PASS batch (PASE).
TIPOS_COMPRA_ADMIN = frozenset(
    (*_valores(TipoCompraChoices), "PASE")
)


class AdminOperacionService:
    """The operational read surface of the administration area."""

    @inject
    def __init__(
        self,
        paginacion_service: AdminPaginacionService,
        inscripcion_selector: AdminInscripcionSelector,
        pago_selector: AdminPagoSelector,
        equipo_selector: AdminEquipoSelector,
        participante_selector: AdminParticipanteSelector,
        acreditacion_selector: AdminAcreditacionSelector,
        usuario_selector: AdminUsuarioSelector,
    ):
        self.paginacion_service = paginacion_service
        self.inscripcion_selector = inscripcion_selector
        self.pago_selector = pago_selector
        self.equipo_selector = equipo_selector
        self.participante_selector = participante_selector
        self.acreditacion_selector = acreditacion_selector
        self.usuario_selector = usuario_selector

    # ── A3 / A4 — Registrations ────────────────────────────────────────────

    def listar_inscripciones(
        self,
        evento: Evento,
        *,
        page: int | None = None,
        page_size: int | None = None,
        q: str | None = None,
        ordering: str | None = None,
        estado: str | None = None,
        paquete_id: str | None = None,
        promocion_id: str | None = None,
        responsable_persona_id: str | None = None,
    ) -> AdminListadoResult[AdminInscripcionListItemResult]:
        """Return the page of registrations of the active event."""
        params = self._paginar(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            permitidos=ORDERING_INSCRIPCIONES,
            default_ordering=DEFAULT_ORDERING_INSCRIPCIONES,
        )

        items, total = self.inscripcion_selector.listar(
            str(evento.id),
            estado=self._validar_enum(
                estado, _valores(EstadoInscripcionChoices), "estado"
            ),
            paquete_id=self._validar_uuid(paquete_id, "paquete_id"),
            promocion_id=self._validar_uuid(promocion_id, "promocion_id"),
            responsable_persona_id=self._validar_uuid(
                responsable_persona_id, "responsable_persona_id"
            ),
            q=params.q,
            params=params,
        )

        return AdminListadoResult(items=items, total=total, params=params)

    def obtener_inscripcion_detalle(
        self,
        evento: Evento,
        inscripcion_id: str,
    ) -> AdminInscripcionDetalleResult:
        """Return the drilldown of one registration of the active event."""
        inscripcion_id = self._validar_uuid_recurso(inscripcion_id, "Inscripción")

        detalle = self.inscripcion_selector.obtener_detalle(
            str(evento.id), inscripcion_id
        )

        return detalle.model_copy(
            update={
                "compras": self.pago_selector.listar_compras_de_inscripcion(
                    inscripcion_id
                ),
                "participantes": (
                    self.participante_selector.listar_por_inscripcion(inscripcion_id)
                ),
            }
        )

    # ── A5 / A6 — Payments ─────────────────────────────────────────────────

    def listar_pagos(
        self,
        evento: Evento,
        *,
        page: int | None = None,
        page_size: int | None = None,
        q: str | None = None,
        ordering: str | None = None,
        estado_compra: str | None = None,
        estado_orden: str | None = None,
        tipo: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
    ) -> AdminListadoResult[AdminPagoListItemResult]:
        """Return the page of purchases of the active event."""
        params = self._paginar(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            permitidos=ORDERING_PAGOS,
            default_ordering=DEFAULT_ORDERING_PAGOS,
        )

        items, total = self.pago_selector.listar(
            str(evento.id),
            estado_compra=self._validar_enum(
                estado_compra, _valores(EstadoCompraChoices), "estado_compra"
            ),
            estado_orden=self._validar_enum(
                estado_orden, _valores(OrdenPagoStatus), "estado_orden"
            ),
            tipo=self._validar_enum(tipo, TIPOS_COMPRA_ADMIN, "tipo"),
            desde=self._validar_fecha(desde, "desde"),
            hasta=self._validar_fecha(hasta, "hasta"),
            q=params.q,
            params=params,
        )

        return AdminListadoResult(items=items, total=total, params=params)

    def obtener_pago_detalle(
        self,
        evento: Evento,
        orden_pago_id: str,
    ) -> AdminPagoDetalleResult:
        """Return the drilldown of one payment order of the active event."""
        orden_pago_id = self._validar_uuid_recurso(orden_pago_id, "Orden de pago")

        return self.pago_selector.obtener_detalle(str(evento.id), orden_pago_id)

    # ── A7 — Teams ─────────────────────────────────────────────────────────

    def listar_equipos(
        self,
        evento: Evento,
        *,
        page: int | None = None,
        page_size: int | None = None,
        q: str | None = None,
        ordering: str | None = None,
        inscripcion_id: str | None = None,
        disciplina_id: str | None = None,
        estado: str | None = None,
        roster: str | None = None,
    ) -> AdminListadoResult:
        """Return the page of teams of the active event."""
        params = self._paginar(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            permitidos=ORDERING_EQUIPOS,
            default_ordering=DEFAULT_ORDERING_EQUIPOS,
        )

        items, total = self.equipo_selector.listar(
            str(evento.id),
            inscripcion_id=self._validar_uuid(inscripcion_id, "inscripcion_id"),
            disciplina_id=self._validar_uuid(disciplina_id, "disciplina_id"),
            estado=self._validar_enum(
                estado, _valores(EstadoEquipoChoices), "estado"
            ),
            roster=self._validar_enum(
                roster,
                frozenset({ROSTER_COMPLETO, ROSTER_INCOMPLETO}),
                "roster",
            ),
            q=params.q,
            params=params,
        )

        return AdminListadoResult(items=items, total=total, params=params)

    # ── A8 / A9 — Participants and participations ──────────────────────────

    def listar_participantes(
        self,
        evento: Evento,
        *,
        page: int | None = None,
        page_size: int | None = None,
        q: str | None = None,
        ordering: str | None = None,
        estado_pool: str | None = None,
        disciplina_id: str | None = None,
        con_cupo: str | None = None,
    ) -> AdminListadoResult[AdminParticipanteListItemResult]:
        """Return the page of registered people of the active event."""
        params = self._paginar(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            permitidos=ORDERING_PARTICIPANTES,
            default_ordering=DEFAULT_ORDERING_PARTICIPANTES,
        )

        items, total = self.participante_selector.listar(
            str(evento.id),
            estado_pool=self._validar_enum(
                estado_pool, _valores(EstadoPoolChoices), "estado_pool"
            ),
            disciplina_id=self._validar_uuid(disciplina_id, "disciplina_id"),
            con_cupo=self._validar_bool(con_cupo, "con_cupo"),
            q=params.q,
            params=params,
        )

        return AdminListadoResult(items=items, total=total, params=params)

    def listar_participaciones(
        self,
        evento: Evento,
        *,
        page: int | None = None,
        page_size: int | None = None,
        q: str | None = None,
        ordering: str | None = None,
        disciplina_id: str | None = None,
        rol: str | None = None,
        estado: str | None = None,
        inscripcion_id: str | None = None,
    ) -> AdminListadoResult[AdminParticipacionListItemResult]:
        """Return the page of roster rows of the active event."""
        params = self._paginar(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            permitidos=ORDERING_PARTICIPACIONES,
            default_ordering=DEFAULT_ORDERING_PARTICIPACIONES,
        )

        items, total = self.participante_selector.listar_participaciones(
            str(evento.id),
            disciplina_id=self._validar_uuid(disciplina_id, "disciplina_id"),
            rol=self._validar_enum(
                rol, _valores(RolParticipanteChoices), "rol"
            ),
            estado=self._validar_enum(
                estado, _valores(EstadoParticipacionChoices), "estado"
            ),
            inscripcion_id=self._validar_uuid(inscripcion_id, "inscripcion_id"),
            q=params.q,
            params=params,
        )

        return AdminListadoResult(items=items, total=total, params=params)

    # ── A10 / A11 / A12 — Accreditations and accesses ──────────────────────

    def listar_acreditaciones(
        self,
        evento: Evento,
        *,
        page: int | None = None,
        page_size: int | None = None,
        q: str | None = None,
        ordering: str | None = None,
        estado: str | None = None,
        autorizacion_fiesta: str | None = None,
        acceso_fiesta: str | None = None,
    ) -> AdminListadoResult[AdminAcreditacionListItemResult]:
        """Return the page of accreditations of the active event."""
        params = self._paginar(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            permitidos=ORDERING_ACREDITACIONES,
            default_ordering=DEFAULT_ORDERING_ACREDITACIONES,
        )

        items, total = self.acreditacion_selector.listar(
            str(evento.id),
            estado=self._validar_enum(
                estado, _valores(EstadoAcreditacionChoices), "estado"
            ),
            autorizacion_fiesta=self._validar_enum(
                autorizacion_fiesta,
                _valores(AutorizacionFiestaChoices),
                "autorizacion_fiesta",
            ),
            acceso_fiesta=self._validar_bool(acceso_fiesta, "acceso_fiesta"),
            q=params.q,
            params=params,
        )

        return AdminListadoResult(items=items, total=total, params=params)

    def obtener_acreditacion_detalle(
        self,
        evento: Evento,
        acreditacion_id: str,
    ) -> AdminAcreditacionDetalleResult:
        """Return the drilldown of one accreditation of the active event."""
        acreditacion_id = self._validar_uuid_recurso(
            acreditacion_id, "Acreditación"
        )

        return self.acreditacion_selector.obtener_detalle(
            str(evento.id), acreditacion_id
        )

    def listar_accesos(
        self,
        evento: Evento,
        *,
        page: int | None = None,
        page_size: int | None = None,
        q: str | None = None,
        ordering: str | None = None,
        resultado: str | None = None,
        punto_acceso: str | None = None,
        desde: str | None = None,
        hasta: str | None = None,
    ) -> AdminListadoResult[AdminAccesoListItemResult]:
        """Return the page of access records of the active event."""
        params = self._paginar(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            permitidos=ORDERING_ACCESOS,
            default_ordering=DEFAULT_ORDERING_ACCESOS,
        )

        items, total = self.acreditacion_selector.listar_accesos(
            str(evento.id),
            resultado=self._validar_enum(
                resultado, _valores(ResultadoAccesoChoices), "resultado"
            ),
            punto_acceso=punto_acceso,
            desde=self._validar_fecha(desde, "desde"),
            hasta=self._validar_fecha(hasta, "hasta"),
            q=params.q,
            params=params,
        )

        return AdminListadoResult(items=items, total=total, params=params)

    # ── A13 / A14 — Accounts ───────────────────────────────────────────────

    def listar_usuarios(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        q: str | None = None,
        ordering: str | None = None,
        estado: str | None = None,
        es_admin: str | None = None,
    ) -> AdminListadoResult[AdminUsuarioListItemResult]:
        """Return the page of accounts.

        The accounts are NOT scoped to an event: an account is a global
        identity. The registrations shown in the detail (A14) ARE scoped to
        the active event.
        """
        params = self._paginar(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            permitidos=ORDERING_USUARIOS,
            default_ordering=DEFAULT_ORDERING_USUARIOS,
        )

        activo = self._validar_estado_usuario(estado)

        items, total = self.usuario_selector.listar(
            activo=activo,
            es_admin=self._validar_bool(es_admin, "es_admin"),
            q=params.q,
            params=params,
        )

        return AdminListadoResult(items=items, total=total, params=params)

    def obtener_usuario_detalle(
        self,
        evento: Evento,
        usuario_id: str,
    ) -> AdminUsuarioDetalleResult:
        """Return the drilldown of one account."""
        usuario_id = self._validar_uuid_recurso(usuario_id, "Usuario")

        return self.usuario_selector.obtener_detalle(str(evento.id), usuario_id)

    # ── Internals ──────────────────────────────────────────────────────────

    def _paginar(
        self,
        *,
        page: int | None,
        page_size: int | None,
        q: str | None,
        ordering: str | None,
        permitidos: dict[str, str],
        default_ordering: str,
    ) -> AdminPaginacionParams:
        """Build the canonical pagination parameters of a list."""
        return self.paginacion_service.construir_paginacion(
            page=page,
            page_size=page_size,
            q=q,
            ordering=ordering,
            permitidos=permitidos,
            default_ordering=default_ordering,
        )

    @staticmethod
    def _validar_enum(valor: str | None, permitidos, campo: str) -> str | None:
        """Return the filter value when it belongs to the vocabulary.

        Raises:
            InvalidFilterError: when the value is outside the vocabulary.
        """
        if valor is None:
            return None

        limpio = str(valor).strip()
        if not limpio:
            return None

        if limpio not in permitidos:
            raise InvalidFilterError()

        return limpio

    @staticmethod
    def _validar_uuid(valor: str | None, campo: str) -> str | None:
        """Return the normalized UUID of a filter value.

        A well formed id that does NOT exist is not an error: it is a filter
        that matches no row, and the list answers empty.

        Raises:
            InvalidFilterError: when the value is not a UUID.
        """
        if valor is None:
            return None

        limpio = str(valor).strip()
        if not limpio:
            return None

        try:
            return str(uuid.UUID(limpio))
        except (ValueError, AttributeError, TypeError):
            raise InvalidFilterError()

    @staticmethod
    def _validar_uuid_recurso(valor: str, recurso: str) -> str:
        """Return the normalized UUID of a RESOURCE id.

        A malformed id and an unknown id are answered the same way: 404
        `RESOURCE_NOT_FOUND`. The surface never confirms the existence of a
        resource, and never leaks the reason of the rejection.

        Raises:
            AdminResourceNotFoundError: when the id is not a UUID.
        """
        try:
            return str(uuid.UUID(str(valor).strip()))
        except (ValueError, AttributeError, TypeError):
            raise AdminResourceNotFoundError(recurso)

    @staticmethod
    def _validar_bool(valor: str | None, campo: str) -> bool | None:
        """Return the boolean value of a filter.

        Raises:
            InvalidFilterError: when the value is not a boolean.
        """
        if valor is None:
            return None

        limpio = str(valor).strip().lower()
        if not limpio:
            return None

        if limpio in {"true", "1", "yes", "si", "sí"}:
            return True

        if limpio in {"false", "0", "no"}:
            return False

        raise InvalidFilterError()

    @staticmethod
    def _validar_fecha(valor: str | None, campo: str) -> date | None:
        """Return the date of an ISO date filter.

        Raises:
            InvalidFilterError: when the value is not an ISO date.
        """
        if valor is None:
            return None

        limpio = str(valor).strip()
        if not limpio:
            return None

        try:
            return date.fromisoformat(limpio)
        except ValueError:
            raise InvalidFilterError()

    @staticmethod
    def _validar_estado_usuario(valor: str | None) -> bool | None:
        """Return the `is_active` filter of the account list.

        The vocabulary is the administrative one: `activo` / `inactivo`.

        Raises:
            InvalidFilterError: when the value is outside the vocabulary.
        """
        if valor is None:
            return None

        limpio = str(valor).strip().lower()
        if not limpio:
            return None

        if limpio == ESTADO_USUARIO_ACTIVO:
            return True

        if limpio == ESTADO_USUARIO_INACTIVO:
            return False

        raise InvalidFilterError()


__all__ = ["AdminOperacionService"]
