"""InscripcionPresenter — transforms domain results to HTTP schemas."""
from decimal import Decimal
from modules.salesianos_fest.domain.results.inscripcion_results import (
    InscripcionResult,
    InscripcionDetailResult,
    EquipoResult,
    InscripcionPersonaResult,
    ParticipacionResult,
    CompraResult,
    PoolEntryResult,
    ElegibleResult,
    ElegiblesEquipoResult,
)
from modules.salesianos_fest.presentation.schemas.inscripcion_schemas import (
    InscripcionOut,
    InscripcionDetailOut,
    EquipoOut,
    DisciplinaSummarySchema,
    CategoriaSummarySchema,
    PersonaSummarySchema,
    EquipoSummarySchema,
    EquipoDetailSchema,
    InscripcionPersonaSummarySchema,
    InscripcionPersonaOut,
    ParticipacionOut,
    PoolEntryOut,
    DisciplinaAsignadaOut,
    ElegibleOut,
    ElegiblesEquipoOut,
    # Phase 3: summary schemas
    ResumenEquiposSchema,
    ResumenPagoSchema,
    ResumenParticipantesSchema,
    CompraResumenSchema,
    OrdenPagoResumenSchema,
)


class InscripcionPresenter:
    """Transforms domain results to HTTP response schemas.

    Pure transformer — no DB access.
    """

    # ─── Inscripcion ─────────────────────────────────────────────────────────

    @staticmethod
    def present_inscripcion(result: InscripcionResult) -> InscripcionOut:
        """Transform InscripcionResult to InscripcionOut."""
        return InscripcionOut(
            id=result.id,
            evento_id=result.evento_id,
            evento_nombre=result.evento_nombre,
            responsable_id=result.responsable_id,
            responsable_nombre=result.responsable_nombre,
            paquete_id=result.paquete_id,
            paquete_nombre=result.paquete_nombre,
            promocion_id=result.promocion_id,
            promocion_nombre=result.promocion_nombre,
            fusion_promocion_id=result.fusion_promocion_id,
            delegado_id=result.delegado_id,
            estado=result.estado,
            observacion=result.observacion,
            created_at=result.created_at.isoformat(),
        )

    @staticmethod
    def present_inscripcion_detail(result: InscripcionDetailResult) -> InscripcionDetailOut:
        """Transform InscripcionDetailResult to InscripcionDetailOut.

        Phase 3: computes per-team roster state (estado_roster, jugadores_registrados,
        minimo_deportivo, faltantes), aggregate resumen_equipos, and aggregate
        resumen_pago from preloaded compra data — NO ORM calls.
        """

        # ── Per-team roster computation ──────────────────────────────────────────
        presented_equipos = []
        completos = 0
        incompletos = 0

        for eq in result.equipos:
            # Count ACTIVA participaciones only. The DB stores estado as a
            # single-char code ("A" = Activa, "R" = Retirada) per the
            # `EstadoParticipacionChoices` — NOT the verbose "ACTIVA" string.
            # Using the wrong literal here silently returns 0 for every team.
            activas = [p for p in eq.participaciones if p.estado == "A"]
            jugadores_registrados = len(activas)
            minimo = eq.min_jugadores or 0
            faltantes = max(0, minimo - jugadores_registrados)
            estado_roster = "COMPLETO" if jugadores_registrados >= minimo else "INCOMPLETO"

            if estado_roster == "COMPLETO":
                completos += 1
            else:
                incompletos += 1

            presented_equipos.append(
                EquipoDetailSchema(
                    id=eq.id,
                    nombre=eq.nombre,
                    estado=eq.estado,  # persisted EQUIPO_ACTIVO / EQUIPO_CANCELADO
                    estado_equipo=eq.estado,  # explicit alias preserved
                    estado_roster=estado_roster,
                    jugadores_registrados=jugadores_registrados,
                    minimo_deportivo=minimo,
                    faltantes=faltantes,
                    disciplina=DisciplinaSummarySchema(
                        id=eq.disciplina_id,
                        nombre=eq.disciplina_nombre,
                        sigla=eq.disciplina_sigla,
                    ),
                    categoria=CategoriaSummarySchema(
                        id=eq.categoria_id,
                        nombre=eq.categoria_nombre,
                    ) if eq.categoria_id else None,
                    participantes=[
                        ParticipacionOut(
                            id=p.id,
                            inscripcion_persona_id=p.inscripcion_persona_id,
                            equipo_id=p.equipo_id,
                            equipo_nombre=p.equipo_nombre,
                            evento_id=p.evento_id,
                            disciplina=DisciplinaSummarySchema(
                                id=p.disciplina_id,
                                nombre=p.disciplina_nombre,
                                sigla=p.disciplina_sigla,
                            ),
                            persona=PersonaSummarySchema(
                                id=p.persona_id,
                                nombre=p.persona_nombre,
                                nombres=p.persona_nombres,
                                apellidos=p.persona_apellidos,
                                numero_documento=p.persona_numero_documento,
                            ),
                            rol=p.rol,
                            talla_camiseta=p.talla_camiseta,
                            notas=p.notas,
                            estado=p.estado,
                            created_at=p.created_at.isoformat(),
                        )
                        for p in eq.participaciones
                    ],
                )
            )

        # ── Aggregate resumen_equipos ──────────────────────────────────────────
        resumen_equipos = ResumenEquiposSchema(
            total=len(result.equipos),
            completos=completos,
            incompletos=incompletos,
        )

        # ── Aggregate resumen_participantes ────────────────────────────────────
        # One paid cup authorises a person in EVERY contracted discipline, so the
        # roster rows and the distinct people are two different numbers. Only
        # the distinct people can be compared against the paid cupos.
        participaciones_activas = [
            p
            for eq in result.equipos
            for p in eq.participaciones
            if p.estado == "A"
        ]
        resumen_participantes = ResumenParticipantesSchema(
            participaciones=len(participaciones_activas),
            personas=len({p.inscripcion_persona_id for p in participaciones_activas}),
        )

        # ── Aggregate resumen_pago ──────────────────────────────────────────────
        compras_pendientes = 0
        compras_pagadas = 0
        compras_canceladas = 0
        total_contratado = 0  # sum of quantities of non-cancelled purchases
        total_pagado = Decimal("0")  # sum of monetary totals of PAGADA purchases
        total_pagado_cantidad = 0  # sum of quantities of PAGADA purchases

        presented_compras = []
        for compra in (result.compras or []):
            # Build nested orden_pago (no metadata)
            orden_pago_schema = None
            if compra.orden_pago:
                orden_pago_schema = OrdenPagoResumenSchema(
                    id=compra.orden_pago.id,
                    numero=compra.orden_pago.numero,
                    estado=compra.orden_pago.estado,
                    pagada_en=compra.orden_pago.pagada_en.isoformat()
                    if compra.orden_pago.pagada_en else None,
                )

            # Build purchase summary
            presented_compras.append(
                CompraResumenSchema(
                    id=compra.id,
                    tipo=compra.tipo,
                    cantidad=compra.cantidad,
                    precio_unitario=float(compra.precio_unitario),
                    total=float(compra.total),
                    estado=compra.estado,
                    orden_pago=orden_pago_schema,
                )
            )

            # Count by estado
            if compra.estado == "PENDIENTE":
                compras_pendientes += 1
                total_contratado += compra.cantidad
            elif compra.estado == "PAGADA":
                compras_pagadas += 1
                total_contratado += compra.cantidad
                total_pagado += Decimal(str(compra.total))
                total_pagado_cantidad += compra.cantidad
            elif compra.estado == "CANCELADA":
                compras_canceladas += 1
                # cancelled purchases don't count toward contracted total

        total_compras = len(result.compras or [])
        # disponible_pagado: paid slots that are still free.
        #
        # It is the paid capacity MINUS the paid rights already consumed
        # (ACTIVE AsignacionCupo funded by a PAGADA compra). The previous
        # formula subtracted the whole contracted total, which always included
        # the PENDIENTE purchases and therefore collapsed to 0 for every
        # inscription. This mirrors
        # `AsignacionCoreService.calcular_saldo_inscripcion().disponibles_pagados`,
        # so the detail summary and `GET /inscripciones/{id}/saldo` agree.
        disponible_pagado = max(0, total_pagado_cantidad - result.asignados_pagados)

        # Global payment state → UI message
        active_count = total_compras - compras_canceladas
        if active_count == 0:
            estado_mensaje = "Sin actividades de pago"
        elif compras_pagadas == active_count and compras_pendientes == 0:
            estado_mensaje = "Pago confirmado"
        elif compras_pagadas > 0 and compras_pendientes > 0:
            estado_mensaje = "Pago parcial"
        else:
            estado_mensaje = "Pago pendiente"

        resumen_pago = ResumenPagoSchema(
            total_compras=total_compras,
            total_contratado=total_contratado,
            total_pagado=float(total_pagado),
            total_pagado_cantidad=total_pagado_cantidad,
            compras_pendientes=compras_pendientes,
            compras_pagadas=compras_pagadas,
            compras_canceladas=compras_canceladas,
            disponible_pagado=disponible_pagado,
            estado_mensaje=estado_mensaje,
            compras=presented_compras,
        )

        # ── Assemble InscripcionDetailOut ──────────────────────────────────────
        return InscripcionDetailOut(
            id=result.id,
            evento_id=result.evento_id,
            evento_nombre=result.evento_nombre,
            responsable_id=result.responsable_id,
            responsable_nombre=result.responsable_nombre,
            paquete_id=result.paquete_id,
            paquete_nombre=result.paquete_nombre,
            promocion_id=result.promocion_id,
            promocion_nombre=result.promocion_nombre,
            fusion_promocion_id=result.fusion_promocion_id,
            delegado_id=result.delegado_id,
            delegado_nombre=result.delegado_nombre,
            estado=result.estado,
            observacion=result.observacion,
            created_at=result.created_at.isoformat(),
            equipos=presented_equipos,
            personas=[
                InscripcionPersonaSummarySchema(
                    id=ip.id,
                    persona=PersonaSummarySchema(
                        id=ip.persona_id,
                        nombre=ip.persona_nombre,
                        nombres=ip.persona_nombres,
                        apellidos=ip.persona_apellidos,
                        numero_documento=ip.persona_numero_documento,
                    ),
                    estado=ip.estado,
                )
                for ip in result.personas
            ],
            resumen_equipos=resumen_equipos,
            resumen_pago=resumen_pago,
            resumen_participantes=resumen_participantes,
        )

    # ─── Equipo ───────────────────────────────────────────────────────────────

    @staticmethod
    def present_equipo(result: EquipoResult) -> EquipoOut:
        """Transform EquipoResult to EquipoOut."""
        return EquipoOut(
            id=result.id,
            inscripcion_id=result.inscripcion_id,
            disciplina=DisciplinaSummarySchema(
                id=result.disciplina_id,
                nombre=result.disciplina_nombre,
                sigla=result.disciplina_sigla,
            ),
            categoria=CategoriaSummarySchema(
                id=result.categoria_id,
                nombre=result.categoria_nombre,
            ) if result.categoria_id else None,
            nombre=result.nombre,
            estado=result.estado,
            created_at=result.created_at.isoformat(),
        )

    @staticmethod
    def present_equipos(results: list[EquipoResult]) -> list[EquipoOut]:
        """Transform list of EquipoResult to list of EquipoOut."""
        return [InscripcionPresenter.present_equipo(r) for r in results]

    @staticmethod
    def present_inscripcion_persona(result: InscripcionPersonaResult) -> InscripcionPersonaOut:
        """Transform InscripcionPersonaResult to InscripcionPersonaOut."""
        return InscripcionPersonaOut(
            id=result.id,
            inscripcion_id=result.inscripcion_id,
            persona=PersonaSummarySchema(
                id=result.persona_id,
                nombre=result.persona_nombre,
                nombres=result.persona_nombres,
                apellidos=result.persona_apellidos,
                numero_documento=result.persona_numero_documento,
            ),
            estado=result.estado,
            created_at=result.created_at.isoformat(),
        )

    # ─── Participacion ───────────────────────────────────────────────────────

    @staticmethod
    def present_participacion(result: ParticipacionResult) -> ParticipacionOut:
        """Transform ParticipacionResult to ParticipacionOut."""
        return ParticipacionOut(
            id=result.id,
            inscripcion_persona_id=result.inscripcion_persona_id,
            equipo_id=result.equipo_id,
            equipo_nombre=result.equipo_nombre,
            evento_id=result.evento_id,
            disciplina=DisciplinaSummarySchema(
                id=result.disciplina_id,
                nombre=result.disciplina_nombre,
                sigla=result.disciplina_sigla,
            ),
            persona=PersonaSummarySchema(
                id=result.persona_id,
                nombre=result.persona_nombre,
                nombres=result.persona_nombres,
                apellidos=result.persona_apellidos,
                numero_documento=result.persona_numero_documento,
            ),
            rol=result.rol,
            talla_camiseta=result.talla_camiseta,
            notas=result.notas,
            estado=result.estado,
            created_at=result.created_at.isoformat(),
        )

    @staticmethod
    def present_participaciones(results: list[ParticipacionResult]) -> list[ParticipacionOut]:
        """Transform list of ParticipacionResult to list of ParticipacionOut."""
        return [InscripcionPresenter.present_participacion(r) for r in results]

    # ── Pool de participantes ─────────────────────────────────────────────────

    @staticmethod
    def present_pool_entry(result: PoolEntryResult) -> PoolEntryOut:
        """Transform a PoolEntryResult into its HTTP wrapper.

        Pure transformer — the eligibility (`tiene_cupo_activo`, `estado_pool`
        and `motivo_bloqueo`) is decided by the domain selector, never here.
        """
        return PoolEntryOut(
            id=result.id,
            persona=PersonaSummarySchema(
                id=result.persona_id,
                nombre=result.persona_nombre,
                nombres=result.persona_nombres,
                apellidos=result.persona_apellidos,
                numero_documento=result.persona_numero_documento,
            ),
            estado=result.estado,
            created_at=result.created_at.isoformat(),
            tiene_cupo_activo=result.tiene_cupo_activo,
            estado_pool=result.estado_pool,
            motivo_bloqueo=result.motivo_bloqueo,
        )

    @staticmethod
    def present_pool(results: list[PoolEntryResult]) -> list[PoolEntryOut]:
        """Transform a list of PoolEntryResult into a list of PoolEntryOut."""
        return [InscripcionPresenter.present_pool_entry(r) for r in results]

    # ── Team-scoped participant selector ───────────────────────────────────

    @staticmethod
    def present_elegible(result: ElegibleResult) -> ElegibleOut:
        """Transform an ElegibleResult into its HTTP wrapper.

        Pure transformer — the eligibility verdict (`asignable`,
        `motivo_no_asignable`) is decided by the domain selector, never here.
        """
        return ElegibleOut(
            id=result.id,
            persona=PersonaSummarySchema(
                id=result.persona_id,
                nombre=result.persona_nombre,
                nombres=result.persona_nombres,
                apellidos=result.persona_apellidos,
                numero_documento=result.persona_numero_documento,
            ),
            estado=result.estado,
            created_at=result.created_at.isoformat(),
            tiene_cupo_activo=result.tiene_cupo_activo,
            estado_pool=result.estado_pool,
            motivo_bloqueo=result.motivo_bloqueo,
            disciplinas_asignadas=[
                DisciplinaAsignadaOut(
                    disciplina=DisciplinaSummarySchema(
                        id=disciplina.disciplina_id,
                        nombre=disciplina.disciplina_nombre,
                        sigla=disciplina.disciplina_sigla,
                    ),
                    equipo_id=disciplina.equipo_id,
                    equipo_nombre=disciplina.equipo_nombre,
                )
                for disciplina in result.disciplinas_asignadas
            ],
            ya_en_disciplina=result.ya_en_disciplina,
            asignable=result.asignable,
            motivo_no_asignable=result.motivo_no_asignable,
        )

    @staticmethod
    def present_elegibles_equipo(result: ElegiblesEquipoResult) -> ElegiblesEquipoOut:
        """Transform an ElegiblesEquipoResult into its HTTP wrapper."""
        return ElegiblesEquipoOut(
            inscripcion_id=result.inscripcion_id,
            equipo_id=result.equipo_id,
            equipo_nombre=result.equipo_nombre,
            disciplina=DisciplinaSummarySchema(
                id=result.disciplina_id,
                nombre=result.disciplina_nombre,
                sigla=result.disciplina_sigla,
            ),
            elegibles=[InscripcionPresenter.present_elegible(e) for e in result.elegibles],
        )
