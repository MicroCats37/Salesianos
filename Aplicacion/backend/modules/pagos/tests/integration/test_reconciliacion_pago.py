"""La conciliación de pagos: un cobro verificado nunca se pierde ni se duplica.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.1 I-1, §2.3, §4, §6)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

Estos tests comprueban las garantías del paquete XCT-03:

1. Un pago verificado cuya activación NO se resolvió es **recuperable**: la
   conciliación lo encuentra y lo reintenta (RN-C08).
2. El reintento **converge**: si el derecho ya estaba habilitado, no se vuelve
   a invocar al dominio (FR-04 I-2).
3. La conciliación **no revierte** el pago: la orden sigue `CONFIRMADA` y la
   compra sigue `PAGADA` pase lo que pase.
4. El veredicto de activación viaja en un canal **SEPARADO** del veredicto
   operativo: el vocabulario congelado de `EstadoOperativoPago` no se amplía
   ni se renumera (D-07, FR-01 §5.2).
"""

from datetime import datetime, timezone

import pytest

from modules.commerce.domain.constants import (
    EstadoActivacionCompra,
    EstadoCompra,
    OrigenCompra,
)
from modules.commerce.domain.models import ActivacionCompra
from modules.commerce.tests.fixtures.activacion_fakes import (  # noqa: F401
    ActivadorDominioFake,
    registro_activadores,
)
from modules.pagos.domain.constants import (
    EstadoActivacionPago,
    EstadoOperativoPago,
    EstadoOrdenPago,
)
from modules.pagos.domain.services.core.estado_operativo_pago_service import (
    EstadoOperativoPagoService,
)
from modules.pagos.domain.services.core.reconciliacion_pago_service import (
    ReconciliacionPagoService,
)

pytestmark = pytest.mark.django_db


# ── Ayudas ──────────────────────────────────────────────────────────────────


def _confirmar(orden_pago, compra):
    """Deja la orden confirmada y la compra pagada (los dos hechos)."""
    orden_pago.estado = EstadoOrdenPago.CONFIRMADA
    orden_pago.pagada_en = datetime.now(timezone.utc)
    orden_pago.save(update_fields=["estado", "pagada_en"])
    compra.estado = EstadoCompra.PAGADA
    compra.save(update_fields=["estado"])


def _activacion(compra, estado=EstadoActivacionCompra.PENDIENTE):
    """El registro de activación de la compra."""
    return ActivacionCompra.objects.create(
        compra=compra,
        origen=compra.origen,
        clave=f"activacion:{compra.origen}:{compra.id}",
        estado=estado,
    )


# ── El veredicto de activación es un canal SEPARADO ─────────────────────────


def test_el_vocabulario_del_veredicto_operativo_no_se_amplia_ni_se_renumera():
    """El veredicto operativo conserva EXACTAMENTE los ocho valores congelados."""
    assert set(EstadoOperativoPago.values) == {
        "SIN_ORDEN",
        "PAGADA",
        "PAGADA_SIN_LIQUIDAR",
        "PAGADA_SIN_EVIDENCIA",
        "PAGADA_SIN_FECHA",
        "PENDIENTE",
        "CANCELADA",
        "VENCIDA",
    }


def test_la_activacion_activada_no_cambia_el_veredicto_operativo(
    injector, orden_pago, compra
):
    """GIVEN una compra pagada con su derecho habilitado
    WHEN  se calcula el veredicto
    THEN  el veredicto operativo sigue siendo el de siempre y la activación
          viaja en su propio canal.
    """
    _confirmar(orden_pago, compra)
    _activacion(compra, EstadoActivacionCompra.ACTIVADA)

    servicio = injector.get(EstadoOperativoPagoService)

    operativo = servicio.calcular_para_orden(orden_pago)
    activacion = servicio.calcular_activacion_para_orden(orden_pago)

    # El veredicto operativo NO se amplía: el vocabulario congelado manda.
    assert operativo.codigo in EstadoOperativoPago.values
    assert activacion is not None
    assert activacion.codigo == EstadoActivacionPago.ACTIVADA
    assert activacion.recuperable is False
    assert activacion.proxima_accion == "NINGUNA"


def test_una_activacion_fallida_se_publica_como_recuperable(
    injector, orden_pago, compra
):
    """GIVEN una compra pagada cuya activación falló
    WHEN  se calcula el veredicto de activación
    THEN  se publica como fallida, recuperable, con la acción segura que sigue.
    """
    _confirmar(orden_pago, compra)
    activacion = _activacion(compra)
    activacion.estado = EstadoActivacionCompra.FALLIDA
    activacion.incidencia = {
        "codigo": "ACTIVACION_FALLIDA",
        "origen": compra.origen,
        "intento": 1,
        "fecha": "2026-11-20T00:00:00+00:00",
    }
    activacion.save(update_fields=["estado", "incidencia"])

    servicio = injector.get(EstadoOperativoPagoService)
    veredicto = servicio.calcular_activacion_para_orden(orden_pago)

    assert veredicto.codigo == EstadoActivacionPago.FALLIDA
    assert veredicto.recuperable is True
    assert veredicto.proxima_accion == "REINTENTAR_ACTIVACION"
    # El veredicto operativo no se contamina con la incidencia.
    assert servicio.calcular_para_orden(orden_pago).codigo in EstadoOperativoPago.values


# ── La conciliación recupera lo perdido y no duplica lo hecho ───────────────


def test_la_conciliacion_encuentra_un_pago_sin_derecho_habilitado(
    injector, orden_pago, compra, registro_activadores
):
    """GIVEN un pago verificado cuya activación quedó pendiente
    WHEN  se concilia
    THEN  la orden aparece en el informe y el reintento habilita el derecho.
    """
    _confirmar(orden_pago, compra)
    activador = ActivadorDominioFake()
    registro_activadores.registrar(OrigenCompra.INSCRIPCION, activador)
    _activacion(compra)

    servicio = injector.get(ReconciliacionPagoService)
    informe = servicio.conciliar(aplicar=True)

    assert informe.revisadas == 1
    assert informe.con_incidencia == 1
    assert informe.recuperadas == 1
    assert informe.pendientes == 0
    assert informe.items[0].estado_activacion == EstadoActivacionPago.ACTIVADA
    assert activador.llamadas_efectivas == 1


def test_la_conciliacion_no_revierte_el_cobro(
    injector, orden_pago, compra, registro_activadores
):
    """GIVEN un pago verificado con la activación pendiente
    WHEN  se concilia
    THEN  la orden sigue CONFIRMADA y la compra sigue PAGADA (RN-C08).
    """
    _confirmar(orden_pago, compra)
    activador = ActivadorDominioFake()
    registro_activadores.registrar(OrigenCompra.INSCRIPCION, activador)
    _activacion(compra)

    injector.get(ReconciliacionPagoService).conciliar(aplicar=True)

    orden_pago.refresh_from_db()
    compra.refresh_from_db()
    assert orden_pago.estado == EstadoOrdenPago.CONFIRMADA
    assert orden_pago.pagada_en is not None
    assert compra.estado == EstadoCompra.PAGADA


def test_la_conciliacion_converge_y_no_habilita_el_derecho_dos_veces(
    injector, orden_pago, compra, registro_activadores
):
    """GIVEN un pago verificado con el derecho YA habilitado
    WHEN  se concilia dos veces
    THEN  el dominio no se invoca otra vez (FR-04 I-2).
    """
    _confirmar(orden_pago, compra)
    activador = ActivadorDominioFake()
    registro_activadores.registrar(OrigenCompra.INSCRIPCION, activador)
    _activacion(compra, EstadoActivacionCompra.ACTIVADA)

    servicio = injector.get(ReconciliacionPagoService)
    primero = servicio.conciliar(aplicar=True)
    segundo = servicio.conciliar(aplicar=True)

    assert primero.con_incidencia == 0
    assert segundo.con_incidencia == 0
    assert activador.llamadas_efectivas == 0


def test_sin_aplicar_la_conciliacion_solo_informa_y_no_muta(
    injector, orden_pago, compra, registro_activadores
):
    """GIVEN un pago verificado con la activación pendiente
    WHEN  se concilia SIN aplicar
    THEN  nada cambia y el informe dice que no se aplicó.
    """
    _confirmar(orden_pago, compra)
    activador = ActivadorDominioFake()
    registro_activadores.registrar(OrigenCompra.INSCRIPCION, activador)
    _activacion(compra)

    servicio = injector.get(ReconciliacionPagoService)
    informe = servicio.conciliar(aplicar=False)

    assert informe.con_incidencia == 1
    assert informe.recuperadas == 0
    assert informe.items[0].aplicada is False
    activacion = ActivacionCompra.objects.get(compra=compra)
    assert activacion.estado == EstadoActivacionCompra.PENDIENTE
    assert activador.llamadas_efectivas == 0


def test_una_orden_no_confirmada_no_se_concilia(
    injector, orden_pago, compra, registro_activadores
):
    """GIVEN una orden que NO está confirmada
    WHEN  se concilia
    THEN  no aparece: sólo un pago verificado puede tener un derecho pendiente.
    """
    activador = ActivadorDominioFake()
    registro_activadores.registrar(OrigenCompra.INSCRIPCION, activador)
    _activacion(compra)

    informe = injector.get(ReconciliacionPagoService).conciliar(aplicar=True)

    assert informe.revisadas == 0
    assert informe.items == []


def test_el_fallo_del_coordinador_no_revierte_el_cobro(
    injector, orden_pago, compra, monkeypatch
):
    """GIVEN un coordinador que falla
    WHEN  se concilia con aplicación
    THEN  la incidencia queda registrada y el cobro se conserva (RN-C08).
    """
    _confirmar(orden_pago, compra)
    _activacion(compra)

    servicio = injector.get(ReconciliacionPagoService)

    def _reventar(orden_pago_id):
        raise RuntimeError("el coordinador no pudo activar")

    monkeypatch.setattr(servicio.activacion_service, "activar_por_orden", _reventar)

    informe = servicio.conciliar(aplicar=True)

    assert informe.con_incidencia == 1
    assert informe.recuperadas == 0
    assert informe.items[0].codigo == "RECONCILIACION_FALLIDA"
    assert informe.items[0].recuperable is True

    orden_pago.refresh_from_db()
    compra.refresh_from_db()
    assert orden_pago.estado == EstadoOrdenPago.CONFIRMADA
    assert compra.estado == EstadoCompra.PAGADA
