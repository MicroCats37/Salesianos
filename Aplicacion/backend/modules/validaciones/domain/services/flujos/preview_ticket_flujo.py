"""`PreviewTicketFlujo` — la vista previa de una credencial.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` §2.1 · `RN-P06`

**ES UNA LECTURA.** No muta, no consume, no crea registro de validación y no
abre transacción (`FR-05` §2.1). Escanear NO es usar: la credencial sigue
intacta después de la vista previa.

El veredicto (`puede_canjear`, `motivo_codigo`, `motivo_mensaje`) lo publica
el MÓDULO DUEÑO del derecho: este flujo no reimplementa ninguna regla
(`FR-05` §1, §5).
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.validaciones.domain.constants import EstadoTicketChoices
from modules.validaciones.domain.exceptions import TicketNoEncontradoError
from modules.validaciones.domain.results.validacion_results import (
    TicketPreviewResult,
)
from modules.validaciones.domain.schemas.validacion_schemas import PreviewTicketData
from modules.validaciones.domain.selectors.ticket_selector import (
    TicketSelector,
    referencia_de,
)
from modules.validaciones.infrastructure.services import RegistroVerificadoresDerecho

#: El motivo por el que una CREDENCIAL revocada no se puede canjear.
#:
#: Es la regla del PROPIO módulo de validaciones sobre su propia credencial
#: (no del dueño del derecho), y por eso vive aquí.
MOTIVO_CREDENCIAL_REVOCADA = "La credencial fue revocada."


class PreviewTicketFlujo:
    """El flujo async de la vista previa."""

    @inject
    def __init__(
        self,
        selector: TicketSelector | None = None,
        registro: RegistroVerificadoresDerecho | None = None,
    ):
        self.selector = selector or TicketSelector()
        self.registro = registro or RegistroVerificadoresDerecho()

    async def _preview(self, data: PreviewTicketData) -> TicketPreviewResult:
        """La vista previa de la credencial indicada."""
        return await sync_to_async(self._preview_sync)(data)

    def _preview_sync(self, data: PreviewTicketData) -> TicketPreviewResult:
        """El cuerpo sync de la vista previa. NO escribe nada."""
        ticket = self.selector.obtener_por_codigo(data.codigo)
        if ticket is None:
            raise TicketNoEncontradoError()

        verificador = self.registro.verificador_de(ticket.tipo_derecho)
        verificacion = verificador.resolver(referencia_de(ticket))

        puede_canjear = verificacion.puede_canjear
        motivo_codigo = verificacion.motivo_codigo
        motivo_mensaje = verificacion.motivo_mensaje

        if puede_canjear and ticket.estado != EstadoTicketChoices.VIGENTE:
            puede_canjear = False
            motivo_codigo = "CREDENCIAL_REVOCADA"
            motivo_mensaje = MOTIVO_CREDENCIAL_REVOCADA

        return TicketPreviewResult(
            tipo_derecho=verificacion.tipo_derecho,
            codigo=verificacion.codigo,
            titular=verificacion.titular,
            edicion_id=verificacion.edicion_id,
            estado=verificacion.estado,
            cantidad_total=verificacion.cantidad_total,
            cantidad_disponible=verificacion.cantidad_disponible,
            cantidad_consumida=verificacion.cantidad_consumida,
            puede_canjear=puede_canjear,
            motivo_codigo=motivo_codigo,
            motivo_mensaje=motivo_mensaje,
        )


__all__ = [
    "MOTIVO_CREDENCIAL_REVOCADA",
    "PreviewTicketFlujo",
]
