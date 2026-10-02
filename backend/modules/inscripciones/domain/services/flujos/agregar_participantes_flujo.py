"""
AgregarParticipantesFlujo — async flow for adding multiple participants to an existing equipo.

Async flow with transaction.atomic — validates and adds one or more participants
to an existing equipo in a single request.
"""

import asyncio

from django.db import transaction
from injector import inject

from modules.inscripciones.domain.models import (
    EquipoInscrito,
    ParticipacionDisciplina,
    ParticipanteInscripcion,
)
from modules.inscripciones.domain import exceptions as exc
from modules.inscripciones.domain.services.core.participacion_service import ParticipacionService
from modules.inscripciones.domain.services.core.participante_service import ParticipanteService
from modules.inscripciones.domain.services.core.equipo_service import EquipoService
from modules.inscripciones.domain.services.core import validators


class AgregarParticipantesFlujo:
    """
    Async flow for adding multiple participants to an existing equipo.

    Validates:
    - Equipo belongs to the given inscription (ownership check)
    - R11: person not already in this discipline+event
    - Package capacity not exceeded
    - Equipo↔discipline consistency
    - max_jugadores not exceeded after adding
    """

    @inject
    def __init__(
        self,
        participacion_svc: ParticipacionService,
        participante_svc: ParticipanteService,
        equipo_svc: EquipoService,
    ):
        self.participacion_svc = participacion_svc
        self.participante_svc = participante_svc
        self.equipo_svc = equipo_svc

    async def _agregar_participantes(
        self,
        inscripcion_id: str,
        equipo_id: str,
        participantes_data: list[dict],
    ) -> list[ParticipanteInscripcion]:
        """
        Add multiple participants to an existing equipo.

        Args:
            inscripcion_id: UUID of the inscription (for ownership validation).
            equipo_id: UUID of the equipo.
            participantes_data: List of participant dicts, each with:
                - persona_id OR inline persona fields (tipoDocumento, numeroDocumento, etc.)
                - rol, talle_camiseta
                - acepto_bases, acepto_aptitud_fisica, acepto_imagen (bool)

        Returns:
            List of created ParticipanteInscripcion records.

        Raises:
            EquipoNotFoundError: If equipo not found.
            InscripcionNotFoundError: If equipo doesn't belong to the inscription.
            ParticipacionDuplicadaError: If R11 violation for any participant.
            CupoExcedidoError: If package capacity would be exceeded.
            ConsistenciaEquipoError: If team consistency check fails.
            MaxJugadoresExcedidoError: If max_jugadores would be exceeded.
        """
        return await asyncio.to_thread(
            self._agregar_participantes_sync,
            inscripcion_id=inscripcion_id,
            equipo_id=equipo_id,
            participantes_data=participantes_data,
        )

    @transaction.atomic()
    def _agregar_participantes_sync(
        self,
        inscripcion_id: str,
        equipo_id: str,
        participantes_data: list[dict],
    ) -> list[ParticipanteInscripcion]:
        """
        Sync version wrapped in transaction.atomic.
        """
        # Get equipo and validate it exists and belongs to inscription
        equipo = self.equipo_svc.obtener(equipo_id)
        if equipo is None:
            raise exc.EquipoNotFoundError(f"Equipo {equipo_id} no encontrado.")

        # Validate equipo belongs to the given inscription
        if str(equipo.inscripcion_id) != str(inscripcion_id):
            raise exc.InscripcionNotFoundError(
                f"El equipo {equipo_id} no pertenece a la inscripción {inscripcion_id}."
            )

        inscripcion = equipo.inscripcion
        paquete = inscripcion.paquete
        evento_id = str(inscripcion.evento_id)
        disciplina_id = str(equipo.disciplina_id)

        # Validate discipline is in package
        if not validators.validar_disciplina_en_paquete(paquete, disciplina_id):
            raise exc.DisciplinaNoEnPaqueteError(
                f"La disciplina {disciplina_id} no está incluida en el paquete."
            )

        # Current participant count (ParticipacionDisciplina records for this equipo)
        cantidad_actual = equipo.participaciones.count()
        disciplina = equipo.disciplina
        max_jugadores = disciplina.max_jugadores

        # Check max_jugadores limit before starting
        if max_jugadores is not None and len(participantes_data) > max_jugadores - cantidad_actual:
            raise exc.MaxJugadoresExcedidoError(
                f"El equipo no puede exceder {max_jugadores} jugadores. "
                f"Espacios disponibles: {max_jugadores - cantidad_actual}."
            )

        created_participantes = []

        for p_data in participantes_data:
            rol = p_data.get("rol", "JUGADOR")
            talle_camiseta = p_data.get("talle_camiseta")
            notas = p_data.get("notas")
            acepto_bases = p_data.get("acepto_bases")
            acepto_aptitud_fisica = p_data.get("acepto_aptitud_fisica")
            acepto_imagen = p_data.get("acepto_imagen")

            # ── Resolve Persona ──────────────────────────────────────────────
            persona_id = p_data.get("persona_id")

            if persona_id:
                # Legacy mode: verify persona exists
                from modules.usuarios.domain.services.core.persona_core_service import PersonaCoreService
                persona_core = PersonaCoreService()
                persona = persona_core._get_persona_por_id(persona_id)
                if persona is None:
                    raise exc.PersonaNotFoundError(persona_id)
            else:
                # Inline mode: lookup or create by document
                from modules.usuarios.domain.services.core.persona_core_service import PersonaCoreService
                persona_core = PersonaCoreService()

                tipo_doc = p_data.get("tipoDocumento")
                num_doc = p_data.get("numeroDocumento")
                nombres = p_data.get("nombres", "").strip()
                apellidos = p_data.get("apellidos", "").strip()
                genero = p_data.get("genero")
                telefono = p_data.get("telefono")
                whatsapp = p_data.get("whatsapp")

                persona = persona_core._get_persona_por_documento(tipo_doc, num_doc)
                if persona is None:
                    # Create new Persona
                    persona_data = {
                        "nombres": nombres,
                        "apellidos": apellidos,
                        "tipo_documento": tipo_doc,
                        "numero_documento": num_doc,
                        "genero": genero,
                    }
                    if telefono:
                        persona_data["telefono"] = telefono.strip()
                    if whatsapp:
                        persona_data["whatsapp"] = whatsapp.strip()
                    persona = persona_core._crear_persona(persona_data)
                else:
                    # Reuse existing: update contact fields if provided
                    needs_save = False
                    if telefono and not persona.telefono:
                        persona.telefono = telefono.strip()
                        needs_save = True
                    if whatsapp and not persona.whatsapp:
                        persona.whatsapp = whatsapp.strip()
                        needs_save = True
                    if needs_save:
                        persona.save()

            persona_id_str = str(persona.id)

            # ── Update Persona boolean acceptance fields ─────────────────────
            if acepto_bases is not None or acepto_aptitud_fisica is not None or acepto_imagen is not None:
                if acepto_bases is not None:
                    persona.acepto_bases = acepto_bases
                if acepto_aptitud_fisica is not None:
                    persona.acepto_aptitud_fisica = acepto_aptitud_fisica
                if acepto_imagen is not None:
                    persona.acepto_imagen = acepto_imagen
                persona.save(update_fields=["acepto_bases", "acepto_aptitud_fisica", "acepto_imagen"])

            # ── Check for existing ParticipacionDisciplina (R11) ─────────────
            existente = ParticipacionDisciplina.objects.filter(
                evento_id=evento_id,
                disciplina_id=disciplina_id,
                persona_id=persona_id_str,
                equipo_id=equipo_id,
            ).first()

            if existente:
                ya_linkeado = ParticipanteInscripcion.objects.filter(
                    participacion=existente,
                    equipo_id=equipo_id,
                ).exists()
                if not ya_linkeado:
                    from modules.inscripciones.domain.schemas import ParticipanteCreateData
                    participante = self.participante_svc.crear(ParticipanteCreateData(
                        participacion_id=str(existente.id),
                        equipo_id=equipo_id,
                        rol=rol,
                        talle_camiseta=talle_camiseta,
                        notas=notas,
                    ))
                    created_participantes.append(participante)
                continue

            # ── Check R11 (person already in this discipline+event via different team) ──
            if validators.validar_r11_prevent_duplicado(
                evento_id=evento_id,
                disciplina_id=disciplina_id,
                persona_id=persona_id_str,
            ):
                raise exc.ParticipacionDuplicadaError(
                    f"La persona ya está registrada en {disciplina.nombre} en este evento."
                )

            # ── Validate package capacity (Nivel 2) ───────────────────────────
            capacidad_errors = validators.validar_cupo_paquete(inscripcion, paquete)
            if capacidad_errors:
                persona_ya_esta = ParticipacionDisciplina.objects.filter(
                    equipo__inscripcion=inscripcion,
                    persona_id=persona_id_str,
                ).exists()
                if not persona_ya_esta:
                    raise exc.CupoExcedidoError("; ".join(capacidad_errors))

            # ── Create ParticipacionDisciplina ─────────────────────────────
            from modules.inscripciones.domain.schemas import ParticipacionCreateData
            participacion = self.participacion_svc.crear(ParticipacionCreateData(
                evento_id=evento_id,
                disciplina_id=disciplina_id,
                persona_id=persona_id_str,
                equipo_id=equipo_id,
            ))

            # ── Create ParticipanteInscripcion ─────────────────────────────
            from modules.inscripciones.domain.schemas import ParticipanteCreateData
            participante = self.participante_svc.crear(ParticipanteCreateData(
                participacion_id=str(participacion.id),
                equipo_id=equipo_id,
                rol=rol,
                talle_camiseta=talle_camiseta,
                notas=notas,
            ))
            created_participantes.append(participante)

            # ── Check max_jugadores after each addition ───────────────────
            cantidad_actual += 1
            if max_jugadores is not None and cantidad_actual > max_jugadores:
                raise exc.MaxJugadoresExcedidoError(
                    f"El equipo no puede exceder {max_jugadores} jugadores."
                )

        return created_participantes
