"""La consola de validación: vista previa, canje y auditoría.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` · `RN-P06` · `RN-P07` · `QA-V01` · `QA-V02`

GIVEN  una credencial emitida por el módulo `validaciones`
WHEN   el operador la comprueba o la canjea
THEN   la comprobación NO consume, el canje consume UNA sola vez y ambos
       intentos quedan auditados.

**Por qué `transaction=True`.** Los flujos son ASYNC y su acceso al ORM
happens en `sync_to_async`, es decir en OTRO hilo y con OTRA conexión. Con la
base en memoria compartida y el `atomic()` que envuelve un test no
transaccional, esa conexión segunda se encuentra con el bloqueo de escritura
de la primera y SQLite responde `database table is locked`. El módulo `usuarios`
resuelve lo mismo con `django_db(transaction=True)` y tests `async def`: es el
patrón establecido del proyecto para flujos async
(`contract/django-app-architecture-contract.md` §2.1).
"""

import pytest

from modules.validaciones.domain.constants import (
    ResultadoValidacionChoices,
)
from modules.validaciones.domain.exceptions import (
    CantidadExcedidaError,
    DerechoRevocadoError,
    TicketNoEncontradoError,
    TicketYaConsumidoError,
)
from modules.validaciones.domain.models import ValidacionTicket
from modules.validaciones.domain.results.validacion_results import (
    TicketConfirmadoResult,
)
from modules.validaciones.domain.schemas.validacion_schemas import (
    ConfirmarTicketData,
    PreviewTicketData,
)
from modules.validaciones.domain.services.flujos.confirmar_ticket_flujo import (
    ConfirmarTicketFlujo,
)
from modules.validaciones.domain.services.flujos.preview_ticket_flujo import (
    PreviewTicketFlujo,
)
from modules.validaciones.tests.fixtures.validacion_fixtures import (
    consumido_de,
    contar_actas,
    listar_actas,
    primera_acta,
    revocar,
)

pytestmark = pytest.mark.django_db(transaction=True)


# ── Servicios ────────────────────────────────────────────────────────────────


@pytest.fixture
def preview_flujo(injector):
    """El flujo real de la vista previa."""
    return injector.get(PreviewTicketFlujo)


@pytest.fixture
def confirmar_flujo(injector):
    """El flujo real del canje."""
    return injector.get(ConfirmarTicketFlujo)


async def _preview(flujo, codigo):
    return await flujo._preview(PreviewTicketData(codigo=codigo))


async def _confirmar(flujo, actor, codigo, clave, cantidad=None):
    return await flujo._confirmar(
        str(actor.id),
        None,
        ConfirmarTicketData(
            codigo=codigo,
            idempotency_key=clave,
            cantidad=cantidad,
        ),
    )


# ── La vista previa NO consume ───────────────────────────────────────────────


async def test_la_vista_previa_no_escribe_nada(preview_flujo, ticket_entrada):
    """GIVEN una credencial vigente · WHEN se comprueba · THEN no se escribe.

    Escanear NO es usar (`RN-P06`): ni el derecho ni la auditoría cambian.
    """
    resultado = await _preview(preview_flujo, ticket_entrada.codigo)

    assert resultado.puede_canjear is True
    assert resultado.cantidad_disponible == 1
    assert resultado.cantidad_consumida == 0
    assert resultado.motivo_codigo is None

    assert await consumido_de(ticket_entrada) == 0
    assert await contar_actas() == 0


async def test_la_vista_previa_de_una_credencial_inexistente_falla(
    preview_flujo, ticket_entrada
):
    """GIVEN un código que no existe · WHEN se comprueba · THEN 404."""
    with pytest.raises(TicketNoEncontradoError):
        await _preview(preview_flujo, "FEST-NO-EXISTE")


async def test_la_vista_previa_de_una_credencial_revocada_no_puede_canjearse(
    preview_flujo, ticket_entrada_revocado
):
    """GIVEN una credencial revocada · WHEN se comprueba · THEN no se canjea."""
    resultado = await _preview(preview_flujo, ticket_entrada_revocado.codigo)

    assert resultado.puede_canjear is False
    assert resultado.motivo_codigo == "CREDENCIAL_REVOCADA"
    assert resultado.motivo_mensaje


# ── El canje consume UNA sola vez ───────────────────────────────────────────


async def test_el_canje_consume_el_derecho_y_deja_acta(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN una credencial vigente · WHEN se confirma · THEN consume y audita."""
    resultado = await _confirmar(
        confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-1"
    )

    assert isinstance(resultado, TicketConfirmadoResult)
    assert resultado.cantidad_consumida == 1
    assert resultado.cantidad_restante == 0
    assert resultado.repetido is False

    assert await consumido_de(ticket_entrada) == 1

    actas = await listar_actas()
    assert len(actas) == 1
    acta = actas[0]
    assert acta.resultado == ResultadoValidacionChoices.PERMITIDO
    assert acta.cantidad == 1
    assert acta.actor_usuario_id == usuario_admin.id
    assert acta.operacion == ticket_entrada.operacion


async def test_la_repeticion_de_la_misma_clave_devuelve_el_mismo_resultado(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN un canje hecho · WHEN se repite con la MISMA clave · THEN se
    devuelve el mismo resultado y NO se consume otra vez (`FR-04` §2.2)."""
    primero = await _confirmar(
        confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-2"
    )
    segundo = await _confirmar(
        confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-2"
    )

    assert primero.validacion_id == segundo.validacion_id
    assert segundo.repetido is True
    assert await contar_actas() == 1

    assert await consumido_de(ticket_entrada) == 1


async def test_el_segundo_uso_con_otra_clave_se_deniega_y_se_audita(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN un ticket ya canjeado · WHEN se vuelve a canjear · THEN se
    deniega y el intento queda en el historial (`QA-V01` · `RN-P07`)."""
    await _confirmar(confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-3")

    with pytest.raises(TicketYaConsumidoError):
        await _confirmar(
            confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-4"
        )

    assert await consumido_de(ticket_entrada) == 1

    denegada = await primera_acta(
        resultado=ResultadoValidacionChoices.DENEGADO
    )
    assert denegada is not None
    assert denegada.cantidad == 0
    assert denegada.motivo_codigo == "TICKET_YA_CONSUMIDO"


async def test_la_clave_reutilizada_con_otra_carga_se_deniega(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN un canje hecho · WHEN se repite la clave con otra cantidad ·
    THEN es un error del cliente (`FR-04` §2.2)."""
    from modules.validaciones.domain.exceptions import IdempotencyKeyReutilizadaError

    await _confirmar(
        confirmar_flujo,
        usuario_admin,
        ticket_entrada.codigo,
        "clave-xct01-5",
        cantidad=1,
    )
    with pytest.raises(IdempotencyKeyReutilizadaError):
        await _confirmar(
            confirmar_flujo,
            usuario_admin,
            ticket_entrada.codigo,
            "clave-xct01-5",
            cantidad=2,
        )


async def test_el_canje_de_un_derecho_revocado_se_deniega(
    confirmar_flujo, ticket_entrada, usuario_admin, beneficiario_pase
):
    """GIVEN un derecho revocado · WHEN se canjea · THEN se deniega."""
    from modules.salesianos_fest.domain.constants import EstadoDerechoPase

    await revocar(beneficiario_pase, EstadoDerechoPase.REVOCADO)

    with pytest.raises(DerechoRevocadoError):
        await _confirmar(
            confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-6"
        )

    denegada = await primera_acta(
        resultado=ResultadoValidacionChoices.DENEGADO
    )
    assert denegada is not None
    assert denegada.motivo_codigo == "DERECHO_REVOCADO"


async def test_la_cantidad_excedente_se_deniega(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN un derecho de una unidad · WHEN se piden dos · THEN se deniega."""
    with pytest.raises(CantidadExcedidaError):
        await _confirmar(
            confirmar_flujo,
            usuario_admin,
            ticket_entrada.codigo,
            "clave-xct01-7",
            cantidad=2,
        )

    assert await consumido_de(ticket_entrada) == 0
