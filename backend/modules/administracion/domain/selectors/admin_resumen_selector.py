"""
AdminResumenSelector — aggregate read queries of the operational overview.

Read-only by construction: no method in this selector writes. Every metric is
computed HERE, on the server, so the frontend never re-derives a count, a
balance or an eligibility (`contract/api-wrapper-presenter-contract.md` §7).

The selector reads the OWNING modules' models through their `domain/models`
re-exports (`modules.salesianos_fest`, `modules.commerce`, `modules.pagos`):
the admin module never imports another module's `presentation/` layer
(`contract/api-wrapper-presenter-contract.md` §1) and never re-implements a
business rule.

Invariants honoured by these queries:

- `Inscripcion.estado` is ADMINISTRATIVE and never reflects the payment; the
  commercial state lives in the `pagos` block.
- Paid capacity comes ONLY from `PAGADA` purchases
  (`CompraInscripcion.cantidad`), never from the registration state.
- One paid cup authorises a person in every contracted discipline, so
  `personas` and `participaciones` are two different numbers.
- The query count is CONSTANT with respect to the number of rows: every
  aggregate is computed with `values().annotate()`, never with a Python loop
  over a queryset.
"""
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.pagos.domain.constants import OrdenPagoStatus
from modules.salesianos_fest.domain.constants import (
    AutorizacionFiestaChoices,
    EstadoAcreditacionChoices,
    EstadoAsignacionCupoChoices,
    EstadoEquipoChoices,
    EstadoInscripcionPersonaChoices,
    EstadoParticipacionChoices,
)
from modules.salesianos_fest.domain.models import (
    AcreditacionEvento,
    AsignacionCupo,
    CompraInscripcion,
    Equipo,
    Inscripcion,
    InscripcionPersona,
    Participacion,
)


class AdminResumenSelector:
    """Aggregate read queries scoped to the active event."""

    DIAS_RECIENTES = 7

    # ── Inscripciones ────────────────────────────────────────────────────────

    def contar_inscripciones(self, evento_id: str) -> dict:
        """Return the administrative counters of the registrations.

        Returns:
            `{"total", "por_estado", "creadas_ultimos_7_dias"}`.

        `por_estado` only carries the states that actually exist; the caller
        completes the vocabulary with the eight known states (a missing state
        means zero, never "unknown").
        """
        qs = Inscripcion.objects.filter(evento_id=evento_id)

        por_estado = {
            fila["estado"]: fila["cantidad"]
            for fila in qs.values("estado").annotate(cantidad=Count("id"))
        }

        corte = timezone.now() - timedelta(days=self.DIAS_RECIENTES)

        return {
            "total": sum(por_estado.values()),
            "por_estado": por_estado,
            "creadas_ultimos_7_dias": qs.filter(created_at__gte=corte).count(),
        }

    # ── Pagos ───────────────────────────────────────────────────────────────

    def contar_compras(self, evento_id: str) -> dict:
        """Return the commercial counters of the purchases of the event.

        The event scope travels through `compra_inscripcion.inscripcion.evento`:
        `commerce.Compra` is generic and has no event of its own.

        Returns:
            `{"compras_total", "compras_pagadas", "compras_pendientes",
            "compras_canceladas", "monto_pagado", "monto_pendiente",
            "ordenes_vencidas", "compras_pagadas_sin_liquidar"}`.
        """
        qs = Compra.objects.filter(
            compra_inscripcion__inscripcion__evento_id=evento_id
        )

        por_estado = {
            fila["estado"]: {"total": fila["cantidad"], "monto": fila["monto"] or 0}
            for fila in qs.values("estado").annotate(
                cantidad=Count("id"),
                monto=Sum("total"),
            )
        }

        ordenes_vencidas = qs.filter(
            orden_pago__estado=OrdenPagoStatus.VENCIDA
        ).count()

        # Settlement gap: the order was paid but the purchase was never
        # settled (the case `reconciliar_pagos` fixes).
        pagadas_sin_liquidar = qs.filter(
            estado=EstadoCompraChoices.PENDIENTE,
            orden_pago__estado=OrdenPagoStatus.PAGADA,
        ).count()

        return {
            "compras_total": sum(v["total"] for v in por_estado.values()),
            "compras_pagadas": por_estado.get(
                EstadoCompraChoices.PAGADA, {"total": 0}
            )["total"],
            "compras_pendientes": por_estado.get(
                EstadoCompraChoices.PENDIENTE, {"total": 0}
            )["total"],
            "compras_canceladas": por_estado.get(
                EstadoCompraChoices.CANCELADA, {"total": 0}
            )["total"],
            "monto_pagado": por_estado.get(
                EstadoCompraChoices.PAGADA, {"monto": 0}
            )["monto"],
            "monto_pendiente": por_estado.get(
                EstadoCompraChoices.PENDIENTE, {"monto": 0}
            )["monto"],
            "ordenes_vencidas": ordenes_vencidas,
            "compras_pagadas_sin_liquidar": pagadas_sin_liquidar,
        }

    # ── Cupos ───────────────────────────────────────────────────────────────

    def contar_cupos(self, evento_id: str) -> dict:
        """Return the capacity counters of the event.

        The capacity rules are the ones of
        `AsignacionCoreService.calcular_saldo_inscripcion()`:

        - `contratado`  = sum of `cantidad` over the purchases that are not
          CANCELADA,
        - `pagado`      = sum of `cantidad` over the PAGADA purchases,
        - `asignado_activo` = ACTIVA assignments funded by PAGADA purchases,
        - `disponible_pagado` = `pagado - asignado_activo` (never negative).

        `inscripciones_con_capacidad_exhaustada` counts the inscriptions that
        HAVE paid capacity and already assigned all of it.
        """
        base = CompraInscripcion.objects.filter(inscripcion__evento_id=evento_id)

        pagados_por_inscripcion = {
            fila["inscripcion_id"]: fila["capacidad"]
            for fila in base.filter(compra__estado=EstadoCompraChoices.PAGADA)
            .values("inscripcion_id")
            .annotate(capacidad=Sum("cantidad"))
        }

        contratados_por_inscripcion = {
            fila["inscripcion_id"]: fila["capacidad"]
            for fila in base.exclude(compra__estado=EstadoCompraChoices.CANCELADA)
            .values("inscripcion_id")
            .annotate(capacidad=Sum("cantidad"))
        }

        asignados_por_inscripcion = {
            fila["inscripcion_id"]: fila["cantidad"]
            for fila in AsignacionCupo.objects.filter(
                inscripcion__evento_id=evento_id,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
                compra__estado=EstadoCompraChoices.PAGADA,
            )
            .values("inscripcion_id")
            .annotate(cantidad=Count("id"))
        }

        pagado = sum(pagados_por_inscripcion.values())
        asignado_activo = sum(asignados_por_inscripcion.values())

        agotadas = sum(
            1
            for inscripcion_id, capacidad in pagados_por_inscripcion.items()
            if capacidad > 0
            and capacidad - asignados_por_inscripcion.get(inscripcion_id, 0) <= 0
        )

        return {
            "contratado": sum(contratados_por_inscripcion.values()),
            "pagado": pagado,
            "asignado_activo": asignado_activo,
            "disponible_pagado": max(0, pagado - asignado_activo),
            "inscripciones_con_capacidad_exhaustada": agotadas,
        }

    # ── Equipos ─────────────────────────────────────────────────────────────

    def contar_equipos(self, evento_id: str) -> dict:
        """Return the team counters of the event.

        Only ACTIVE teams are counted: a cancelled team is not part of the
        operation. A team is COMPLETE when its ACTIVE participations reach the
        `min_jugadores` of its discipline (the roster rule of the domain).
        """
        equipos = (
            Equipo.objects.filter(
                inscripcion__evento_id=evento_id,
                estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
            )
            .select_related("disciplina")
            .annotate(
                jugadores=Count(
                    "participaciones",
                    filter=Q(participaciones__estado=EstadoParticipacionChoices.ACTIVA),
                )
            )
        )

        total = 0
        completos = 0
        por_disciplina: dict[str, dict] = {}

        for equipo in equipos:
            total += 1

            minimo = equipo.disciplina.min_jugadores or 0
            if equipo.jugadores >= minimo:
                completos += 1

            clave = str(equipo.disciplina_id)
            if clave not in por_disciplina:
                por_disciplina[clave] = {
                    "disciplina_id": clave,
                    "sigla": equipo.disciplina.sigla,
                    "nombre": equipo.disciplina.nombre,
                    "total": 0,
                }
            por_disciplina[clave]["total"] += 1

        return {
            "total": total,
            "completos": completos,
            "incompletos": total - completos,
            "por_disciplina": list(por_disciplina.values()),
        }

    # ── Participantes ───────────────────────────────────────────────────────

    def contar_participantes(self, evento_id: str) -> dict:
        """Return the participant counters of the event.

        `personas_distintas` counts ACTIVE `InscripcionPersona` rows, while
        `participaciones_activas` counts ACTIVE `Participacion` rows: one paid
        cup authorises a person in EVERY contracted discipline, so the two
        numbers are reported separately and never merged.

        `en_pool` = registered people without any ACTIVE participation.
        `sin_cupo_activo` = registered people without an ACTIVE cup assignment.
        """
        base = InscripcionPersona.objects.filter(
            inscripcion__evento_id=evento_id,
            estado=EstadoInscripcionPersonaChoices.ACTIVO,
        )

        personas_distintas = base.values("persona_id").distinct().count()

        participaciones_activas = Participacion.objects.filter(
            evento_id=evento_id,
            estado=EstadoParticipacionChoices.ACTIVA,
        ).count()

        en_pool = base.exclude(
            participaciones__estado=EstadoParticipacionChoices.ACTIVA
        ).count()

        sin_cupo_activo = base.exclude(
            asignaciones_cupo__estado=EstadoAsignacionCupoChoices.ACTIVA
        ).count()

        return {
            "personas_distintas": personas_distintas,
            "participaciones_activas": participaciones_activas,
            "en_pool": en_pool,
            "sin_cupo_activo": sin_cupo_activo,
        }

    # ── Acreditaciones ──────────────────────────────────────────────────────

    def contar_acreditaciones(self, evento_id: str) -> dict:
        """Return the accreditation counters of the event.

        `con_acceso_fiesta` counts the EFFECTIVE fiesta access, honouring the
        precedence of the domain: `estado=REVOCADA` or `habilitado=False`
        blocks regardless of `acceso_fiesta`
        (`modules.salesianos_fest.domain.models.AcreditacionEvento`).
        """
        base = AcreditacionEvento.objects.filter(evento_id=evento_id)

        por_estado = {
            fila["estado"]: fila["cantidad"]
            for fila in base.values("estado").annotate(cantidad=Count("id"))
        }

        con_acceso_fiesta = (
            base.filter(acceso_fiesta=True)
            .exclude(estado=EstadoAcreditacionChoices.REVOCADA)
            .filter(Q(habilitado=True) | Q(habilitado__isnull=True))
            .count()
        )

        bloqueadas_por_admin = base.filter(
            autorizacion_fiesta=AutorizacionFiestaChoices.BLOQUEADA
        ).count()

        return {
            "total": sum(por_estado.values()),
            "por_estado": por_estado,
            "con_acceso_fiesta": con_acceso_fiesta,
            "bloqueadas_por_admin": bloqueadas_por_admin,
        }


__all__ = ["AdminResumenSelector"]
