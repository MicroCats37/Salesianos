"""El escaneo simultáneo y la entrega de la tienda.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `QA-V02` · `RN-M07`

GIVEN  dos operadores que confirman la MISMA credencial a la vez
WHEN   ambas peticiones compiten
THEN   sólo se consume la cantidad autorizada (`QA-V02`).

Este test usa `transaction=True`: con la base en memoria compartida, cada
conexión ve los datos ya confirmados, que es lo que ocurre en producción.
"""

import asyncio

import pytest

from modules.marketplace.domain.constants import EstadoEntregaPedido
from modules.marketplace.domain.models import EntregaPedido
from modules.validaciones.domain.constants import ResultadoValidacionChoices
from modules.validaciones.domain.models import ValidacionTicket
from modules.validaciones.domain.results.validacion_results import (
    TicketConfirmadoResult,
)
from modules.validaciones.domain.schemas.validacion_schemas import ConfirmarTicketData
from modules.validaciones.domain.services.flujos.confirmar_ticket_flujo import (
    ConfirmarTicketFlujo,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def confirmar_flujo(injector):
    """El flujo real del canje."""
    return injector.get(ConfirmarTicketFlujo)


# ── El escaneo simultáneo ────────────────────────────────────────────────────


def test_dos_escaneos_simultaneos_consumen_una_sola_vez(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN dos confirmaciones simultáneas de la MISMA credencial
    WHEN  ambas compiten
    THEN  queda UN solo consumo y UN solo acta permitida (`QA-V02`)."""

    async def _simultaneas():
        return await asyncio.gather(
            confirmar_flujo._confirmar(
                str(usuario_admin.id),
                None,
                ConfirmarTicketData(
                    codigo=ticket_entrada.codigo,
                    idempotency_key="clave-carrera-1",
                ),
            ),
            confirmar_flujo._confirmar(
                str(usuario_admin.id),
                None,
                ConfirmarTicketData(
                    codigo=ticket_entrada.codigo,
                    idempotency_key="clave-carrera-2",
                ),
            ),
            return_exceptions=True,
        )

    respuestas = asyncio.run(_simultaneas())

    exitos = [
        respuesta
        for respuesta in respuestas
        if isinstance(respuesta, TicketConfirmadoResult)
    ]
    assert len(exitos) == 1, respuestas

    ticket_entrada.pase_beneficiario.refresh_from_db()
    assert ticket_entrada.pase_beneficiario.cantidad_consumida == 1

    permitidas = ValidacionTicket.objects.filter(
        resultado=ResultadoValidacionChoices.PERMITIDO
    )
    assert permitidas.count() == 1
    assert permitidas.first().cantidad == 1
