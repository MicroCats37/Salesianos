"""
AdminInscripcionSelector — read queries of the registrations (A3, A4).

The selector owns the QUERY composition and every DERIVED number of the
registrations; the presenter only transforms the result objects it returns
(`contract/api-wrapper-presenter-contract.md` §3).

Invariants honoured here:

- the EVENT scope is applied by the caller (`evento_id`): the client never
  sends `evento_id`,
- `equipos_total` counts only ACTIVE teams — a cancelled team is not part of
  the operation,
- `personas` counts the ACTIVE registered people and `participaciones` the
  ACTIVE roster rows: one paid cup authorises a person in EVERY contracted
  discipline, so the two numbers are never merged,
- the paid capacity comes ONLY from the `PAGADA` purchases
  (`CompraInscripcion.cantidad`), never from the administrative state of the
  registration,
- the query count is CONSTANT with respect to the number of rows: every
  counter is an aggregate over the ids of the requested page, never a Python
  loop over a queryset.

Read-only by construction: no method in this selector writes.
"""
from django.db.models import Count, Q, Sum
from injector import inject

from modules.administracion.domain.exceptions import AdminResourceNotFoundError
from modules.administracion.domain.results.admin_inscripcion_results import (
    AdminAceptacionListItemResult,
    AdminAsignacionListItemResult,
    AdminEquipoDetalleResult,
    AdminEquipoListItemResult,
    AdminInscripcionDetalleResult,
    AdminInscripcionListItemResult,
    AdminSaldoResult,
)
from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.salesianos_fest.domain.constants import (
    EstadoAsignacionCupoChoices,
    EstadoEquipoChoices,
    EstadoInscripcionPersonaChoices,
    EstadoParticipacionChoices,
)
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    Equipo,
    Inscripcion,
    InscripcionPersona,
    Participacion,
)
from modules.salesianos_fest.domain.selectors.aceptacion_inscripcion_selector import (
    AceptacionInscripcionSelector,
)
from modules.salesianos_fest.domain.services.core.asignacion_service import (
    AsignacionCoreService,
)


def _nombre_completo(nombres: str, apellidos: str) -> str:
    """Return the display name of a person."""
    return f"{nombres} {apellidos}".strip()


def _referencia_corta(identificador) -> str:
    """Return a short display reference of an id.

    The administration surface shows the reference in dense tables; the full
    id is still available in the `id` field for the drilldowns.
    """
    return str(identificador)[:8].upper()


class AdminInscripcionSelector:
    """Read-only queries for the registrations of an event."""

    @inject
    def __init__(
        self,
        asignacion_service: AsignacionCoreService,
        aceptacion_selector: AceptacionInscripcionSelector,
    ):
        self.asignacion_service = asignacion_service
        self.aceptacion_selector = aceptacion_selector

    # ── List (A3) ──────────────────────────────────────────────────────────

    def listar(
        self,
        evento_id: str,
        *,
        estado: str | None = None,
        paquete_id: str | None = None,
        promocion_id: str | None = None,
        responsable_persona_id: str | None = None,
        q: str | None = None,
        params: AdminPaginacionParams,
    ) -> tuple[list[AdminInscripcionListItemResult], int]:
        """Return the page of registrations and the total of matching rows.

        Args:
            evento_id: the ACTIVE event (resolved server-side).
            estado: administrative state filter (the 8 known states).
            paquete_id: commercial package filter.
            promocion_id: promotion filter.
            responsable_persona_id: responsible person filter.
            q: free text over the responsible (name, document) and the package
                name — the DOCUMENTED fields of this resource only.
            params: the normalized pagination parameters.

        Returns:
            `(items, total)` — the rows of the requested page and the number
            of rows that match the filters.
        """
        qs = (
            Inscripcion.objects
            .filter(evento_id=evento_id)
            .select_related("evento", "responsable", "paquete", "promocion")
        )

        if estado:
            qs = qs.filter(estado=estado)

        if paquete_id:
            qs = qs.filter(paquete_id=paquete_id)

        if promocion_id:
            qs = qs.filter(promocion_id=promocion_id)

        if responsable_persona_id:
            qs = qs.filter(responsable_id=responsable_persona_id)

        if q:
            qs = qs.filter(
                Q(responsable__nombres__icontains=q)
                | Q(responsable__apellidos__icontains=q)
                | Q(responsable__numero_documento__icontains=q)
                | Q(paquete__nombre__icontains=q)
            )

        qs = qs.order_by(params.ordering)

        total = qs.count()
        filas = list(qs[params.offset: params.offset + params.page_size])

        return self._construir_items(filas), total

    # ── Detail (A4) ────────────────────────────────────────────────────────

    def obtener_detalle(
        self,
        evento_id: str,
        inscripcion_id: str,
    ) -> AdminInscripcionDetalleResult:
        """Return the drilldown of one registration.

        An id that does not exist AND an id that belongs to another edition
        are answered the SAME way: 404 `RESOURCE_NOT_FOUND`. The surface never
        confirms the existence of a resource outside its scope.

        Raises:
            AdminResourceNotFoundError: when the registration does not exist or
                belongs to another event.
        """
        inscripcion = (
            Inscripcion.objects
            .filter(id=inscripcion_id, evento_id=evento_id)
            .select_related(
                "evento",
                "responsable",
                "paquete",
                "promocion",
                "delegado",
            )
            .first()
        )

        if inscripcion is None:
            raise AdminResourceNotFoundError("Inscripción")

        items = self._construir_items([inscripcion])

        return AdminInscripcionDetalleResult(
            **items[0].model_dump(),
            delegado_nombre=(
                _nombre_completo(inscripcion.delegado.nombres, inscripcion.delegado.apellidos)
                if inscripcion.delegado
                else None
            ),
            observacion=inscripcion.observacion,
            fecha_limite_modificacion=inscripcion.evento.fecha_limite_modificacion,
            equipos=self._equipos_de_inscripcion(inscripcion),
            compras=[],
            asignaciones=self._asignaciones_de_inscripcion(inscripcion),
            aceptaciones=self._aceptaciones_de_inscripcion(inscripcion),
            saldo=self._saldo_de_inscripcion(inscripcion),
        )

    # ── Internals ──────────────────────────────────────────────────────────

    def _construir_items(
        self,
        filas: list[Inscripcion],
    ) -> list[AdminInscripcionListItemResult]:
        """Map the page rows into the list item result, with their counters."""
        if not filas:
            return []

        ids = [fila.id for fila in filas]
        equipos = self._equipos_por_inscripcion(ids)
        personas = self._personas_por_inscripcion(ids)
        participaciones = self._participaciones_por_inscripcion(ids)
        cupos = self._cupos_por_inscripcion(ids)

        items: list[AdminInscripcionListItemResult] = []
        for fila in filas:
            clave = str(fila.id)
            equipo = equipos.get(clave, {"total": 0, "completos": 0})
            cupo = cupos.get(
                clave,
                {"contratados": 0, "pagados": 0, "asignados": 0, "monto": 0.0},
            )

            items.append(
                AdminInscripcionListItemResult(
                    id=str(fila.id),
                    evento_nombre=fila.evento.nombre,
                    responsable_nombre=_nombre_completo(
                        fila.responsable.nombres, fila.responsable.apellidos
                    ),
                    responsable_documento=fila.responsable.numero_documento,
                    paquete_nombre=fila.paquete.nombre,
                    promocion_nombre=fila.promocion.nombre,
                    estado=fila.estado,
                    equipos_total=equipo["total"],
                    equipos_completos=equipo["completos"],
                    personas=personas.get(clave, 0),
                    participaciones=participaciones.get(clave, 0),
                    cupos_contratados=cupo["contratados"],
                    cupos_pagados=cupo["pagados"],
                    cupos_disponibles=max(0, cupo["pagados"] - cupo["asignados"]),
                    monto_pagado=cupo["monto"],
                    created_at=fila.created_at,
                )
            )

        return items

    def _equipos_por_inscripcion(self, inscripcion_ids: list) -> dict[str, dict]:
        """Return the team counters of every inscription of the page.

        A team is COMPLETE when its ACTIVE participations reach the
        `min_jugadores` of its discipline — the roster rule of the domain.
        """
        filas = (
            Equipo.objects
            .filter(
                inscripcion_id__in=inscripcion_ids,
                estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
            )
            .values("inscripcion_id", "id", "disciplina__min_jugadores")
            .annotate(
                jugadores=Count(
                    "participaciones",
                    filter=Q(participaciones__estado=EstadoParticipacionChoices.ACTIVA),
                )
            )
        )

        resultado: dict[str, dict] = {}
        for fila in filas:
            clave = str(fila["inscripcion_id"])
            bloque = resultado.setdefault(clave, {"total": 0, "completos": 0})
            bloque["total"] += 1
            minimo = fila["disciplina__min_jugadores"] or 0
            if (fila["jugadores"] or 0) >= minimo:
                bloque["completos"] += 1

        return resultado

    def _personas_por_inscripcion(self, inscripcion_ids: list) -> dict[str, int]:
        """Return the ACTIVE registered people of every inscription."""
        filas = (
            InscripcionPersona.objects
            .filter(
                inscripcion_id__in=inscripcion_ids,
                estado=EstadoInscripcionPersonaChoices.ACTIVO,
            )
            .values("inscripcion_id")
            .annotate(cantidad=Count("id"))
        )
        return {str(fila["inscripcion_id"]): fila["cantidad"] for fila in filas}

    def _participaciones_por_inscripcion(self, inscripcion_ids: list) -> dict[str, int]:
        """Return the ACTIVE roster rows of every inscription."""
        filas = (
            Participacion.objects
            .filter(
                inscripcion_persona__inscripcion_id__in=inscripcion_ids,
                estado=EstadoParticipacionChoices.ACTIVA,
            )
            .values("inscripcion_persona__inscripcion_id")
            .annotate(cantidad=Count("id"))
        )
        return {
            str(fila["inscripcion_persona__inscripcion_id"]): fila["cantidad"]
            for fila in filas
        }

    def _cupos_por_inscripcion(self, inscripcion_ids: list) -> dict[str, dict]:
        """Return the cup counters of every inscription.

        - `contratados` — sum of `cantidad` over the purchases that are not
          CANCELADA,
        - `pagados` — sum of `cantidad` over the PAGADA purchases,
        - `asignados` — ACTIVA assignments funded by PAGADA purchases,
        - `monto` — sum of the purchase totals of the PAGADA purchases.
        """
        contratados = {
            str(fila["inscripcion_id"]): fila["cantidad"]
            for fila in CompraInscripcion.objects
            .filter(inscripcion_id__in=inscripcion_ids)
            .exclude(compra__estado=EstadoCompraChoices.CANCELADA)
            .values("inscripcion_id")
            .annotate(cantidad=Sum("cantidad"))
        }

        pagados = {
            str(fila["inscripcion_id"]): fila
            for fila in CompraInscripcion.objects
            .filter(
                inscripcion_id__in=inscripcion_ids,
                compra__estado=EstadoCompraChoices.PAGADA,
            )
            .values("inscripcion_id")
            .annotate(cantidad=Sum("cantidad"), monto=Sum("compra__total"))
        }

        asignados = {
            str(fila["inscripcion_id"]): fila["cantidad"]
            for fila in AsignacionCupo.objects
            .filter(
                inscripcion_id__in=inscripcion_ids,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
                compra__estado=EstadoCompraChoices.PAGADA,
            )
            .values("inscripcion_id")
            .annotate(cantidad=Count("id"))
        }

        resultado: dict[str, dict] = {}
        for clave in {*contratados, *pagados, *asignados}:
            bloque_pagado = pagados.get(clave, {})
            resultado[clave] = {
                "contratados": contratados.get(clave, 0),
                "pagados": bloque_pagado.get("cantidad") or 0,
                "asignados": asignados.get(clave, 0),
                "monto": float(bloque_pagado.get("monto") or 0),
            }

        return resultado

    def _equipos_de_inscripcion(self, inscripcion: Inscripcion) -> list[AdminEquipoDetalleResult]:
        """Return the teams of one registration with their roster rows."""
        equipos = list(
            Equipo.objects
            .filter(inscripcion_id=inscripcion.id)
            .select_related("disciplina", "categoria")
            .order_by("nombre")
        )

        roster = self._roster_por_equipo([equipo.id for equipo in equipos])

        participaciones = (
            Participacion.objects
            .filter(equipo_id__in=[equipo.id for equipo in equipos])
            .select_related("persona", "disciplina")
            .order_by("persona__nombres", "persona__apellidos")
        )

        por_equipo: dict[str, list] = {}
        for participacion in participaciones:
            por_equipo.setdefault(str(participacion.equipo_id), []).append(
                {
                    "id": str(participacion.id),
                    "inscripcion_persona_id": str(participacion.inscripcion_persona_id),
                    "persona_nombre": _nombre_completo(
                        participacion.persona.nombres, participacion.persona.apellidos
                    ),
                    "persona_documento": participacion.persona.numero_documento,
                    "equipo_nombre": participacion.equipo.nombre,
                    "disciplina_sigla": participacion.disciplina.sigla,
                    "inscripcion_id": str(inscripcion.id),
                    "rol": participacion.rol,
                    "talla_camiseta": participacion.talla_camiseta,
                    "estado": participacion.estado,
                    "created_at": participacion.created_at,
                }
            )

        resultado: list[AdminEquipoDetalleResult] = []
        for equipo in equipos:
            jugadores, minimo = roster.get(str(equipo.id), (0, equipo.disciplina.min_jugadores or 0))
            resultado.append(
                AdminEquipoDetalleResult(
                    id=str(equipo.id),
                    nombre=equipo.nombre,
                    disciplina_sigla=equipo.disciplina.sigla,
                    disciplina_nombre=equipo.disciplina.nombre,
                    categoria_nombre=equipo.categoria.nombre if equipo.categoria else None,
                    inscripcion_id=str(inscripcion.id),
                    inscripcion_ref=_referencia_corta(inscripcion.id),
                    estado=equipo.estado,
                    jugadores_registrados=jugadores,
                    minimo_deportivo=minimo,
                    faltantes=max(0, minimo - jugadores),
                    estado_roster=(
                        "COMPLETO" if jugadores >= minimo else "INCOMPLETO"
                    ),
                    created_at=equipo.created_at,
                    participaciones=por_equipo.get(str(equipo.id), []),
                )
            )

        return resultado

    def _roster_por_equipo(self, equipo_ids: list) -> dict[str, tuple[int, int]]:
        """Return `(jugadores, minimo)` of every team of the given ids."""
        if not equipo_ids:
            return {}

        filas = (
            Equipo.objects
            .filter(id__in=equipo_ids)
            .values("id", "disciplina__min_jugadores")
            .annotate(
                jugadores=Count(
                    "participaciones",
                    filter=Q(participaciones__estado=EstadoParticipacionChoices.ACTIVA),
                )
            )
        )

        return {
            str(fila["id"]): (
                fila["jugadores"] or 0,
                fila["disciplina__min_jugadores"] or 0,
            )
            for fila in filas
        }

    def _asignaciones_de_inscripcion(
        self,
        inscripcion: Inscripcion,
    ) -> list[AdminAsignacionListItemResult]:
        """Return the cup assignments of one registration."""
        filas = (
            AsignacionCupo.objects
            .filter(inscripcion_id=inscripcion.id)
            .select_related("inscripcion_persona__persona")
            .order_by("-created_at")
        )

        return [
            AdminAsignacionListItemResult(
                id=str(fila.id),
                persona_nombre=_nombre_completo(
                    fila.inscripcion_persona.persona.nombres,
                    fila.inscripcion_persona.persona.apellidos,
                ),
                estado=fila.estado,
                motivo=fila.motivo,
                liberada_en=fila.liberada_en,
                compra_id=str(fila.compra_id),
                created_at=fila.created_at,
            )
            for fila in filas
        ]

    def _aceptaciones_de_inscripcion(
        self,
        inscripcion: Inscripcion,
    ) -> list[AdminAceptacionListItemResult]:
        """Return the legal acceptances of one registration.

        The acceptances are read through the OWNING module's selector
        (`AceptacionInscripcionSelector`): the admin module never re-implements
        the acceptance rules.
        """
        filas = self.aceptacion_selector.listar_por_inscripcion(str(inscripcion.id))

        return [
            AdminAceptacionListItemResult(
                persona_id=str(fila.inscripcion_persona.persona_id),
                tipo_aceptacion=fila.tipo_aceptacion,
                documento_version=fila.documento_version,
                aceptado_en=fila.aceptado_en,
                medio=fila.medio,
            )
            for fila in filas
        ]

    def _saldo_de_inscripcion(self, inscripcion: Inscripcion) -> AdminSaldoResult:
        """Return the cup balance of one registration.

        The numbers are the ones of
        `AsignacionCoreService.calcular_saldo_inscripcion()`.
        """
        saldo = self.asignacion_service.calcular_saldo_inscripcion(str(inscripcion.id))

        return AdminSaldoResult(
            contratados=saldo["contratados"],
            pagados=saldo["pagados"],
            asignados_pagados=saldo["asignados_pagados"],
            disponibles_pagados=saldo["disponibles_pagados"],
        )


__all__ = ["AdminInscripcionSelector"]
