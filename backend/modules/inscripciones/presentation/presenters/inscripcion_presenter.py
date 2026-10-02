"""InscripcionPresenter — transforma modelos de dominio a esquemas HTTP."""

from modules.inscripciones.presentation.schemas import (
    InscripcionOut,
    InscripcionDetalleOut,
    DelegadoOut,
    EquipoOut,
    EquipoDetalleOut,
    ParticipanteOut,
    PersonaResumenOut,
    DisciplinaResumenOut,
    CategoriaResumenOut,
    EventoResumenOut,
    PaqueteResumenOut,
    PromocionResumenOut,
)


class InscripcionPresenter:
    """Presenter for inscription-related responses."""

    # ── Persona ──────────────────────────────────────────────────────────────

    @staticmethod
    def _present_persona(persona) -> PersonaResumenOut:
        """Transform a Persona instance to PersonaResumenOut."""
        return PersonaResumenOut(
            id=str(persona.id),
            nombres=persona.nombres,
            apellidos=persona.apellidos,
            numero_documento=persona.numero_documento,
        )

    # ── Disciplina/Categoria ─────────────────────────────────────────────────

    @staticmethod
    def _present_disciplina_resumen(disciplina) -> DisciplinaResumenOut:
        return DisciplinaResumenOut(
            id=str(disciplina.id),
            nombre=disciplina.nombre,
            sigla=disciplina.sigla,
        )

    @staticmethod
    def _present_categoria_resumen(categoria) -> CategoriaResumenOut:
        return CategoriaResumenOut(
            id=str(categoria.id),
            nombre=categoria.nombre,
        )

    # ── Equipo ────────────────────────────────────────────────────────────────

    @staticmethod
    def present_equipo(equipo) -> EquipoOut:
        """Transform an EquipoInscrito to EquipoOut."""
        return EquipoOut(
            id=str(equipo.id),
            inscripcion_id=str(equipo.inscripcion_id),
            disciplina_id=str(equipo.disciplina_id),
            categoria_id=str(equipo.categoria_id) if equipo.categoria_id else None,
            nombre=equipo.nombre,
        )

    @staticmethod
    def present_equipo_detalle(equipo) -> EquipoDetalleOut:
        """Transform an EquipoInscrito with related data to EquipoDetalleOut."""
        participantes = []
        if hasattr(equipo, "participantes_inscripcion"):
            for p in equipo.participantes_inscripcion.all():
                persona = p.participacion.persona
                participantes.append(
                    ParticipanteOut(
                        id=str(p.id),
                        participacion_id=str(p.participacion_id),
                        equipo_id=str(p.equipo_id),
                        rol=p.rol,
                        talle_camiseta=p.talle_camiseta,
                        notas=getattr(p, "notas", None),
                        persona=InscripcionPresenter._present_persona(persona),
                        acepto_bases=getattr(persona, "acepto_bases", False),
                        acepto_aptitud_fisica=getattr(persona, "acepto_aptitud_fisica", False),
                        acepto_imagen=getattr(persona, "acepto_imagen", False),
                    )
                )

        return EquipoDetalleOut(
            id=str(equipo.id),
            inscripcion_id=str(equipo.inscripcion_id),
            disciplina_id=str(equipo.disciplina_id),
            categoria_id=str(equipo.categoria_id) if equipo.categoria_id else None,
            nombre=equipo.nombre,
            disciplina=InscripcionPresenter._present_disciplina_resumen(equipo.disciplina),
            categoria=InscripcionPresenter._present_categoria_resumen(equipo.categoria) if equipo.categoria_id else None,
            participantes=participantes,
        )

    # ── Delegado ────────────────────────────────────────────────────────────

    @staticmethod
    def present_delegado(delegado) -> DelegadoOut:
        """Transform an InscripcionDelegado to DelegadoOut."""
        persona = getattr(delegado, "persona", None)
        return DelegadoOut(
            id=str(delegado.id),
            inscripcion_id=str(delegado.inscripcion_id),
            persona_id=str(delegado.persona_id),
            persona_nombre=f"{persona.nombres} {persona.apellidos}" if persona else None,
            persona_numero_documento=persona.numero_documento if persona else None,
        )

    # ── Evento/Paquete ─────────────────────────────────────────────────────

    @staticmethod
    def _present_evento_resumen(evento) -> EventoResumenOut:
        return EventoResumenOut(
            id=str(evento.id),
            nombre=evento.nombre,
        )

    @staticmethod
    def _present_paquete_resumen(paquete) -> PaqueteResumenOut:
        return PaqueteResumenOut(
            id=str(paquete.id),
            nombre=paquete.nombre,
        )

    # ── Inscripcion ────────────────────────────────────────────────────────

    @staticmethod
    def _present_promocion(promocion) -> PromocionResumenOut | None:
        """Transform a Promocion instance to PromocionResumenOut."""
        if promocion is None:
            return None
        return PromocionResumenOut(
            id=str(promocion.id),
            anio=promocion.anio,
            nombre=promocion.nombre,
        )

    @staticmethod
    def present_inscripcion(inscripcion) -> InscripcionOut:
        """Transform an Inscripcion model to InscripcionOut."""
        cantidad_equipos = 0
        cantidad_participantes = 0
        if hasattr(inscripcion, "equipos"):
            equipos_qs = inscripcion.equipos.all()
            cantidad_equipos = equipos_qs.count()
            for eq in equipos_qs:
                if hasattr(eq, "participantes_inscripcion"):
                    cantidad_participantes += eq.participantes_inscripcion.count()
        evento_nombre = getattr(getattr(inscripcion, "evento", None), "nombre", None)
        paquete_nombre = getattr(getattr(inscripcion, "paquete", None), "nombre", None)
        return InscripcionOut(
            id=str(inscripcion.id),
            evento_id=str(inscripcion.evento_id),
            responsable_id=str(inscripcion.responsable_id),
            paquete_id=str(inscripcion.paquete_id),
            promocion=InscripcionPresenter._present_promocion(inscripcion.promocion),
            fusion_promocion=InscripcionPresenter._present_promocion(getattr(inscripcion, 'fusion_promocion', None)),
            estado=inscripcion.estado,
            observacion=inscripcion.observacion,
            created_at=inscripcion.created_at,
            evento_nombre=evento_nombre,
            paquete_nombre=paquete_nombre,
            promocion_nombre=(
                getattr(inscripcion.promocion, "nombre", None)
                if getattr(inscripcion, "promocion", None)
                else None
            ),
            fusion_promocion_nombre=(
                getattr(
                    getattr(inscripcion, "fusion_promocion", None),
                    "nombre",
                    None,
                )
            ),
            cantidad_equipos=cantidad_equipos,
            cantidad_participantes=cantidad_participantes,
        )

    @staticmethod
    def present_inscripcion_detalle(inscripcion) -> InscripcionDetalleOut:
        """Transform an Inscripcion with related data to InscripcionDetalleOut."""
        # Load related data if not already loaded
        evento = getattr(inscripcion, "evento", None)
        paquete = getattr(inscripcion, "paquete", None)

        # Get delegate if available (already prefetched by selector)
        delegado = None
        if hasattr(inscripcion, "delegados"):
            delegados_qs = inscripcion.delegados.all()
            if delegados_qs:
                delegado = delegados_qs[0]

        # Present equipos with detail (equipos is prefetched by selector)
        equipos_out = []
        if hasattr(inscripcion, "equipos"):
            for eq in inscripcion.equipos.all():
                equipos_out.append(InscripcionPresenter.present_equipo_detalle(eq))

        # Get responsible's acceptance booleans
        responsable = getattr(inscripcion, "responsable", None)
        responsable_acepto_bases = getattr(responsable, "acepto_bases", False) if responsable else False
        responsable_acepto_aptitud_fisica = getattr(responsable, "acepto_aptitud_fisica", False) if responsable else False
        responsable_acepto_imagen = getattr(responsable, "acepto_imagen", False) if responsable else False

        return InscripcionDetalleOut(
            id=str(inscripcion.id),
            evento_id=str(inscripcion.evento_id),
            responsable_id=str(inscripcion.responsable_id),
            paquete_id=str(inscripcion.paquete_id),
            promocion=InscripcionPresenter._present_promocion(inscripcion.promocion),
            fusion_promocion=InscripcionPresenter._present_promocion(getattr(inscripcion, 'fusion_promocion', None)),
            estado=inscripcion.estado,
            observacion=inscripcion.observacion,
            created_at=inscripcion.created_at,
            evento=InscripcionPresenter._present_evento_resumen(evento) if evento else EventoResumenOut(id=str(inscripcion.evento_id), nombre=""),
            paquete=InscripcionPresenter._present_paquete_resumen(paquete) if paquete else PaqueteResumenOut(id=str(inscripcion.paquete_id), nombre=""),
            equipos=equipos_out,
            delegado=InscripcionPresenter.present_delegado(delegado) if delegado else None,
            responsable_acepto_bases=responsable_acepto_bases,
            responsable_acepto_aptitud_fisica=responsable_acepto_aptitud_fisica,
            responsable_acepto_imagen=responsable_acepto_imagen,
        )
