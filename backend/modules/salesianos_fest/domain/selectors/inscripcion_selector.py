"""InscripcionSelector — read-only queries for inscripciones."""
from typing import Optional

from datetime import datetime
from typing import Optional

from ..models import Inscripcion, InscripcionPersona, Participacion, Equipo
from ..results.inscripcion_results import (
    InscripcionResult,
    InscripcionDetailResult,
    EquipoResult,
    InscripcionPersonaResult,
    ParticipacionResult,
    CompraResult,
    OrdenPagoResult,
    PoolEntryResult,
    DisciplinaAsignadaResult,
    ElegibleResult,
    ElegiblesEquipoResult,
)
from ..constants import (
    EstadoParticipacionChoices,
    EstadoAsignacionCupoChoices,
    EstadoPoolChoices,
    EstadoInscripcionPersonaChoices,
    MOTIVO_ESPERANDO_PAGO,
    MOTIVO_SIN_CAPACIDAD,
    MOTIVO_CUPO_POR_ASIGNAR,
    MOTIVO_YA_EN_DISIPLINA,
    MOTIVO_GENERO_NO_COMPATIBLE,
)
from ..validators import es_genero_compatible_con_modalidad


def _estado_pool_de_entrada(
    has_cup: bool,
    pagados: int,
    disponibles_pagados: int,
) -> tuple[str, str | None]:
    """Derive the pool eligibility state and its UI-safe blocked reason.

    Pure function — no ORM access, no HTTP knowledge.

    The distinction that matters for the UI: "waiting for a payment" is only
    true when the inscription has NO paid capacity at all. When the payment
    already exists (paid capacity available or exhausted) the person is NOT
    waiting for a payment, and the UI must never say so.

    Args:
        has_cup: whether the participant already holds an ACTIVA paid cup.
        pagados: total paid capacity of the inscription.
        disponibles_pagados: paid capacity still free.

    Returns:
        (estado_pool, motivo_bloqueo) — `motivo_bloqueo` is None when eligible.
    """
    if has_cup:
        return EstadoPoolChoices.LISTO, None

    if disponibles_pagados > 0:
        # The payment exists and there is free capacity, but this participant
        # still has no right: the assignment is pending (repairable state).
        return EstadoPoolChoices.CUPO_POR_ASIGNAR, MOTIVO_CUPO_POR_ASIGNAR

    if pagados > 0:
        # The paid capacity is exhausted — the responsible must expand it.
        return EstadoPoolChoices.SIN_CAPACIDAD, MOTIVO_SIN_CAPACIDAD

    # No paid capacity at all: the person waits for the payment.
    return EstadoPoolChoices.ESPERANDO_PAGO, MOTIVO_ESPERANDO_PAGO


class InscripcionSelector:
    """Queries for Inscripcion entities."""

    @staticmethod
    def get_by_id(inscripcion_id: str) -> Optional[InscripcionResult]:
        """Return an inscripcion by ID or None."""
        try:
            ins = Inscripcion.objects.select_related(
                "evento", "responsable", "paquete", "promocion",
                "fusion_promocion", "delegado",
            ).get(id=inscripcion_id)
            return InscripcionResult(
                id=str(ins.id),
                evento_id=str(ins.evento_id),
                evento_nombre=ins.evento.nombre,
                responsable_id=str(ins.responsable_id),
                responsable_nombre=f"{ins.responsable.nombres} {ins.responsable.apellidos}",
                paquete_id=str(ins.paquete_id),
                paquete_nombre=ins.paquete.nombre,
                promocion_id=str(ins.promocion_id),
                promocion_nombre=ins.promocion.nombre,
                fusion_promocion_id=str(ins.fusion_promocion_id) if ins.fusion_promocion_id else None,
                delegado_id=str(ins.delegado_id) if ins.delegado_id else None,
                estado=ins.estado,
                observacion=ins.observacion,
                created_at=ins.created_at,
            )
        except Inscripcion.DoesNotExist:
            return None

    @staticmethod
    def get_by_id_with_details(inscripcion_id: str) -> Optional[InscripcionDetailResult]:
        """Return an inscripcion with equipos, personas and FEST compras populated.

        Loads:
        - Equipos with disciplina (including min_jugadores), categoria, participaciones
        - Personas (InscripcionPersona)
        - FEST compras via CompraInscripcion -> Compra -> OrdenPago
        - AsignacionCupo of the inscripcion (to count the paid rights already
          consumed) so the presenter can derive `disponible_pagado` without ORM

        NO derived state is calculated here (estado_roster, resumen_equipos,
        resumen_pago) — only raw data for the presenter to transform.
        Uses select_related/prefetch_related to avoid N+1 queries.
        """
        try:
            ins = Inscripcion.objects.select_related(
                "evento", "responsable", "paquete", "promocion",
                "fusion_promocion", "delegado",
            ).prefetch_related(
                "equipos__disciplina",
                "equipos__categoria",
                "equipos__participaciones__inscripcion_persona__persona",
                "inscripcion_personas__persona",
                "compras_inscripcion__compra__orden_pago",
                "asignaciones_cupo",
            ).get(id=inscripcion_id)

            equipos = []
            for eq in ins.equipos.all():
                participaciones = [
                    ParticipacionResult(
                        id=str(p.id),
                        inscripcion_persona_id=str(p.inscripcion_persona_id),
                        equipo_id=str(p.equipo_id),
                        equipo_nombre=p.equipo.nombre,
                        evento_id=str(p.evento_id),
                        disciplina_id=str(p.disciplina_id),
                        disciplina_nombre=p.disciplina.nombre,
                        disciplina_sigla=p.disciplina.sigla,
                        persona_id=str(p.persona_id),
                        persona_nombre=f"{p.inscripcion_persona.persona.nombres} {p.inscripcion_persona.persona.apellidos}",
                        persona_nombres=p.inscripcion_persona.persona.nombres,
                        persona_apellidos=p.inscripcion_persona.persona.apellidos,
                        persona_numero_documento=p.inscripcion_persona.persona.numero_documento,
                        rol=p.rol,
                        talla_camiseta=p.talla_camiseta,
                        notas=p.notas,
                        estado=p.estado,
                        created_at=p.created_at,
                    )
                    for p in eq.participaciones.all()
                ]
                equipos.append(EquipoResult(
                    id=str(eq.id),
                    inscripcion_id=str(eq.inscripcion_id),
                    disciplina_id=str(eq.disciplina_id),
                    disciplina_nombre=eq.disciplina.nombre,
                    disciplina_sigla=eq.disciplina.sigla,
                    min_jugadores=eq.disciplina.min_jugadores,  # Loaded via prefetch
                    categoria_id=str(eq.categoria_id) if eq.categoria_id else None,
                    categoria_nombre=eq.categoria.nombre if eq.categoria_id else None,
                    nombre=eq.nombre,
                    estado=eq.estado,
                    created_at=eq.created_at,
                    participaciones=participaciones,
                ))

            personas = [
                InscripcionPersonaResult(
                    id=str(ip.id),
                    inscripcion_id=str(ip.inscripcion_id),
                    persona_id=str(ip.persona_id),
                    persona_nombre=f"{ip.persona.nombres} {ip.persona.apellidos}",
                    persona_nombres=ip.persona.nombres,
                    persona_apellidos=ip.persona.apellidos,
                    persona_numero_documento=ip.persona.numero_documento,
                    estado=ip.estado,
                    created_at=ip.created_at,
                )
                for ip in ins.inscripcion_personas.all()
            ]

            # Load FEST compras via CompraInscripcion
            compras = []
            for ci in ins.compras_inscripcion.all():
                compra = ci.compra
                orden_pago_result = None
                if compra.orden_pago:
                    orden_pago_result = OrdenPagoResult(
                        id=str(compra.orden_pago.id),
                        numero=compra.orden_pago.numero,
                        estado=compra.orden_pago.estado,
                        pagada_en=compra.orden_pago.pagada_en,
                    )
                compras.append(CompraResult(
                    id=str(compra.id),
                    tipo=ci.tipo,
                    cantidad=ci.cantidad,
                    precio_unitario=ci.precio_unitario,
                    total=ci.total,
                    estado=compra.estado,
                    orden_pago=orden_pago_result,
                ))

            # Paid rights already consumed: ACTIVA AsignacionCupo funded by one
            # of this inscripcion's PAGADA compras. The set of PAGADA compra ids
            # is the same one used by `AsignacionCoreService.calcular_saldo_inscripcion`,
            # so `disponible_pagado` and `disponibles_pagados` cannot diverge.
            compras_pagadas_ids = {
                compra.id for compra in compras if compra.estado == "PAGADA"
            }
            asignados_pagados = sum(
                1
                for asignacion in ins.asignaciones_cupo.all()
                if asignacion.estado == EstadoAsignacionCupoChoices.ACTIVA
                and str(asignacion.compra_id) in compras_pagadas_ids
            )

            return InscripcionDetailResult(
                id=str(ins.id),
                evento_id=str(ins.evento_id),
                evento_nombre=ins.evento.nombre,
                responsable_id=str(ins.responsable_id),
                responsable_nombre=f"{ins.responsable.nombres} {ins.responsable.apellidos}",
                paquete_id=str(ins.paquete_id),
                paquete_nombre=ins.paquete.nombre,
                promocion_id=str(ins.promocion_id),
                promocion_nombre=ins.promocion.nombre,
                fusion_promocion_id=str(ins.fusion_promocion_id) if ins.fusion_promocion_id else None,
                delegado_id=str(ins.delegado_id) if ins.delegado_id else None,
                delegado_nombre=f"{ins.delegado.nombres} {ins.delegado.apellidos}" if ins.delegado_id else None,
                estado=ins.estado,
                observacion=ins.observacion,
                created_at=ins.created_at,
                equipos=equipos,
                personas=personas,
                compras=compras,
                asignados_pagados=asignados_pagados,
            )
        except Inscripcion.DoesNotExist:
            return None

    @staticmethod
    def get_by_evento(evento_id: str) -> list[InscripcionResult]:
        """Return all inscripciones for an evento."""
        qs = Inscripcion.objects.select_related(
            "evento", "responsable", "paquete", "promocion",
        ).filter(evento_id=evento_id).order_by("-created_at")
        return [
            InscripcionResult(
                id=str(ins.id),
                evento_id=str(ins.evento_id),
                evento_nombre=ins.evento.nombre,
                responsable_id=str(ins.responsable_id),
                responsable_nombre=f"{ins.responsable.nombres} {ins.responsable.apellidos}",
                paquete_id=str(ins.paquete_id),
                paquete_nombre=ins.paquete.nombre,
                promocion_id=str(ins.promocion_id),
                promocion_nombre=ins.promocion.nombre,
                fusion_promocion_id=str(ins.fusion_promocion_id) if ins.fusion_promocion_id else None,
                delegado_id=str(ins.delegado_id) if ins.delegado_id else None,
                estado=ins.estado,
                observacion=ins.observacion,
                created_at=ins.created_at,
            )
            for ins in qs
        ]

    @staticmethod
    def get_by_responsable(responsable_id: str) -> list[InscripcionResult]:
        """Return all inscripciones for a responsable (authenticated user)."""
        qs = Inscripcion.objects.select_related(
            "evento", "responsable", "paquete", "promocion",
        ).filter(responsable_id=responsable_id).order_by("-created_at")
        return [
            InscripcionResult(
                id=str(ins.id),
                evento_id=str(ins.evento_id),
                evento_nombre=ins.evento.nombre,
                responsable_id=str(ins.responsable_id),
                responsable_nombre=f"{ins.responsable.nombres} {ins.responsable.apellidos}",
                paquete_id=str(ins.paquete_id),
                paquete_nombre=ins.paquete.nombre,
                promocion_id=str(ins.promocion_id),
                promocion_nombre=ins.promocion.nombre,
                fusion_promocion_id=str(ins.fusion_promocion_id) if ins.fusion_promocion_id else None,
                delegado_id=str(ins.delegado_id) if ins.delegado_id else None,
                estado=ins.estado,
                observacion=ins.observacion,
                created_at=ins.created_at,
            )
            for ins in qs
        ]

    @staticmethod
    def get_pool(inscripcion_id: str) -> list[PoolEntryResult]:
        """Return pre-registered participants (InscripcionPersona without active Participacion).

        Pool members are thoseInscripcionPersona records linked to the inscripcion
        that have NO active Participacion (estado=A) — they are waiting in the pool
        and cannot be assigned to an equipo without an active AsignacionCupo.

        Exposes only UI-safe details. No payment metadata (compra data) is included.
        Eligibility to join a team is determined by the presence of an ACTIVA
        AsignacionCupo linked to this inscripcion_persona.

        Uses prefetch_related to avoid N+1 queries when building PoolEntryResult list.
        """
        # Fetch pool members: InscripcionPersona with no active Participacion in any equipo
        pool_ips = (
            InscripcionPersona.objects
            .filter(inscripcion_id=inscripcion_id, estado="A")
            .select_related("persona")
            .prefetch_related("asignaciones_cupo")
        )

        # Also prefetch active participaciones to exclude them
        active_participaciones = Participacion.objects.filter(
            inscripcion_persona__inscripcion_id=inscripcion_id,
            estado=EstadoParticipacionChoices.ACTIVA,
        ).values_list("inscripcion_persona_id", flat=True)
        active_ip_ids = set(str(ip_id) for ip_id in active_participaciones)

        # Remaining paid capacity of the inscripcion — it tells apart the
        # participants waiting for a payment from the ones over the capacity.
        from ..services.core.asignacion_service import AsignacionCoreService

        saldo = AsignacionCoreService().calcular_saldo_inscripcion(inscripcion_id)
        pagados = saldo["pagados"]
        disponibles_pagados = saldo["disponibles_pagados"]

        results = []
        for ip in pool_ips:
            if str(ip.id) in active_ip_ids:
                continue  # Has active Participacion — not in pool

            # Check if this InscripcionPersona has an active cup
            has_cup = ip.asignaciones_cupo.filter(
                estado=EstadoAsignacionCupoChoices.ACTIVA
            ).exists()

            estado_pool, motivo_bloqueo = _estado_pool_de_entrada(
                has_cup=has_cup,
                pagados=pagados,
                disponibles_pagados=disponibles_pagados,
            )

            results.append(PoolEntryResult(
                id=str(ip.id),
                persona_id=str(ip.persona_id),
                persona_nombre=f"{ip.persona.nombres} {ip.persona.apellidos}",
                persona_nombres=ip.persona.nombres,
                persona_apellidos=ip.persona.apellidos,
                persona_numero_documento=ip.persona.numero_documento,
                estado=ip.estado,
                created_at=ip.created_at,
                tiene_cupo_activo=has_cup,
                estado_pool=estado_pool,
                motivo_bloqueo=motivo_bloqueo,
            ))

        return results

    @staticmethod
    def get_elegibles_equipo(
        inscripcion_id: str,
        equipo_id: str,
    ) -> ElegiblesEquipoResult:
        """Return the candidates of the participant selector for ONE team.

        Team-scoped read. It lists every ACTIVE `InscripcionPersona` of the
        inscription and, for each one:

        - the commercial eligibility (`tiene_cupo_activo`, `estado_pool`,
          `motivo_bloqueo`) — the very same typed discriminator the pool uses,
        - the disciplines where the person ALREADY plays
          (`disciplinas_asignadas`), and
        - the backend verdict for THIS team (`asignable` +
          `motivo_no_asignable`).

        One paid cup authorises the person in EVERY contracted discipline, so a
        person that already plays in another discipline is still a candidate
        here. R11 only forbids playing twice in the SAME discipline — exactly
        what `asignable=False` reports for the target discipline.

        The verdict also applies the discipline/gender compatibility rule: a
        person whose PERSISTED gender is not accepted by the modality of the
        target discipline is NOT assignable. The matrix is NOT re-derived
        here — the shared predicate decides it, and the selector only
        translates a rejection into the UI-safe reason.

        The UI never re-derives any of this: it renders the verdict it gets.

        Raises:
            EquipoNotFoundError: when the equipo does not belong to the
                inscripcion (or does not exist).
        """
        from ..exceptions import EquipoNotFoundError

        try:
            equipo = Equipo.objects.select_related("disciplina").get(
                id=equipo_id,
                inscripcion_id=inscripcion_id,
            )
        except Equipo.DoesNotExist:
            raise EquipoNotFoundError()

        # Active participaciones of the inscription, grouped by inscripcion_persona.
        # A person may appear in several disciplines — one cup, several teams.
        disciplinas_por_ip: dict[str, list[DisciplinaAsignadaResult]] = {}
        participaciones = (
            Participacion.objects
            .filter(
                inscripcion_persona__inscripcion_id=inscripcion_id,
                estado=EstadoParticipacionChoices.ACTIVA,
            )
            .select_related("disciplina", "equipo")
        )
        for p in participaciones:
            disciplinas_por_ip.setdefault(str(p.inscripcion_persona_id), []).append(
                DisciplinaAsignadaResult(
                    disciplina_id=str(p.disciplina_id),
                    disciplina_nombre=p.disciplina.nombre,
                    disciplina_sigla=p.disciplina.sigla,
                    equipo_id=str(p.equipo_id),
                    equipo_nombre=p.equipo.nombre,
                )
            )

        inscripcion_personas = (
            InscripcionPersona.objects
            .filter(
                inscripcion_id=inscripcion_id,
                estado=EstadoInscripcionPersonaChoices.ACTIVO,
            )
            .select_related("persona")
            .prefetch_related("asignaciones_cupo")
        )

        # Remaining paid capacity — it tells apart the participants waiting for
        # a payment from the ones over the capacity (same rule as the pool).
        from ..services.core.asignacion_service import AsignacionCoreService

        saldo = AsignacionCoreService().calcular_saldo_inscripcion(inscripcion_id)
        pagados = saldo["pagados"]
        disponibles_pagados = saldo["disponibles_pagados"]

        resultados = []
        for ip in inscripcion_personas:
            # The prefetched cache is used on purpose: no extra query per person.
            has_cup = any(
                asignacion.estado == EstadoAsignacionCupoChoices.ACTIVA
                for asignacion in ip.asignaciones_cupo.all()
            )

            estado_pool, motivo_bloqueo = _estado_pool_de_entrada(
                has_cup=has_cup,
                pagados=pagados,
                disponibles_pagados=disponibles_pagados,
            )

            disciplinas = disciplinas_por_ip.get(str(ip.id), [])
            ya_en_disciplina = any(
                disciplina.disciplina_id == str(equipo.disciplina_id)
                for disciplina in disciplinas
            )

            # Compatibility of the PERSISTED gender with the modality of the
            # target discipline. Both values come from the rows already loaded
            # by `select_related` — the check adds NO query. The matrix lives
            # in the shared predicate: this is the only place that decides it.
            genero_compatible = es_genero_compatible_con_modalidad(
                ip.persona.genero,
                equipo.disciplina.modalidad,
            )

            asignable = has_cup and not ya_en_disciplina and genero_compatible
            if asignable:
                motivo_no_asignable = None
            elif ya_en_disciplina:
                # R11 — the person already plays in this discipline.
                motivo_no_asignable = MOTIVO_YA_EN_DISIPLINA
            elif not has_cup:
                # The commercial block comes FIRST: without a paid cup the
                # person cannot be assigned at all, no matter the discipline.
                motivo_no_asignable = motivo_bloqueo
            else:
                # The modality of the discipline does not accept the persisted
                # gender — the very rule the write path enforces.
                motivo_no_asignable = MOTIVO_GENERO_NO_COMPATIBLE

            resultados.append(ElegibleResult(
                id=str(ip.id),
                persona_id=str(ip.persona_id),
                persona_nombre=f"{ip.persona.nombres} {ip.persona.apellidos}",
                persona_nombres=ip.persona.nombres,
                persona_apellidos=ip.persona.apellidos,
                persona_numero_documento=ip.persona.numero_documento,
                estado=ip.estado,
                created_at=ip.created_at,
                tiene_cupo_activo=has_cup,
                estado_pool=estado_pool,
                motivo_bloqueo=motivo_bloqueo,
                disciplinas_asignadas=disciplinas,
                ya_en_disciplina=ya_en_disciplina,
                asignable=asignable,
                motivo_no_asignable=motivo_no_asignable,
            ))

        return ElegiblesEquipoResult(
            inscripcion_id=str(inscripcion_id),
            equipo_id=str(equipo.id),
            equipo_nombre=equipo.nombre,
            disciplina_id=str(equipo.disciplina_id),
            disciplina_nombre=equipo.disciplina.nombre,
            disciplina_sigla=equipo.disciplina.sigla,
            elegibles=resultados,
        )
