"""CrearEquipoFlujo — async flow for creating an equipo."""
from asgiref.sync import sync_to_async
from django.db import transaction

from ..core.equipo_service import EquipoCoreService
from ...schemas.inscripcion_schemas import EquipoCreateData
from ...results.inscripcion_results import EquipoResult
from ...exceptions import FechaLimiteExcedidaError
from ...models import Inscripcion


class CrearEquipoFlujo:
    """Async flow for creating an equipo atomically."""

    def __init__(self, equipo_core: EquipoCoreService):
        self._equipo_core = equipo_core

    def _verificar_fecha_limite(self, inscripcion_id: str) -> None:
        """Verify that modifications are still allowed for this evento."""
        inscripcion = Inscripcion.objects.select_related("evento").get(id=inscripcion_id)
        if not inscripcion.evento.puede_modificar():
            raise FechaLimiteExcedidaError()

    @sync_to_async
    def _crear_atomico(self, data: EquipoCreateData) -> EquipoResult:
        """Create equipo in a transaction."""
        with transaction.atomic():
            # Verify fecha_limite has not been exceeded
            self._verificar_fecha_limite(data.inscripcion_id)

            eq = self._equipo_core.crear(data)
            return EquipoResult(
                id=str(eq.id),
                inscripcion_id=str(eq.inscripcion_id),
                disciplina_id=str(eq.disciplina_id),
                disciplina_nombre=eq.disciplina.nombre,
                disciplina_sigla=eq.disciplina.sigla,
                categoria_id=str(eq.categoria_id) if eq.categoria_id else None,
                categoria_nombre=eq.categoria.nombre if eq.categoria_id else None,
                nombre=eq.nombre,
                estado=eq.estado,
                created_at=eq.created_at,
            )

    async def ejecutar(self, data: EquipoCreateData) -> EquipoResult:
        """Execute the crear equipo flow."""
        return await self._crear_atomico(data)
