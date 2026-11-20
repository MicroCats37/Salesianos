"""El alta de la inscripción inicial: inscripción, equipos y compra pendiente.

GIVEN  un responsable autenticado, un paquete vigente con precio, una
       promoción y una disciplina permitida
WHEN   confirma la inscripción
THEN   se crean la INSCRIPCIÓN, sus EQUIPOS y la COMPRA PENDIENTE de los cupos
       iniciales, con el precio CONGELADO por el servidor (`FL-03` paso 3,
       `RN-C01`, `RN-C02`, `RN-I01`) y con la categoría DERIVADA de la
       promoción (`D-CAT-05`).
"""

from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.constants import EstadoCompra, OrigenCompra
from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.constants import CausaOperativaInscripcion
from modules.salesianos_fest.domain.models import Equipo, Inscripcion
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    EquipoCreateData,
    InscripcionInicialData,
)
from modules.salesianos_fest.domain.services.flujos.inscripcion_flujo import (
    InscripcionFlujo,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real de inscripciones."""
    return injector.get(InscripcionFlujo)


@pytest.fixture
def intencion(
    edicion_publicada, paquete, disciplina, persona, precio, promocion, categoria
):
    """La intención de alta de la inscripción."""
    return InscripcionInicialData(
        responsable_id=persona.id,
        edicion_id=edicion_publicada.id,
        paquete_id=paquete.id,
        promocion_id=promocion.id,
        cantidad=10,
        equipos=[
            EquipoCreateData(disciplina_id=disciplina.id, nombre="EquipoUno"),
        ],
    )


def test_el_alta_crea_la_inscripcion_sus_equipos_y_la_compra_pendiente(
    flujo, intencion, edicion_publicada, paquete, disciplina, persona, promocion
):
    """GIVEN una intención de alta válida
    WHEN  se confirma
    THEN  hay una inscripción, su equipo y una compra PENDIENTE de origen
       INSCRIPCION.
    """
    resultado = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert resultado.causa_operativa == CausaOperativaInscripcion.INSCRIPCION_CREADA
    assert Inscripcion.objects.count() == 1
    assert Equipo.objects.count() == 1

    inscripcion = Inscripcion.objects.get()
    assert inscripcion.responsable_id == persona.id
    assert inscripcion.edicion_id == edicion_publicada.id
    assert inscripcion.paquete_id == paquete.id
    assert inscripcion.promocion_id == promocion.id
    assert inscripcion.cupos_solicitados == 10

    assert Compra.objects.count() == 1
    compra = Compra.objects.get()
    assert compra.origen == OrigenCompra.INSCRIPCION
    assert compra.estado == EstadoCompra.PENDIENTE
    assert compra.persona_id == persona.id
    assert compra.referencia == f"INSCRIPCION:{inscripcion.id}:INICIAL"


def test_el_servidor_congela_el_precio_del_catalogo(
    flujo, intencion, paquete, precio
):
    """GIVEN un paquete con precio de catálogo
    WHEN  se confirma el alta
    THEN  la compra congela ESE precio y el total lo deriva el servidor
       (`RN-C02`). El cliente no impone ningún importe.

    El precio es UNITARIO (`D-CAT-01`): el total es
    `cantidad × precio_unitario`.
    """
    resultado = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert resultado.compra.total == Decimal("2500.00")
    assert resultado.compra.moneda == "PEN"
    assert resultado.compra.cantidad == 10
    assert resultado.compra.precio_unitario == Decimal("250.00")

    compra = Compra.objects.get()
    linea = compra.lineas_snapshot[0]
    assert linea["concepto_tipo"] == "PAQUETE"
    assert linea["concepto_id"] == str(paquete.id)
    assert linea["concepto_nombre"] == "Paquete competitivo"
    assert linea["cantidad"] == 10
    assert linea["precio_unitario"] == "250.00"
    assert linea["precio_aplicado"] == "250.00"


def test_la_categoria_del_equipo_la_deriva_el_servidor(
    flujo, intencion, categoria, promocion
):
    """GIVEN una promoción con categoría en la edición
    WHEN  se confirma el alta
    THEN  el equipo lleva esa categoría: el cliente declara la promoción,
       nunca la categoría (`D-CAT-05`).
    """
    async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    equipo = Equipo.objects.get()
    assert equipo.categoria_id == categoria.id

    detalle = async_to_sync(flujo.obtener_inscripcion)(
        Inscripcion.objects.get().id
    )
    assert detalle.promocion.anio == promocion.anio
    assert detalle.equipos[0].categoria_nombre == categoria.nombre


def test_el_alta_deja_la_inscripcion_lista_para_recuperar_la_compra(
    flujo, intencion, edicion_publicada, disciplina
):
    """GIVEN un alta confirmada
    WHEN  se lee el detalle de la inscripción
    THEN  la inscripción existe, con sus equipos y con su saldo en cero.
    """
    async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    detalle = async_to_sync(flujo.obtener_inscripcion)(Inscripcion.objects.get().id)

    assert detalle.edicion_nombre == edicion_publicada.nombre
    assert detalle.paquete_nombre == "Paquete competitivo"
    assert [equipo.nombre for equipo in detalle.equipos] == ["EquipoUno"]
    assert detalle.equipos[0].disciplina_nombre == disciplina.nombre
    assert detalle.cupos_solicitados == 10
    assert detalle.cupos_disponibles == 0
