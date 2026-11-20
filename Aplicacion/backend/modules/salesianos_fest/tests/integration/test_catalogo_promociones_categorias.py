"""El catálogo de promociones y categorías y la cotización de un paquete.

GIVEN  un catálogo con promociones, categorías y un paquete con precio
WHEN   se consultan los catálogos públicos y se cotiza un paquete
THEN   se publican las promociones ACTIVAS del catálogo GLOBAL, las
       categorías ACTIVAS de la edición y la cotización con el precio
       UNITARIO vigente y el total derivado por el servidor
       (`D-CAT-01`, `D-CAT-04`, `RN-C02`).
"""

from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync

from modules.salesianos_fest.domain.exceptions import CantidadInsuficienteError
from modules.salesianos_fest.domain.services.flujos.catalogo_flujo import CatalogoFlujo

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real del catálogo."""
    return injector.get(CatalogoFlujo)


def test_el_catalogo_de_promociones_es_global_y_activo(
    flujo, edicion_publicada, promocion, promocion_inactiva
):
    """GIVEN una promoción activa y otra inactiva
    WHEN  se consulta el catálogo de promociones
    THEN  sólo se publica la activa, y la EDICIÓN que scopea el catálogo va
       en el ENVOLTORIO: la promoción es GLOBAL (`D-CAT-04`).
    """
    resultado = async_to_sync(flujo.listar_promociones)(edicion_publicada.id)

    assert [publicada.anio for publicada in resultado.promociones] == [promocion.anio]
    assert resultado.promociones[0].nombre == "Junior"
    assert resultado.promociones[0].estado == "ACTIVA"
    assert resultado.edicion_id == str(edicion_publicada.id)
    assert resultado.edicion_nombre == edicion_publicada.nombre


def test_el_catalogo_de_categorias_es_por_edicion(
    flujo, edicion_publicada, edicion_otra, categoria
):
    """GIVEN una categoría de la edición publicada
    WHEN  se consulta el catálogo de categorías de otra edición
    THEN  no aparece: la categoría es de UNA EDICIÓN (`RN-E01`).
    """
    resultado = async_to_sync(flujo.listar_categorias)(edicion_publicada.id)

    assert [publicada.nombre for publicada in resultado.categorias] == ["Junior"]
    assert resultado.categorias[0].promocion_desde == 2012
    assert resultado.categorias[0].promocion_hasta == 2025
    assert resultado.edicion_id == str(edicion_publicada.id)

    resultado_otra = async_to_sync(flujo.listar_categorias)(edicion_otra.id)
    assert resultado_otra.categorias == []


def test_la_cotizacion_usa_el_precio_unitario_y_deriva_el_total(
    flujo, edicion_publicada, paquete, precio
):
    """GIVEN un paquete con precio unitario vigente
    WHEN  se cotiza para 12 participantes
    THEN  devuelve el precio UNITARIO y un total de `12 × precio`: el cliente
       no envía ningún importe (`RN-C02`).

    Devuelve además el TOKEN DE CONCURRENCIA (`version`) del precio y su
    ventana de validez.
    """
    resultado = async_to_sync(flujo.cotizar)(paquete.id, 12)

    assert resultado.minimo_cantidad == 10
    assert resultado.cantidad_cotizada == 12
    assert resultado.precio_unitario == Decimal("250.00")
    assert resultado.total == Decimal("3000.00")
    assert resultado.moneda == "PEN"
    assert resultado.version == 1
    assert resultado.estado == "ACTIVA"
    assert resultado.validez_hasta is not None


def test_la_cotizacion_exige_el_minimo_comercial(
    flujo, edicion_publicada, paquete, precio
):
    """GIVEN un paquete cuyo mínimo comercial es 10
    WHEN  se cotiza para 5 participantes
    THEN  se rechaza con `CANTIDAD_INSUFICIENTE`.
    """
    with pytest.raises(CantidadInsuficienteError):
        async_to_sync(flujo.cotizar)(paquete.id, 5)


def test_la_cotizacion_de_un_paquete_sin_precio_no_inventa_importe(
    flujo, edicion_publicada, paquete_sin_precio
):
    """GIVEN un paquete SIN precio vigente
    WHEN  se cotiza
    THEN  se rechaza con `PAQUETE_NO_VIGENTE`: no hay precio de reserva
       (`FL-01` paso 3).
    """
    from modules.salesianos_fest.domain.exceptions import PaqueteNoVigenteError

    with pytest.raises(PaqueteNoVigenteError):
        async_to_sync(flujo.cotizar)(paquete_sin_precio.id, 10)
