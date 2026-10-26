"""ParticipacionOrchestrator — thin async facade for participacion operations."""
from asgiref.sync import sync_to_async
from injector import inject

from ..core.participacion_service import ParticipacionCoreService
from ...selectors.participacion_selector import ParticipacionSelector
from ...results.inscripcion_results import ParticipacionResult


class ParticipacionOrchestrator:
    """Thin async orchestrator — delegates to core, no business logic."""

    @inject
    def __init__(self, participacion_core: ParticipacionCoreService):
        self._participacion_core = participacion_core

    async def crear_participacion_proceso(self, data) -> ParticipacionResult:
        """Create a new participacion (with R11 and roster validation)."""
        return await self._crear_participacion_atomico(data)

    @sync_to_async
    def _crear_participacion_atomico(self, data):
        from django.db import transaction
        with transaction.atomic():
            p = self._participacion_core.crear(data)
            return ParticipacionResult(
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
                persona_numero_documento=p.inscripcion_persona.persona.numero_documento,
                rol=p.rol,
                talla_camiseta=p.talla_camiseta,
                notas=p.notas,
                estado=p.estado,
                created_at=p.created_at,
            )

    async def obter_participacion_proceso(self, participacion_id: str) -> ParticipacionResult | None:
        """Get participacion by ID."""
        return await sync_to_async(ParticipacionSelector.get_by_id)(participacion_id)

    async def listar_por_equipo_proceso(self, equipo_id: str) -> list[ParticipacionResult]:
        """List participaciones for an equipo."""
        return await sync_to_async(ParticipacionSelector.get_by_equipo)(equipo_id)

    async def mover_participacion_proceso(
        self, participacion_id: str, equipo_destino_id: str
    ) -> ParticipacionResult:
        """Move a participacion to another equipo."""
        return await self._mover_atomico(participacion_id, equipo_destino_id)

    @sync_to_async
    def _mover_atomico(self, participacion_id: str, equipo_destino_id: str):
        from django.db import transaction

        with transaction.atomic():
            p = self._participacion_core.obtener_por_id(participacion_id)
            # Cup check and roster validation are done inside mover()
            p = self._participacion_core.mover(p, equipo_destino_id)
            return ParticipacionResult(
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
                persona_numero_documento=p.inscripcion_persona.persona.numero_documento,
                rol=p.rol,
                talla_camiseta=p.talla_camiseta,
                notas=p.notas,
                estado=p.estado,
                created_at=p.created_at,
            )

    async def retirer_participacion_proceso(self, participacion_id: str) -> ParticipacionResult:
        """Retire a participacion (set estado=R)."""
        return await self._retirar_atomico(participacion_id)

    @sync_to_async
    def _retirar_atomico(self, participacion_id: str):
        from django.db import transaction
        with transaction.atomic():
            p = self._participacion_core.obtener_por_id(participacion_id)
            p = self._participacion_core.retirer(p)
            return ParticipacionResult(
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
                persona_numero_documento=p.inscripcion_persona.persona.numero_documento,
                rol=p.rol,
                talla_camiseta=p.talla_camiseta,
                notas=p.notas,
                estado=p.estado,
                created_at=p.created_at,
            )

    async def actualizar_participacion_proceso(
        self, participacion_id: str, data
    ) -> ParticipacionResult:
        """Update participacion fields (rol, talla_camiseta, notas, estado)."""
        return await self._actualizar_atomico(participacion_id, data)

    @sync_to_async
    def _actualizar_atomico(self, participacion_id: str, data):
        from django.db import transaction
        with transaction.atomic():
            p = self._participacion_core.obtener_por_id(participacion_id)
            p = self._participacion_core.actualizar(p, data)
            return ParticipacionResult(
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
                persona_numero_documento=p.inscripcion_persona.persona.numero_documento,
                rol=p.rol,
                talla_camiseta=p.talla_camiseta,
                notas=p.notas,
                estado=p.estado,
                created_at=p.created_at,
            )
