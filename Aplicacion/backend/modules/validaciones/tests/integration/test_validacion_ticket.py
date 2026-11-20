"""La consola de validación: vista previa, canje y auditoría.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` · `RN-P06` · `RN-P07` · `QA-V01` · `QA-V02`

GIVEN  una credencial emitida por el módulo `validaciones`
WHEN   el operador la comprueba o la canjea
THEN   la comprobación NO consume, el canje consume UNA sola vez y ambos
       intentos quedan auditados.
"""

import asyncio

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

pytestmark = pytest.mark.django_db


# ── Servicios ────────────────────────────────────────────────────────────────


@pytest.fixture
def preview_flujo(injector):
    """El flujo real de la vista previa."""
    return injector.get(PreviewTicketFlujo)


@pytest.fixture
def confirmar_flujo(injector):
    """El flujo real del canje."""
    return injector.get(ConfirmarTicketFlujo)


def _preview(flujo, codigo):
    return asyncio.run(flujo._preview(PreviewTicketData(codigo=codigo)))


def _confirmar(flujo, actor, codigo, clave, cantidad=None):
    return asyncio.run(
        flujo._confirmar(
            str(actor.id),
            None,
            ConfirmarTicketData(
                codigo=codigo,
                idempotency_key=clave,
                cantidad=cantidad,
            ),
        )
    )


# ── La vista previa NO consume ───────────────────────────────────────────────


def test_la_vista_previa_no_escribe_nada(preview_flujo, ticket_entrada):
    """GIVEN una credencial vigente · WHEN se comprueba · THEN no se escribe.

    Escanear NO es usar (`RN-P06`): ni el derecho ni la auditoría cambian.
    """
    resultado = _preview(preview_flujo, ticket_entrada.codigo)

    assert resultado.puede_canjear is True
    assert resultado.cantidad_disponible == 1
    assert resultado.cantidad_consumida == 0
    assert resultado.motivo_codigo is None

    ticket_entrada.pase_beneficiario.refresh_from_db()
    assert ticket_entrada.pase_beneficiario.cantidad_consumida == 0
    assert ValidacionTicket.objects.count() == 0


def test_la_vista_previa_de_una_credencial_inexistente_falla(
    preview_flujo, ticket_entrada
):
    """GIVEN un código que no existe · WHEN se comprueba · THEN 404."""
    with pytest.raises(TicketNoEncontradoError):
        _preview(preview_flujo, "FEST-NO-EXISTE")


def test_la_vista_previa_de_una_credencial_revocada_no_puede_canjearse(
    preview_flujo, ticket_entrada_revocado
):
    """GIVEN una credencial revocada · WHEN se comprueba · THEN no se canjea."""
    resultado = _preview(preview_flujo, ticket_entrada_revocado.codigo)

    assert resultado.puede_canjear is False
    assert resultado.motivo_codigo == "CREDENCIAL_REVOCADA"
    assert resultado.motivo_mensaje


# ── El canje consume UNA sola vez ───────────────────────────────────────────


def test_el_canje_consume_el_derecho_y_deja_acta(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN una credencial vigente · WHEN se confirma · THEN consume y audita."""
    resultado = _confirmar(
        confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-1"
    )

    assert isinstance(resultado, TicketConfirmadoResult)
    assert resultado.cantidad_consumida == 1
    assert resultado.cantidad_restante == 0
    assert resultado.repetido is False

    ticket_entrada.pase_beneficiario.refresh_from_db()
    assert ticket_entrada.pase_beneficiario.cantidad_consumida == 1

    actas = ValidacionTicket.objects.all()
    assert actas.count() == 1
    acta = actas.first()
    assert acta.resultado == ResultadoValidacionChoices.PERMITIDO
    assert acta.cantidad == 1
    assert acta.actor_usuario_id == usuario_admin.id
    assert acta.operacion == ticket_entrada.operacion


def test_la_repeticion_de_la_misma_clave_devuelve_el_mismo_resultado(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN un canje hecho · WHEN se repite con la MISMA clave · THEN se
    devuelve el mismo resultado y NO se consume otra vez (`FR-04` §2.2)."""
    primero = _confirmar(
        confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-2"
    )
    segundo = _confirmar(
        confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-2"
    )

    assert primero.validacion_id == segundo.validacion_id
    assert segundo.repetido is True
    assert ValidacionTicket.objects.count() == 1

    ticket_entrada.pase_beneficiario.refresh_from_db()
    assert ticket_entrada.pase_beneficiario.cantidad_consumida == 1


def test_el_segundo_uso_con_otra_clave_se_deniega_y_se_audita(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN un ticket ya canjeado · WHEN se vuelve a canjear · THEN se
    deniega y el intento queda en el historial (`QA-V01` · `RN-P07`)."""
    _confirmar(confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-3")

    with pytest.raises(TicketYaConsumidoError):
        _confirmar(confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-4")

    ticket_entrada.pase_beneficiario.refresh_from_db()
    assert ticket_entrada.pase_beneficiario.cantidad_consumida == 1

    denegada = ValidacionTicket.objects.filter(
        resultado=ResultadoValidacionChoices.DENEGADO
    ).first()
    assert denegada is not None
    assert denegada.cantidad == 0
    assert denegada.motivo_codigo == "TICKET_YA_CONSUMIDO"


def test_la_clave_reutilizada_con_otra_carga_se_deniega(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN un canje hecho · WHEN se repite la clave con otra cantidad ·
    THEN es un error del cliente (`FR-04` §2.2)."""
    from modules.validaciones.domain.exceptions import IdempotencyKeyReutilizadaError

    _confirmar(
        confirmar_flujo,
        usuario_admin,
        ticket_entrada.codigo,
        "clave-xct01-5",
        cantidad=1,
    )
    with pytest.raises(IdempotencyKeyReutilizadaError):
        _confirmar(
            confirmar_flujo,
            usuario_admin,
            ticket_entrada.codigo,
            "clave-xct01-5",
            cantidad=2,
        )


def test_el_canje_de_un_derecho_revocado_se_deniega(
    confirmar_flujo, ticket_entrada, usuario_admin, beneficiario_pase
):
    """GIVEN un derecho revocado · WHEN se canjea · THEN se deniega."""
    from modules.salesianos_fest.domain.constants import EstadoDerechoPase

    beneficiario_pase.estado = EstadoDerechoPase.REVOCADO
    beneficiario_pase.save(update_fields=["estado", "updated_at"])

    with pytest.raises(DerechoRevocadoError):
        _confirmar(
            confirmar_flujo, usuario_admin, ticket_entrada.codigo, "clave-xct01-6"
        )

    denegada = ValidacionTicket.objects.filter(
        resultado=ResultadoValidacionChoices.DENEGADO
    ).first()
    assert denegada is not None
    assert denegada.motivo_codigo == "DERECHO_REVOCADO"


def test_la_cantidad_excedente_se_deniega(
    confirmar_flujo, ticket_entrada, usuario_admin
):
    """GIVEN un derecho de una unidad · WHEN se piden dos · THEN se deniega."""
    with pytest.raises(CantidadExcedidaError):
        _confirmar(
            confirmar_flujo,
            usuario_admin,
            ticket_entrada.codigo,
            "clave-xct01-7",
            cantidad=2,
        )

    ticket_entrada.pase_beneficiario.refresh_from_db()
    assert ticket_entrada.pase_beneficiario.cantidad_consumida == 0
