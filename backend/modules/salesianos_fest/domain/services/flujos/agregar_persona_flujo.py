"""AgregarPersonaFlujo — async flow for adding a person to an inscripcion."""
from asgiref.sync import sync_to_async
from django.db import transaction

from core.exceptions import NotFoundError
from modules.usuarios.domain.models.persona import Persona
from ...models import InscripcionPersona, AceptacionInscripcion, Participacion
from ...exceptions import (
    InscripcionNotFoundError,
    FechaLimiteExcedidaError,
    CupoNoAsignadoError,
    CupoAgotadoError,
    CupoContratadoExcedidoError,
)
from ...schemas.inscripcion_schemas import InscripcionPersonaCreateData


# Version actual de documento de bases (para Phase 6)
DOCUMENTO_VERSION_BASES = "BASES-SF26-2026-09-06"


class AgregarPersonaFlujo:
    """Async flow for adding a persona to an inscripcion."""

    def _verificar_fecha_limite(self, inscripcion) -> None:
        """Verify that modifications are still allowed for this evento."""
        if not inscripcion.evento.puede_modificar():
            raise FechaLimiteExcedidaError()

    def _validar_cupo_contratado(self, inscripcion, exclude_ip_id: str | None = None) -> None:
        """Validate that active preregistered participants don't exceed paid contracted capacity.

        Allows pre-registration (InscripcionPersona without Participacion) up to the
        total paid capacity (sum of cantidad from PAGADA CompraInscripcion entries).
        This check is only applied when adding without equipo_id (pool preregistro).

        If there is NO paid capacity (total_pagados == 0), the check is skipped —
        this allows pre-registration in inscriptions without any purchase yet.
        The capacity gate only fires when there IS paid capacity that could be exceeded.

        Args:
            inscripcion: The inscripcion to validate against.
            exclude_ip_id: If provided, this InscripcionPersona ID is excluded from the
                          count. Used for get_or_create scenarios where an existing
                          active InscripcionPersona is being re-registered — the count
                          should not increase for an already-counted record.
        """
        from ...services.core.asignacion_service import AsignacionCoreService
        saldo = AsignacionCoreService().calcular_saldo_inscripcion(str(inscripcion.id))
        total_pagados = saldo["pagados"]

        # Skip check if there is no paid capacity yet (inscription without purchases)
        if total_pagados == 0:
            return

        # Count active InscripcionPersona, excluding the record being re-registered
        # (get_or_create on an existing active InscripcionPersona doesn't consume new capacity)
        queryset = InscripcionPersona.objects.filter(
            inscripcion_id=str(inscripcion.id),
            estado="A",
        )
        if exclude_ip_id:
            queryset = queryset.exclude(id=exclude_ip_id)
        activos_count = queryset.count()

        # The count ALREADY includes the participant being preregistered (the
        # record is created before this gate runs), so the capacity is exceeded
        # only when the resulting count is GREATER than the paid capacity.
        # Comparing with `>=` here rejected the last free slot: with 1 paid cup
        # nobody could be preregistered, and the automatic claim of the paid
        # cup could never fire for the final slot.
        if activos_count > total_pagados:
            raise CupoContratadoExcedidoError(maximo=total_pagados)

    def _verificar_cupo_activo(self, inscripcion_persona: InscripcionPersona) -> None:
        """Verify that the InscripcionPersona has an active AsignacionCupo.

        Raises CupoNoAsignadoError if no active cup is found and the participant
        has no released right either. When the participant had a released right
        that cannot be restored (no paid capacity left), the commercial reason
        is CupoAgotadoError — the responsible must buy an amplification.
        """
        from ...services.core.asignacion_service import AsignacionCoreService

        core = AsignacionCoreService()
        inscripcion_id = str(inscripcion_persona.inscripcion_id)

        has_cup = core.obtener_asignacion_activa_por_inscripcion_persona(
            inscripcion_id=inscripcion_id,
            inscripcion_persona_id=str(inscripcion_persona.id),
        )
        if has_cup:
            return

        liberada = core.obtener_asignacion_liberada(
            inscripcion_id=inscripcion_id,
            inscripcion_persona_id=str(inscripcion_persona.id),
        )
        if liberada is not None:
            raise CupoAgotadoError()

        raise CupoNoAsignadoError()

    def _restaurar_derecho(self, inscripcion_persona: InscripcionPersona):
        """Restore a released paid right on re-entry, when capacity allows it.

        A retired participant keeps a LIBERADA AsignacionCupo: the purchase is
        still paid, so the right can be restored as long as there is paid
        capacity left. When there is none, the participant stays without a
        right (blocked in the pool) — no fictitious right is created.
        """
        from ...services.core.asignacion_service import AsignacionCoreService

        core = AsignacionCoreService()
        inscripcion_id = str(inscripcion_persona.inscripcion_id)
        liberada = core.obtener_asignacion_liberada(
            inscripcion_id=inscripcion_id,
            inscripcion_persona_id=str(inscripcion_persona.id),
        )
        if liberada is None:
            return None

        return core.reactivar_asignacion_liberada(liberada)

    def _asignar_cupo_pagado_si_hay_capacidad(self, inscripcion) -> list:
        """Materialize the paid cup of a preregistered participant.

        The preregistration IS the commercial event: the person enters the
        pool and, when the inscription still has free paid capacity, the
        backend creates the ACTIVA `AsignacionCupo` right away.

        Rules:
        - Atomic: it runs inside the preregistration transaction, so the
          person and its right are committed together (or not at all).
        - Deterministic and FIFO: it reuses the same allocator used at payment
          settlement (`asignar_cupos_a_preregistrados`), so the earliest
          preregistration is always served first and there is a single writer
          for `AsignacionCupo`.
        - Honest: when there is no paid capacity the participant stays
          preregistered WITHOUT a right — no fictitious right is ever created.
        """
        from ...services.core.asignacion_service import AsignacionCoreService
        from ...services.core.acreditacion_service import AcreditacionCoreService

        asignaciones = AsignacionCoreService().asignar_cupos_a_preregistrados(
            inscripcion_id=str(inscripcion.id),
        )
        if not asignaciones:
            return []

        acreditacion_core = AcreditacionCoreService()
        evento_id = str(inscripcion.evento_id)
        for asignacion in asignaciones:
            acreditacion_core.sync_acreditacion_desde_compras(
                evento_id=evento_id,
                persona_id=str(asignacion.inscripcion_persona.persona_id),
            )

        return asignaciones

    @sync_to_async
    def _agregar_atomico(
        self,
        data: InscripcionPersonaCreateData,
    ) -> tuple[InscripcionPersona, Participacion | None]:
        """Add persona to inscripcion in a transaction, optionally creating Participacion.

        Validation order (Phase 2):
          1. Authorization — deferred to Phase 3 (ownership/permission layer)
          2. Deadline — _verificar_fecha_limite()
          3. Inscription membership — implicit (InscripcionPersona belongs to inscripcion)
          4. Active cup check — only when equipo_id is provided (Participacion creation)
          5. R11 and roster max — handled by ParticipacionCoreService.crear()

        When equipo_id is None: creates pre-registration (InscripcionPersona only,
        no Participacion). Capacity check ensures active preregistered count does not
        exceed total paid contracted capacity. When the inscription still has free
        paid capacity, the preregistration also materializes the ACTIVA
        AsignacionCupo of the participant (same transaction, FIFO allocator).

        When equipo_id is provided: the participant ALREADY exists in the system
        (`persona_id` path) and is placed in the team atomically. The pool-first
        input guard lives in `InscripcionPersonaCreateData` and rejects the
        combination `persona_data` + `equipo_id` (a NEW person created inside a
        team) with `ParticipanteDebePreregistrarseError` (422).

        Persona resolution (XOR — exactly one of the two must be provided;
        enforced by the schema validator):
          - `data.persona_id`: look up an existing Persona by primary key.
          - `data.persona_data`: typed `PersonaInlineData`. The server looks
            up by `(tipo_documento, numero_documento)` and reuses an existing
            Persona if found; otherwise creates a new one. This makes retries
            and refreshes idempotent.

        Returns (InscripcionPersona, Participacion) where Participacion is None
        if `equipo_id` was not provided.

        Raises:
            PersonaDataRequiredError: both or neither of persona_id/persona_data
                (raised by the schema validator before reaching this method).
            ParticipanteDebePreregistrarseError: `persona_data` combined with
                `equipo_id` (raised by the schema validator before reaching this
                method).
            InscripcionNotFoundError: inscripcion_id does not exist.
            PersonaNotFoundError: persona_id does not exist (lookup path).
            FechaLimiteExcedidaError: evento.puede_modificar() is False.
            CupoContratadoExcedidoError: preregistro capacity exceeded.
            CupoNoAsignadoError: Participacion creation attempted without active cup.
        """
        with transaction.atomic():
            # Verify inscripcion exists
            from ...models import Inscripcion, Equipo
            try:
                inscripcion = Inscripcion.objects.select_related("evento").get(id=data.inscripcion_id)
            except Inscripcion.DoesNotExist:
                raise InscripcionNotFoundError()

            # 2. Verify fecha_limite has not been exceeded
            self._verificar_fecha_limite(inscripcion)

            # Resolve persona (existing UUID or inline upsert)
            if data.persona_data is not None:
                pd = data.persona_data
                persona = Persona.objects.filter(
                    tipo_documento=pd.tipo_documento,
                    numero_documento=pd.numero_documento,
                ).first()
                if persona is None:
                    persona = Persona.objects.create(
                        tipo_documento=pd.tipo_documento,
                        numero_documento=pd.numero_documento,
                        nombres=pd.nombres,
                        apellidos=pd.apellidos,
                        genero=pd.genero,
                        telefono=pd.telefono,
                        whatsapp=pd.whatsapp,
                    )
            else:
                try:
                    persona = Persona.objects.get(id=data.persona_id)  # type: ignore[arg-type]
                except Persona.DoesNotExist:
                    raise NotFoundError(
                        resource="Persona", code="PERSONA_NOT_FOUND"
                    )

            # Create or get existing InscripcionPersona
            ip, created = InscripcionPersona.objects.get_or_create(
                inscripcion_id=data.inscripcion_id,
                persona_id=str(persona.id),
                defaults={"estado": "A"},
            )
            reingreso = False
            if not created and ip.estado == "R":
                ip.estado = "A"
                ip.save()
                reingreso = True

            # Phase 4: on re-entry the released paid right is restored when the
            # paid capacity still allows it. Without capacity the participant
            # stays in the pool without a right (never a fictitious one).
            if reingreso:
                self._restaurar_derecho(ip)

            # 4. Active cup check: only required when creating Participacion (equipo_id provided)
            # Preregistro (no equipo_id) only needs capacity check (done below)
            participacion = None

            if data.equipo_id:
                # Pool-first: this branch only places an ALREADY registered
                # participant (`persona_id`). A brand-new person combined with
                # `equipo_id` is rejected by the input guard of
                # `InscripcionPersonaCreateData` (422 / PARTICIPANTE_DEBE_
                # PREREGISTRARSE) before this flow runs.
                # Verify active cup before creating Participacion
                self._verificar_cupo_activo(ip)

                from ...services.core.participacion_service import ParticipacionCoreService
                from ...schemas.inscripcion_schemas import ParticipacionCreateData

                eq = Equipo.objects.select_related("disciplina", "inscripcion").get(id=data.equipo_id)
                from ...models import Participacion

                # R11 and roster max are checked by ParticipacionCoreService.crear()
                participacion_core = ParticipacionCoreService()
                participacion_data = ParticipacionCreateData(
                    inscripcion_persona_id=str(ip.id),
                    equipo_id=str(data.equipo_id),
                    rol="J",
                    talla_camiseta="",
                    notas="",
                    estado="A",
                )
                participacion = participacion_core.crear(participacion_data)
            else:
                # 2.1: Preregistro capacity check — active InscripcionPersona count
                # must not exceed total paid contracted capacity.
                # exclude_ip_id: if get_or_create found an existing active InscripcionPersona
                # (created=False), that record was already counted in capacity so exclude it
                # from the count check. A truly new record (created=True) is counted normally.
                exclude_ip_id = str(ip.id) if not created else None
                self._validar_cupo_contratado(inscripcion, exclude_ip_id=exclude_ip_id)

                # 2.2: the preregistration claims a paid cup when the inscription
                # has free paid capacity. The person and its right are committed
                # in the same transaction, so the pool and the saldo can never
                # disagree (no "cupo pendiente de asignar" dead end).
                self._asignar_cupo_pagado_si_hay_capacidad(inscripcion)

            # Record aceptaciones if provided
            if data.aceptaciones:
                actor = data.actor_id or str(persona.id)
                for tipo in data.aceptaciones:
                    AceptacionInscripcion.objects.update_or_create(
                        inscripcion_persona=ip,
                        tipo_aceptacion=tipo,
                        defaults={
                            "documento_version": DOCUMENTO_VERSION_BASES,
                            "actor_id": actor,
                            "medio": data.medio,
                            "ip_address": data.ip_address,
                        },
                    )

            return ip, participacion

    async def ejecutar(
        self,
        data: InscripcionPersonaCreateData,
    ) -> tuple[InscripcionPersona, Participacion | None]:
        """Execute the agregar persona flow."""
        return await self._agregar_atomico(data=data)

    def __init__(self):
        pass
