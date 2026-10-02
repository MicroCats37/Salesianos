"""
CrearInscripcionFlujo — async flow for creating an inscription with teams and participants.

Async flow with transaction.atomic — coordinates the complete inscription creation.
"""

import asyncio

from django.db import transaction
from injector import inject

from django.conf import settings

from modules.inscripciones.domain.models import (
    Inscripcion,
    EquipoInscrito,
    ParticipacionDisciplina,
    ParticipanteInscripcion,
    Paquete,
    Evento,
)
from modules.inscripciones.domain import exceptions as exc
from modules.inscripciones.domain.services.core.disciplina_service import DisciplinaService
from modules.inscripciones.domain.services.core.paquete_service import PaqueteService
from modules.inscripciones.domain.services.core.evento_service import EventoService
from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService
from modules.inscripciones.domain.services.core.equipo_service import EquipoService
from modules.inscripciones.domain.services.core.participacion_service import ParticipacionService
from modules.inscripciones.domain.services.core.participante_service import ParticipanteService
from modules.inscripciones.domain.services.core import validators
from modules.usuarios.domain.services.core.persona_core_service import PersonaCoreService


class CrearInscripcionFlujo:
    """
    Async flow for creating a complete inscription.

    Creates:
    1. Inscripcion
    2. EquipoInscrito (one per discipline in the package)
    3. ParticipacionDisciplina + ParticipanteInscripcion per participant

    Participant resolution:
    - If `persona_id` is provided, the existing Persona is used.
    - If inline data is provided, the Persona is looked up by
      (tipo_documento, numero_documento). If found, it is reused;
      if not found, a new Persona is created.

    All within a single transaction.atomic.
    """

    @inject
    def __init__(
        self,
        disciplina_svc: DisciplinaService,
        paquete_svc: PaqueteService,
        evento_svc: EventoService,
        inscripcion_svc: InscripcionService,
        equipo_svc: EquipoService,
        participacion_svc: ParticipacionService,
        participante_svc: ParticipanteService,
        persona_core: PersonaCoreService,
    ):
        self.disciplina_svc = disciplina_svc
        self.paquete_svc = paquete_svc
        self.evento_svc = evento_svc
        self.inscripcion_svc = inscripcion_svc
        self.equipo_svc = equipo_svc
        self.participacion_svc = participacion_svc
        self.participante_svc = participante_svc
        self.persona_core = persona_core

    def _actualizar_aceptaciones(
        self,
        responsable_id: str,
        accepted_bases: bool | None,
        fitness_declaration: bool | None,
        image_consent: bool | None,
    ) -> None:
        """
        Set acceptance boolean flags on the responsible Persona.
        """
        from modules.usuarios.domain.models import Persona

        persona = Persona.objects.filter(id=responsable_id).first()
        if persona is None:
            return
        if accepted_bases is not None:
            persona.acepto_bases = accepted_bases
        if fitness_declaration is not None:
            persona.acepto_aptitud_fisica = fitness_declaration
        if image_consent is not None:
            persona.acepto_imagen = image_consent
        persona.save(update_fields=["acepto_bases", "acepto_aptitud_fisica", "acepto_imagen"])

    async def _crear_inscripcion_completa(
        self,
        responsable_id: str,
        paquete_id: str,
        promocion_id: str,
        observacion: str | None,
        equipos_data: list[dict],
        fusion_promocion_id: str | None = None,
        accepted_bases: bool | None = None,
        fitness_declaration: bool | None = None,
        image_consent: bool | None = None,
    ) -> Inscripcion:
        """
        Create a complete inscription with teams and participants.

        The active event is resolved internally via `EVENTO_ACTIVO_NOMBRE`
        in settings — it is NOT provided by the client.

        Args:
            responsable_id: UUID of the responsible persona.
            paquete_id: UUID of the package.
            promocion_id: UUID of the Promocion.
            observacion: Optional observation.
            equipos_data: List of dicts with:
                - disciplina_id: UUID
                - categoria_id: UUID | None (optional — frontend may omit)
                - nombre: str
                - participantes: list of dicts with:
                    - persona_id: UUID
                    - rol: str (default JUGADOR)
                    - talle_camiseta: str | None
                    - notas: str | None
            fusion_promocion_id: Optional UUID of fusion Promocion.
            accepted_bases: Whether the responsible accepted the event bases.
            fitness_declaration: Whether the responsible declared fitness.
            image_consent: Whether the responsible consented to image usage.

        Returns:
            The created Inscripcion instance.

        Raises:
            EventoNotFoundError: If no active event can be resolved.
            PaqueteNotFoundError: If package not found.
            DisciplinaNoEnPaqueteError: If a discipline is not in the package.
            EquipoDuplicadoError: If two teams for the same discipline.
            ParticipacionDuplicadaError: If R11 violation.
            CupoExcedidoError: If package capacity exceeded.
        """
        # Use asyncio.to_thread to run the sync method in a thread pool.
        # asyncio.to_thread properly propagates thread-local context including
        # Django's transaction.atomic() state (which uses _thread_locals).
        # The @transaction.atomic() decorator on _crear_inscripcion_sync
        # opens the transaction in the worker thread where ORM calls run.
        return await asyncio.to_thread(
            self._crear_inscripcion_sync,
            responsable_id=responsable_id,
            paquete_id=paquete_id,
            promocion_id=promocion_id,
            observacion=observacion,
            equipos_data=equipos_data,
            fusion_promocion_id=fusion_promocion_id,
            accepted_bases=accepted_bases,
            fitness_declaration=fitness_declaration,
            image_consent=image_consent,
        )

    def _resolver_evento_activo(self) -> Evento:
        """
        Resolve the active event from the configured constant.

        Returns the single active event whose name matches
        `settings.EVENTO_ACTIVO_NOMBRE`. If none matches, falls back to the
        unique active event. Raises `EventoNotFoundError` when the constant
        can't be resolved or `BusinessError` if more than one is active.

        Centralizes the single source of truth for the inscription event.
        """
        nombre_objetivo = getattr(settings, "EVENTO_ACTIVO_NOMBRE", None)

        queryset = Evento.objects.filter(esta_activo=True)
        evento = None
        if nombre_objetivo:
            evento = queryset.filter(nombre=nombre_objetivo).first()

        if evento is None:
            activos = list(queryset.order_by("-fecha_inicio"))
            if not activos:
                raise exc.EventoNotFoundError(
                    "No hay un evento activo configurado para inscripciones."
                )
            if len(activos) > 1:
                raise exc.DisciplinaNoEnPaqueteError(
                    "Existen varios eventos activos. Configure EVENTO_ACTIVO_NOMBRE."
                )
            evento = activos[0]

        return evento

    @transaction.atomic()
    def _crear_inscripcion_sync(
        self,
        paquete_id: str,
        responsable_id: str,
        promocion_id: str,
        observacion: str | None,
        equipos_data: list[dict],
        fusion_promocion_id: str | None = None,
        accepted_bases: bool | None = None,
        fitness_declaration: bool | None = None,
        image_consent: bool | None = None,
    ) -> Inscripcion:
        """
        Sync version with transaction.atomic — asyncio.to_thread runs this
        in a worker thread where the transaction context is active.
        """
        # ── Resolve active event from constants/settings ────────────────────
        evento = self._resolver_evento_activo()
        evento_id = str(evento.id)

        paquete = self.paquete_svc.obtener(paquete_id)
        if paquete is None:
            raise exc.PaqueteNotFoundError(f"Paquete {paquete_id} no encontrado.")

        # ── Validate discipline count matches package requirements ─────────────────
        errores_disciplinas = validators.validar_cantidad_disciplinas_paquete(paquete, equipos_data)
        if errores_disciplinas:
            raise exc.CantidadDisciplinasInvalidaError(
                " | ".join(errores_disciplinas)
            )

        # ── Create Inscripcion ───────────────────────────────────────────────
        from modules.inscripciones.domain.schemas import InscripcionCreateData
        inscripcion_data = InscripcionCreateData(
            evento_id=evento_id,
            responsable_id=responsable_id,
            paquete_id=paquete_id,
            promocion_id=promocion_id,
            fusion_promocion_id=fusion_promocion_id,
            observacion=observacion,
        )
        inscripcion = self.inscripcion_svc.crear(inscripcion_data)

        # ── Set acceptance booleans on Persona ───────────────────────────────
        self._actualizar_aceptaciones(
            responsable_id=responsable_id,
            accepted_bases=accepted_bases,
            fitness_declaration=fitness_declaration,
            image_consent=image_consent,
        )

        # ── Create equipos and participaciones ──────────────────────────────
        for equipo_data in equipos_data:
            disciplina_id = equipo_data["disciplina_id"]
            categoria_id = equipo_data.get("categoria_id")  # Optional — may be None
            nombre_equipo = equipo_data["nombre"]
            participantes = equipo_data.get("participantes", [])

            # Validate discipline is in package
            if not validators.validar_disciplina_en_paquete(paquete, disciplina_id):
                raise exc.DisciplinaNoEnPaqueteError(
                    f"La disciplina {disciplina_id} no está incluida en el paquete {paquete.nombre}."
                )

            # Create EquipoInscrito
            from modules.inscripciones.domain.schemas import EquipoCreateData
            equipo = self.equipo_svc.crear(EquipoCreateData(
                inscripcion_id=str(inscripcion.id),
                disciplina_id=disciplina_id,
                categoria_id=categoria_id,
                nombre=nombre_equipo,
            ))

            # Create ParticipacionDisciplina + ParticipanteInscripcion per participant
            for p_idx, p_data in enumerate(participantes):
                rol = p_data.get("rol", "JUGADOR")
                talle = p_data.get("talle_camiseta")
                notas = p_data.get("notas")

                # ── Resolve Persona ────────────────────────────────────────────
                persona_id = p_data.get("persona_id")

                if persona_id:
                    # Legacy mode: verify persona exists
                    persona = self.persona_core._get_persona_por_id(persona_id)
                    if persona is None:
                        raise exc.PersonaNotFoundError(persona_id)
                else:
                    # Inline mode: lookup or create by document
                    tipo_doc = p_data.get("tipoDocumento")
                    num_doc = p_data.get("numeroDocumento")
                    nombres = p_data.get("nombres", "").strip()
                    apellidos = p_data.get("apellidos", "").strip()
                    genero = p_data.get("genero")
                    telefono = p_data.get("telefono")
                    whatsapp = p_data.get("whatsapp")

                    persona = self.persona_core._get_persona_por_documento(tipo_doc, num_doc)
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
                        persona = self.persona_core._crear_persona(persona_data)
                    else:
                        # Reuse existing: update contact fields if empty and provided
                        needs_save = False
                        if telefono and not persona.telefono:
                            persona.telefono = telefono.strip()
                            needs_save = True
                        if whatsapp and not persona.whatsapp:
                            persona.whatsapp = whatsapp.strip()
                            needs_save = True
                        if needs_save:
                            persona.save()

                # ── Update Persona boolean acceptance fields ────────────────────
                acepto_bases = p_data.get("acepto_bases")
                acepto_aptitud_fisica = p_data.get("acepto_aptitud_fisica")
                acepto_imagen = p_data.get("acepto_imagen")
                if acepto_bases is not None or acepto_aptitud_fisica is not None or acepto_imagen is not None:
                    if acepto_bases is not None:
                        persona.acepto_bases = acepto_bases
                    if acepto_aptitud_fisica is not None:
                        persona.acepto_aptitud_fisica = acepto_aptitud_fisica
                    if acepto_imagen is not None:
                        persona.acepto_imagen = acepto_imagen
                    persona.save(update_fields=["acepto_bases", "acepto_aptitud_fisica", "acepto_imagen"])

                # ── Create ParticipacionDisciplina ────────────────────────────

                # Create ParticipacionDisciplina
                from modules.inscripciones.domain.schemas import ParticipacionCreateData
                participacion = self.participacion_svc.crear(ParticipacionCreateData(
                    evento_id=evento_id,
                    disciplina_id=disciplina_id,
                    persona_id=str(persona.id),
                    equipo_id=str(equipo.id),
                ))

                # Create ParticipanteInscripcion
                from modules.inscripciones.domain.schemas import ParticipanteCreateData
                self.participante_svc.crear(ParticipanteCreateData(
                    participacion_id=str(participacion.id),
                    equipo_id=str(equipo.id),
                    rol=rol,
                    talle_camiseta=talle,
                    notas=notas,
                ))

        return inscripcion
