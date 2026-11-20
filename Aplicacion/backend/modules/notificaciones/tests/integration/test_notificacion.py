"""El módulo `notificaciones`: trazabilidad del intento, sin proveedor.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3 paso 6, §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

`PD-08` (proveedor, plantillas, límites, reintentos y entrega) sigue
**ABIERTO** y diferido por `DEC-21`. Estos tests comprueban lo que SÍ está
decidido:

1. El intento queda **registrado** (trazabilidad) aunque no se envíe.
2. El envío se **omite** con un código explícito: no hay un fallo silencioso
   ni un envío accidental.
3. La trazabilidad es **idempotente** por `(orden_pago_id, tipo)`: un webhook
   duplicado no crea un segundo registro.
4. La incidencia persistida sólo admite **datos seguros**: nunca el texto de
   una excepción, ni un payload de proveedor, ni un secreto.
"""

import pytest

from modules.notificaciones.domain.constants import (
    CODIGO_ENVIO_FALLIDO,
    CODIGO_PROVEEDOR_NO_APROBADO,
    EstadoNotificacion,
    TipoNotificacion,
)
from modules.notificaciones.domain.services.core.notificacion_envio_core_service import (
    NotificacionEnvioCoreService,
)
from modules.notificaciones.infrastructure.services.notificador_comprador import (
    NotificadorCompradorAdapter,
)
from modules.notificaciones.models import NotificacionEnvio
from modules.pagos.domain.schemas.pago_schemas import ContextoNotificacionCompra

pytestmark = pytest.mark.django_db


@pytest.fixture
def contexto():
    """Los hechos congelados de una compra pagada."""
    return ContextoNotificacionCompra(
        orden_pago_id="11111111-1111-1111-1111-111111111111",
        persona_id="22222222-2222-2222-2222-222222222222",
        referencia="ORD-PRUEBA-0001",
        total="100.00",
        moneda="PEN",
    )


@pytest.fixture
def notificador():
    """El notificador vigente: sin proveedor aprobado."""
    return NotificadorCompradorAdapter()


# ── La trazabilidad del intento ─────────────────────────────────────────────


def test_el_intento_queda_registrado_aunque_no_se_envie(notificador, contexto):
    """GIVEN una compra pagada
    WHEN  se pide notificar al comprador
    THEN  hay un registro auditable del intento.
    """
    resultado = notificador.notificar_compra_confirmada(contexto)

    assert resultado.enviada is False
    assert resultado.omitida is True
    assert resultado.codigo == CODIGO_PROVEEDOR_NO_APROBADO
    assert NotificacionEnvio.objects.count() == 1

    registro = NotificacionEnvio.objects.get()
    assert registro.estado == EstadoNotificacion.OMITIDA
    assert registro.codigo == CODIGO_PROVEEDOR_NO_APROBADO
    assert registro.tipo == TipoNotificacion.COMPRA_CONFIRMADA
    assert registro.intentos == 1
    assert registro.enviada_en is None


def test_el_envio_se_omite_con_un_codigo_explicito(notificador, contexto):
    """El bloqueo es EXPLÍCITO: nadie cree que se envió un correo."""
    resultado = notificador.notificar_compra_confirmada(contexto)

    assert resultado.codigo == CODIGO_PROVEEDOR_NO_APROBADO
    assert resultado.omitida is True
    # Es recuperable: cuando PD-08 se ratifique, el mismo intento se rehace.
    assert resultado.recuperable is True


def test_la_trazabilidad_es_idempotente_por_orden_y_tipo(notificador, contexto):
    """GIVEN un intento ya registrado
    WHEN  se repite la notificación
    THEN  hay un SOLO registro, con el contador de intentos actualizado.
    """
    notificador.notificar_compra_confirmada(contexto)
    notificador.notificar_compra_confirmada(contexto)

    assert NotificacionEnvio.objects.count() == 1
    registro = NotificacionEnvio.objects.get()
    assert registro.intentos == 2


def test_una_incidencia_solo_guarda_datos_seguros(notificador, contexto):
    """La incidencia nunca guarda el texto de una excepción ni un payload."""
    notificador.registrar_fallo(contexto)

    registro = NotificacionEnvio.objects.get()
    assert registro.estado == EstadoNotificacion.FALLIDA
    assert registro.codigo == CODIGO_ENVIO_FALLIDO
    assert set(registro.incidencia) == {"codigo", "intento", "fecha"}
    assert "Traceback" not in str(registro.incidencia)
    assert "ERROR" not in str(registro.incidencia)


def test_el_registro_no_guarda_el_monto_ni_la_referencia_del_proveedor(
    notificador, contexto
):
    """La trazabilidad guarda hechos, no el detalle comercial de la compra."""
    notificador.notificar_compra_confirmada(contexto)

    registro = NotificacionEnvio.objects.get()
    campos = {campo.name for campo in registro._meta.get_fields()}
    assert "total" not in campos
    assert "moneda" not in campos
    assert "referencia" not in campos


def test_el_registro_es_idempotente_aunque_lleguen_dos_voltas(
    contexto,
):
    """La restricción única de la base de datos es la guarda real."""
    core = NotificacionEnvioCoreService()

    primero = core.registrar_intento(
        orden_pago_id=contexto.orden_pago_id,
        tipo=TipoNotificacion.COMPRA_CONFIRMADA,
        estado=EstadoNotificacion.OMITIDA,
        codigo=CODIGO_PROVEEDOR_NO_APROBADO,
    )
    segundo = core.registrar_intento(
        orden_pago_id=contexto.orden_pago_id,
        tipo=TipoNotificacion.COMPRA_CONFIRMADA,
        estado=EstadoNotificacion.OMITIDA,
        codigo=CODIGO_PROVEEDOR_NO_APROBADO,
    )

    assert primero.id == segundo.id
    assert NotificacionEnvio.objects.count() == 1
