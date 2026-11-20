"""`AdminOperacionPresenter` — la proyección HTTP de la CAPA OPERATIVA.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

El presenter **transforma y nada más**: recibe el resultado del dominio y
devuelve la forma HTTP. No consulta la base de datos, no llama a un selector
y no decide nada
(`contract/api-wrapper-presenter-contract.md` §3).

## Lo que el presenter NO hace

- **No deriva veredictos.** El `estado_operativo` que se publica es el que
  calculó el dueño; aquí sólo se copia.
- **No inventa importes.** El total y la moneda son los que la compra
  congeló; viajan como texto, nunca como `float` (`FR-08` §2.4).
- **No inventa relaciones.** Lo que el objetivo no relaciona no se publica.
"""

from modules.administracion.presentation.schemas.admin_operacion_schemas import (
    AccionOperativaOut,
    AdminEquipoDetalleOut,
    AdminEquipoListItemOut,
    AdminInscripcionDetalleOut,
    AdminInscripcionListItemOut,
    AdminPagoDetalleOut,
    AdminPagoListItemOut,
    AdminPersonaDetalleOut,
    AdminPersonaListItemOut,
    CandidatoAEquipoOut,
    CausaOut,
    CompraDeCuposOut,
    CompraOut,
    CompradorOut,
    CuposOperativosOut,
    EntregaDerechosOut,
    EquipoDeInscripcionOut,
    EstadoOperativoOut,
    EventoHistorialAdminOut,
    EventoHistorialOut,
    InscripcionDetalleEquipoOut,
    IntentoPagoOut,
    OperacionManualOut,
    ParticipacionAdminOut,
    ParticipacionPoolOut,
    ParticipanteAdminOut,
    ParticipanteDeEquipoOut,
    PersonaOut,
    PlantillaEquipoOut,
    PoolOut,
    ReferenciaOut,
)


class AdminOperacionPresenter:
    """Proyecta los resultados del dominio a las formas HTTP del panel."""

    # ── Vocabulario compartido ──────────────────────────────────────────────

    @staticmethod
    def present_estado(estado) -> EstadoOperativoOut:
        """El veredicto operativo."""
        return EstadoOperativoOut(
            codigo=estado.codigo,
            etiqueta=estado.etiqueta,
            descripcion=estado.descripcion,
        )

    @staticmethod
    def present_causa(causa) -> CausaOut:
        """Una causa con su prosa."""
        return CausaOut(codigo=causa.codigo, mensaje=causa.mensaje)

    @staticmethod
    def present_accion(accion) -> AccionOperativaOut:
        """Una acción proyectada."""
        return AccionOperativaOut(
            codigo=accion.codigo,
            etiqueta=accion.etiqueta,
            href=accion.href,
        )

    @staticmethod
    def present_cupos(cupos) -> CuposOperativosOut:
        """Los tres cupos."""
        return CuposOperativosOut(
            adquiridos=cupos.adquiridos,
            asignados=cupos.asignados,
            disponibles=cupos.disponibles,
        )

    @staticmethod
    def present_referencia(referencia) -> ReferenciaOut:
        """Una referencia a un registro del área."""
        return ReferenciaOut(id=referencia.id, nombre=referencia.nombre)

    # ── Inscripciones ────────────────────────────────────────────────────────

    @staticmethod
    def present_inscripcion_lista(item) -> AdminInscripcionListItemOut:
        """La fila de la lista de inscripciones."""
        return AdminInscripcionListItemOut(
            id=item.id,
            responsable=PersonaOut(
                id=item.responsable.id, nombre=item.responsable.nombre
            ),
            paquete=AdminOperacionPresenter.present_referencia(item.paquete),
            edicion=AdminOperacionPresenter.present_referencia(item.edicion),
            equipos=item.equipos,
            personas=item.personas,
            estado=AdminOperacionPresenter.present_estado(item.estado),
            cupos=AdminOperacionPresenter.present_cupos(item.cupos),
            pago=(
                AdminOperacionPresenter.present_estado(item.pago)
                if item.pago
                else None
            ),
            alerta=(
                AdminOperacionPresenter.present_causa(item.alerta)
                if item.alerta
                else None
            ),
            siguiente_accion=(
                AdminOperacionPresenter.present_accion(item.siguiente_accion)
                if item.siguiente_accion
                else None
            ),
        )

    @staticmethod
    def present_inscripcion_detalle(detalle) -> AdminInscripcionDetalleOut:
        """El detalle de una inscripción."""
        base = AdminOperacionPresenter.present_inscripcion_lista(detalle.item)

        return AdminInscripcionDetalleOut(
            **base.model_dump(),
            equipos_detalle=[
                AdminOperacionPresenter.present_equipo_de_inscripcion(equipo)
                for equipo in detalle.equipos_detalle
            ],
            pool=(
                AdminOperacionPresenter.present_pool(detalle.pool)
                if detalle.pool
                else None
            ),
            compras=[
                AdminOperacionPresenter.present_compra_de_cupos(compra)
                for compra in detalle.compras
            ],
            historial=[
                AdminOperacionPresenter.present_evento(evento)
                for evento in detalle.historial
            ],
        )

    @staticmethod
    def present_equipo_de_inscripcion(equipo) -> EquipoDeInscripcionOut:
        """El equipo de una inscripción."""
        return EquipoDeInscripcionOut(
            id=equipo.id,
            nombre=equipo.nombre,
            disciplina=AdminOperacionPresenter.present_referencia(equipo.disciplina),
            estado=equipo.estado,
            participantes=[
                AdminOperacionPresenter.present_participante_de_equipo(participante)
                for participante in equipo.participantes
            ],
            estado_operativo=AdminOperacionPresenter.present_estado(
                equipo.estado_operativo
            ),
        )

    @staticmethod
    def present_participante_de_equipo(participante) -> ParticipanteDeEquipoOut:
        """Una persona de la plantilla de un equipo."""
        return ParticipanteDeEquipoOut(
            id=participante.id,
            persona_id=participante.persona_id,
            nombre=participante.nombre,
            documento=participante.documento,
            rol=participante.rol,
            estado=participante.estado,
        )

    @staticmethod
    def present_pool(pool) -> PoolOut:
        """El pool de una inscripción."""
        return PoolOut(
            cupos_pagados=pool.cupos_pagados,
            cupos_asignados=pool.cupos_asignados,
            cupos_disponibles=pool.cupos_disponibles,
            participaciones=[
                ParticipacionPoolOut(
                    id=participacion.id,
                    persona_id=participacion.persona_id,
                    equipo_id=participacion.equipo_id,
                    equipo_nombre=participacion.equipo_nombre,
                    disciplina_nombre=participacion.disciplina_nombre,
                    rol=participacion.rol,
                    estado=participacion.estado,
                    ocupa_cupo=participacion.ocupa_cupo,
                )
                for participacion in pool.participaciones
            ],
            impedimentos=[
                AdminOperacionPresenter.present_causa(impedimento)
                for impedimento in pool.impedimentos
            ],
        )

    @staticmethod
    def present_compra_de_cupos(compra) -> CompraDeCuposOut:
        """Una compra que financia la inscripción."""
        return CompraDeCuposOut(
            compra_id=compra.compra_id,
            orden_pago_id=compra.orden_pago_id,
            estado=compra.estado,
            total=compra.total,
            moneda=compra.moneda,
            estado_operativo=AdminOperacionPresenter.present_estado(
                compra.estado_operativo
            ),
        )

    @staticmethod
    def present_evento(evento) -> EventoHistorialOut:
        """Un evento del historial."""
        return EventoHistorialOut(
            occurred_at=evento.occurred_at,
            tipo=evento.tipo,
            descripcion=evento.descripcion,
            actor=evento.actor,
        )

    # ── Equipos ──────────────────────────────────────────────────────────────

    @staticmethod
    def present_equipo_lista(item) -> AdminEquipoListItemOut:
        """La fila de la lista de equipos."""
        return AdminEquipoListItemOut(
            id=item.id,
            nombre=item.nombre,
            disciplina=AdminOperacionPresenter.present_referencia(item.disciplina),
            categoria=(
                AdminOperacionPresenter.present_referencia(item.categoria)
                if item.categoria
                else None
            ),
            plantilla=PlantillaEquipoOut(
                registrados=item.plantilla.registrados,
                minimo=item.plantilla.minimo,
                maximo=item.plantilla.maximo,
            ),
            estado_operativo=AdminOperacionPresenter.present_estado(
                item.estado_operativo
            ),
            acciones_disponibles=list(item.acciones_disponibles),
            responsable=AdminOperacionPresenter.present_referencia(item.responsable),
            inscripcion=AdminOperacionPresenter.present_referencia(item.inscripcion),
        )

    @staticmethod
    def present_equipo_detalle(detalle) -> AdminEquipoDetalleOut:
        """El detalle de un equipo."""
        base = AdminOperacionPresenter.present_equipo_lista(detalle.item)

        return AdminEquipoDetalleOut(
            **base.model_dump(),
            participantes=[
                AdminOperacionPresenter.present_participante_de_equipo(participante)
                for participante in detalle.participantes
            ],
            cupos=(
                AdminOperacionPresenter.present_cupos(detalle.cupos)
                if detalle.cupos
                else None
            ),
            inscripcion_detalle=(
                InscripcionDetalleEquipoOut(
                    id=detalle.inscripcion_detalle.id,
                    nombre=detalle.inscripcion_detalle.nombre,
                    referencia=detalle.inscripcion_detalle.nombre,
                )
                if detalle.inscripcion_detalle
                else None
            ),
            elegibilidad=[
                CandidatoAEquipoOut(
                    id=candidato.id,
                    persona_id=candidato.persona_id,
                    nombre=candidato.nombre,
                    documento=candidato.documento,
                    estado_operativo=AdminOperacionPresenter.present_estado(
                        candidato.estado_operativo
                    ),
                )
                for candidato in detalle.elegibilidad
            ],
        )

    # ── Participantes y personas ─────────────────────────────────────────────

    @staticmethod
    def present_participacion_admin(participacion) -> ParticipacionAdminOut:
        """Una participación de una persona."""
        return ParticipacionAdminOut(
            id=participacion.id,
            edicion=AdminOperacionPresenter.present_referencia(participacion.edicion),
            equipo=AdminOperacionPresenter.present_referencia(participacion.equipo),
            disciplina=AdminOperacionPresenter.present_referencia(
                participacion.disciplina
            ),
            rol=participacion.rol,
            estado=participacion.estado,
            conflicto=(
                AdminOperacionPresenter.present_causa(participacion.conflicto)
                if participacion.conflicto
                else None
            ),
        )

    @staticmethod
    def present_participante_admin(item) -> ParticipanteAdminOut:
        """La persona con sus participaciones."""
        return ParticipanteAdminOut(
            id=item.id,
            nombre=item.nombre,
            documento=item.documento,
            participaciones=[
                AdminOperacionPresenter.present_participacion_admin(participacion)
                for participacion in item.participaciones
            ],
            historial=[
                EventoHistorialAdminOut(
                    occurred_at=evento.occurred_at,
                    tipo=evento.tipo,
                    descripcion=evento.descripcion,
                )
                for evento in item.historial
            ],
        )

    @staticmethod
    def present_persona_lista(item) -> AdminPersonaListItemOut:
        """La fila de la búsqueda de personas."""
        base = AdminOperacionPresenter.present_participante_admin(item)

        return AdminPersonaListItemOut(**base.model_dump())

    @staticmethod
    def present_persona_detalle(detalle) -> AdminPersonaDetalleOut:
        """El detalle de una persona."""
        base = AdminOperacionPresenter.present_persona_lista(detalle.item)

        return AdminPersonaDetalleOut(
            **base.model_dump(),
            telefono=detalle.telefono,
            whatsapp=detalle.whatsapp,
            email=detalle.email,
        )

    # ── Pagos ────────────────────────────────────────────────────────────────

    @staticmethod
    def present_pago_lista(item) -> AdminPagoListItemOut:
        """La fila de la lista de pagos."""
        return AdminPagoListItemOut(
            compra_id=item.compra_id,
            orden_pago_id=item.orden_pago_id,
            tipo_compra=item.tipo_compra,
            resumen_concepto=item.resumen_concepto,
            comprador=CompradorOut(
                persona_id=item.comprador.persona_id, nombre=item.comprador.nombre
            ),
            monto=item.monto,
            moneda=item.moneda,
            estado_operativo=AdminOperacionPresenter.present_estado(
                item.estado_operativo
            ),
            entrega_derechos=EntregaDerechosOut(
                codigo=item.entrega_derechos.codigo,
                etiqueta=item.entrega_derechos.etiqueta,
            ),
            acciones_disponibles=list(item.acciones_disponibles),
            fecha=item.fecha,
        )

    @staticmethod
    def present_pago_detalle(detalle) -> AdminPagoDetalleOut:
        """El detalle comercial de un pago."""
        base = AdminOperacionPresenter.present_pago_lista(detalle.item)

        return AdminPagoDetalleOut(
            **base.model_dump(),
            compra=(
                CompraOut(
                    id=detalle.compra.id,
                    estado=detalle.compra.estado,
                    total=detalle.compra.total,
                    moneda=detalle.compra.moneda,
                )
                if detalle.compra
                else None
            ),
            origen_pago=detalle.origen_pago,
            intentos=[
                IntentoPagoOut(
                    id=intento.id,
                    intento=intento.intento,
                    estado=intento.estado,
                    verificada=intento.verificada,
                    codigo_respuesta=intento.codigo_respuesta,
                    metodo_pago=intento.metodo_pago,
                    creada_en=intento.creada_en,
                )
                for intento in detalle.intentos
            ],
            operaciones_manuales=[
                OperacionManualOut(
                    id=operacion.id,
                    canal=operacion.canal,
                    monto=operacion.monto,
                    moneda=operacion.moneda,
                    motivo=operacion.motivo,
                    registrada_en=operacion.registrada_en,
                    actor=operacion.actor,
                )
                for operacion in detalle.operaciones_manuales
            ],
            siguiente_accion=(
                AdminOperacionPresenter.present_accion(detalle.siguiente_accion)
                if detalle.siguiente_accion
                else None
            ),
        )


__all__ = ["AdminOperacionPresenter"]
