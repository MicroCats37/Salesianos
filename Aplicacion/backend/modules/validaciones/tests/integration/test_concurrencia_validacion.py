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

from modules.validaciones.domain.constants import ResultadoValidacionChoices
from modules.validaciones.domain.models import ValidacionTicket
from modules.validaciones.domain.results.validacion_results import (
    TicketConfirmadoResult,
)
from modules.validaciones.domain.schemas.validacion_schemas import ConfirmarTicketData
from modules.validaciones.domain.services.flujos.confirmar_ticket_flujo import (
    ConfirmarTicketFlujo,
)
from modules.validaciones.tests.fixtures.validacion_fixtures import (
    consumido_de,
    listar_actas,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def confirmar_flujo(injector):
    """El flujo real del canje."""
    return injector.get(ConfirmarTicketFlujo)


# ── El escaneo simultáneo ────────────────────────────────────────────────────


async def test_dos_escaneos_simultaneos_consumen_una_sola_vez(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN dos confirmaciones simultáneas de la MISMA credencial
    WHEN  ambas compiten
    THEN  queda UN solo consumo y UN solo acta permitida (`QA-V02`)."""

    respuestas = await asyncio.gather(
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

    exitos = [
        respuesta
        for respuesta in respuestas
        if isinstance(respuesta, TicketConfirmadoResult)
    ]
    assert len(exitos) == 1, respuestas

    assert await consumido_de(ticket_entrada) == 1

    permitidas = await listar_actas(resultado=ResultadoValidacionChoices.PERMITIDO)
    assert len(permitidas) == 1
    assert permitidas[0].cantidad == 1
