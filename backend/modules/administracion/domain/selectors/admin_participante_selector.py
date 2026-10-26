"""
AdminParticipanteSelector — read queries of the participants and the roster
rows (A8, A9).

The two surfaces are DIFFERENT things and are never merged
(`sdd/administracion-operativa-fest/admin-surface` §3):

- A8 (`participantes`) — the PEOPLE registered in an inscription. One paid
  cup authorises a person in EVERY contracted discipline, so a person may
  appear in several teams: `personas` and `participaciones` are two different
  numbers.
- A9 (`participaciones`) — the ROST ROWS: one person placed in one team of
  one discipline.

The pool state (`estado_pool`) is DERIVED, never persisted
(`modules.salesianos_fest.domain.constants.EstadoPoolChoices`):

| State              | Meaning                                                  |
|--------------------|----------------------------------------------------------|
| `LISTO`            | the person holds an ACTIVE paid cup                      |
| `ESPERANDO_PAGO`   | the registration has NO paid capacity at all             |
| `SIN_CAPACIDAD`    | the paid capacity is exhausted — an amplification is due |
| `CUPO_POR_ASIGNAR` | there IS free paid capacity, but the person has no cup   |

Read-only by construction: no method in this selector writes.
"""
from django.db.models import (
    Count,
    Exists,
    ExpressionWrapper,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from modules.administracion.domain.results.admin_inscripcion_results import (
    AdminParticipacionListItemResult,
    AdminParticipanteListItemResult,
)
from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.salesianos_fest.domain.constants import (
    MOTIVO_CUPO_POR_ASIGNAR,
    MOTIVO_ESPERANDO_PAGO,
    MOTIVO_SIN_CAPACIDAD,
    EstadoAsignacionCupoChoices,
    EstadoParticipacionChoices,
    EstadoPoolChoices,
)
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    InscripcionPersona,
    Participacion,
)


def _nombre_completo(nombres: str, apellidos: str) -> str:
    """Return the display name of a person."""
    return f"{nombres} {apellidos}".strip()


class AdminParticipanteSelector:
    """Read-only queries for the participants of an event."""

    # ── Participants (A8) ──────────────────────────────────────────────────

    def listar(
        self,
        evento_id: str,
        *,
        estado_pool: str | None = None,
        disciplina_id: str | None = None,
        con_cupo: bool | None = None,
        q: str | None = None,
        params: AdminPaginacionParams,
    ) -> tuple[list[AdminParticipanteListItemResult], int]:
        """Return the page of registered people and the total of matching rows.

        Args:
            evento_id: the ACTIVE event (resolved server-side).
            estado_pool: filter by the DERIVED pool state.
            disciplina_id: only the people with an ACTIVE participation in
                that discipline.
            con_cupo: only the people WITH (True) or WITHOUT (False) an
                ACTIVE cup assignment.
            q: free text over the person (name, document).
            params: the normalized pagination parameters.

        Returns:
            `(items, total)`.
        """
        qs = (
            InscripcionPersona.objects
            .filter(inscripcion__evento_id=evento_id)
            .select_related("inscripcion", "persona")
        )

        if disciplina_id:
            qs = qs.filter(
                participaciones__estado=EstadoParticipacionChoices.ACTIVA,
                participaciones__disciplina_id=disciplina_id,
            )

        if q:
            qs = qs.filter(
                Q(persona__nombres__icontains=q)
                | Q(persona__apellidos__icontains=q)
                | Q(persona__numero_documento__icontains=q)
            )

        qs = self._anotar_pool(qs)

        if con_cupo is True:
            qs = qs.filter(tiene_cupo_activo=True)
        elif con_cupo is False:
            qs = qs.filter(tiene_cupo_activo=False)

        if estado_pool:
            qs = self._filtrar_estado_pool(qs, estado_pool)

        total = qs.count()

        filas = list(
            qs.order_by(params.ordering)[params.offset: params.offset + params.page_size]
        )

        disciplinas = self._disciplinas_por_persona(
            [fila.id for fila in filas]
        )

        items: list[AdminParticipanteListItemResult] = []
        for fila in filas:
            estado, motivo = self._estado_pool(fila)
            items.append(
                AdminParticipanteListItemResult(
                    inscripcion_persona_id=str(fila.id),
                    persona_id=str(fila.persona_id),
                    persona_nombre=_nombre_completo(
                        fila.persona.nombres, fila.persona.apellidos
                    ),
                    persona_documento=fila.persona.numero_documento,
                    inscripcion_id=str(fila.inscripcion_id),
                    estado=fila.estado,
                    estado_pool=estado,
                    motivo_bloqueo=motivo,
                    tiene_cupo_activo=bool(fila.tiene_cupo_activo),
                    disciplinas=disciplinas.get(str(fila.id), []),
                    created_at=fila.created_at,
                )
            )

        return items, total

    def listar_por_inscripcion(
        self,
        inscripcion_id: str,
    ) -> list[AdminParticipanteListItemResult]:
        """Return the registered people of ONE registration (the block of A4)."""
        qs = self._anotar_pool(
            InscripcionPersona.objects
            .filter(inscripcion_id=inscripcion_id)
            .select_related("inscripcion", "persona")
        ).order_by("persona__nombres", "persona__apellidos")

        filas = list(qs)

        disciplinas = self._disciplinas_por_persona([fila.id for fila in filas])

        items: list[AdminParticipanteListItemResult] = []
        for fila in filas:
            estado, motivo = self._estado_pool(fila)
            items.append(
                AdminParticipanteListItemResult(
                    inscripcion_persona_id=str(fila.id),
                    persona_id=str(fila.persona_id),
                    persona_nombre=_nombre_completo(
                        fila.persona.nombres, fila.persona.apellidos
                    ),
                    persona_documento=fila.persona.numero_documento,
                    inscripcion_id=str(fila.inscripcion_id),
                    estado=fila.estado,
                    estado_pool=estado,
                    motivo_bloqueo=motivo,
                    tiene_cupo_activo=bool(fila.tiene_cupo_activo),
                    disciplinas=disciplinas.get(str(fila.id), []),
                    created_at=fila.created_at,
                )
            )

        return items

    # ── Participations (A9) ────────────────────────────────────────────────

    def listar_participaciones(
        self,
        evento_id: str,
        *,
        disciplina_id: str | None = None,
        rol: str | None = None,
        estado: str | None = None,
        inscripcion_id: str | None = None,
        q: str | None = None,
        params: AdminPaginacionParams,
    ) -> tuple[list[AdminParticipacionListItemResult], int]:
        """Return the page of roster rows and the total of matching rows.

        Args:
            evento_id: the ACTIVE event (resolved server-side).
            disciplina_id: filter by the discipline.
            rol: filter by the role (J / C / D).
            estado: filter by the participation state (A / R).
            inscripcion_id: filter by the registration that owns the roster.
            q: free text over the person and the team.
            params: the normalized pagination parameters.

        Returns:
            `(items, total)`.
        """
        qs = (
            Participacion.objects
            .filter(evento_id=evento_id)
            .select_related(
                "inscripcion_persona__persona",
                "inscripcion_persona__inscripcion",
                "equipo",
                "disciplina",
            )
        )

        if disciplina_id:
            qs = qs.filter(disciplina_id=disciplina_id)

        if rol:
            qs = qs.filter(rol=rol)

        if estado:
            qs = qs.filter(estado=estado)

        if inscripcion_id:
            qs = qs.filter(inscripcion_persona__inscripcion_id=inscripcion_id)

        if q:
            qs = qs.filter(
                Q(persona__nombres__icontains=q)
                | Q(persona__apellidos__icontains=q)
                | Q(persona__numero_documento__icontains=q)
                | Q(equipo__nombre__icontains=q)
            )

        qs = qs.order_by(params.ordering)

        total = qs.count()
        filas = list(qs[params.offset: params.offset + params.page_size])

        items: list[AdminParticipacionListItemResult] = []
        for fila in filas:
            items.append(
                AdminParticipacionListItemResult(
                    id=str(fila.id),
                    inscripcion_persona_id=str(fila.inscripcion_persona_id),
                    persona_nombre=_nombre_completo(
                        fila.persona.nombres, fila.persona.apellidos
                    ),
                    persona_documento=fila.persona.numero_documento,
                    equipo_nombre=fila.equipo.nombre,
                    disciplina_sigla=fila.disciplina.sigla,
                    inscripcion_id=str(fila.inscripcion_persona.inscripcion_id),
                    rol=fila.rol,
                    talla_camiseta=fila.talla_camiseta,
                    estado=fila.estado,
                    created_at=fila.created_at,
                )
            )

        return items, total

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _anotar_pool(qs):
        """Annotate a participant queryset with the pool derivations.

        - `tiene_cupo_activo` — the person holds an ACTIVE cup assignment,
        - `pagados` — the paid capacity of the registration,
        - `asignados` — the paid capacity already assigned,
        - `disponible` — the free paid capacity of the registration.
        """
        pagados = Coalesce(
            Subquery(
                CompraInscripcion.objects
                .filter(
                    inscripcion_id=OuterRef("inscripcion_id"),
                    compra__estado=EstadoCompraChoices.PAGADA,
                )
                .values("inscripcion_id")
                .annotate(capacidad=Sum("cantidad"))
                .values("capacidad"),
                output_field=IntegerField(),
            ),
            Value(0),
            output_field=IntegerField(),
        )

        asignados = Coalesce(
            Subquery(
                AsignacionCupo.objects
                .filter(
                    inscripcion_id=OuterRef("inscripcion_id"),
                    estado=EstadoAsignacionCupoChoices.ACTIVA,
                    compra__estado=EstadoCompraChoices.PAGADA,
                )
                .values("inscripcion_id")
                .annotate(cantidad=Count("id"))
                .values("cantidad"),
                output_field=IntegerField(),
            ),
            Value(0),
            output_field=IntegerField(),
        )

        return qs.annotate(
            tiene_cupo_activo=Exists(
                AsignacionCupo.objects.filter(
                    inscripcion_persona_id=OuterRef("pk"),
                    estado=EstadoAsignacionCupoChoices.ACTIVA,
                )
            ),
            pagados=pagados,
            asignados=asignados,
        ).annotate(
            disponible=ExpressionWrapper(
                F("pagados") - F("asignados"),
                output_field=IntegerField(),
            )
        )

    @staticmethod
    def _filtrar_estado_pool(qs, estado_pool: str):
        """Restrict a participant queryset to one DERIVED pool state.

        The state is computed in SQL (subqueries over the paid capacity of the
        registration), so the filter is applied BEFORE the pagination.
        """
        if estado_pool == EstadoPoolChoices.LISTO:
            return qs.filter(tiene_cupo_activo=True)

        sin_cupo = qs.filter(tiene_cupo_activo=False)

        if estado_pool == EstadoPoolChoices.ESPERANDO_PAGO:
            return sin_cupo.filter(pagados=0)

        if estado_pool == EstadoPoolChoices.SIN_CAPACIDAD:
            return sin_cupo.filter(pagados__gt=0, disponible__lte=0)

        return sin_cupo.filter(pagados__gt=0, disponible__gt=0)

    @staticmethod
    def _estado_pool(fila) -> tuple[str, str | None]:
        """Return the `(estado, motivo)` of one participant.

        The precedence is the one of `EstadoPoolChoices`: a person with an
        ACTIVE cup is READY, whatever the capacity of the registration.
        """
        if fila.tiene_cupo_activo:
            return EstadoPoolChoices.LISTO, None

        if not fila.pagados:
            return EstadoPoolChoices.ESPERANDO_PAGO, MOTIVO_ESPERANDO_PAGO

        if fila.disponible <= 0:
            return EstadoPoolChoices.SIN_CAPACIDAD, MOTIVO_SIN_CAPACIDAD

        return EstadoPoolChoices.CUPO_POR_ASIGNAR, MOTIVO_CUPO_POR_ASIGNAR

    @staticmethod
    def _disciplinas_por_persona(inscripcion_persona_ids: list) -> dict[str, list[str]]:
        """Return the siglas of the disciplines each person plays in."""
        if not inscripcion_persona_ids:
            return {}

        filas = (
            Participacion.objects
            .filter(
                inscripcion_persona_id__in=inscripcion_persona_ids,
                estado=EstadoParticipacionChoices.ACTIVA,
            )
            .values("inscripcion_persona_id", "disciplina__sigla")
            .order_by("inscripcion_persona_id", "disciplina__sigla")
        )

        resultado: dict[str, list[str]] = {}
        for fila in filas:
            siglas = resultado.setdefault(str(fila["inscripcion_persona_id"]), [])
            sigla = fila["disciplina__sigla"]
            if sigla not in siglas:
                siglas.append(sigla)

        return resultado


__all__ = ["AdminParticipanteSelector"]
