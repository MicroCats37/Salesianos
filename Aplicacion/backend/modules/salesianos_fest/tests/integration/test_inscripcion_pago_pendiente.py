"""Una compra PENDIENTE no habilita ningún cupo (`RN-I02`, `QA-I01`).

GIVEN  una inscripción inicial recién creada
WHEN   se mira su saldo y su compra
THEN   los cupos PAGADOS son cero, los DISPONIBLES son cero y la compra
       sigue PENDIENTE: comprar no es habilitar.
"""

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.constants import EstadoCompra
from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.models import Inscripcion
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
def inscripcion_creada(flujo, edicion_publicada, paquete, disciplina, persona, precio):
    """Una inscripción inicial ya creada (con su compra pendiente)."""
    intencion = InscripcionInicialData(
        responsable_id=persona.id,
        edicion_id=edicion_publicada.id,
        paquete_id=paquete.id,
        equipos=[
            EquipoCreateData(disciplina_id=disciplina.id, nombre="EquipoUno"),
        ],
    )
    async_to_sync(flujo.crear_inscripcion_inicial)(intencion)
    return Inscripcion.objects.get()


def test_la_inscripcion_nace_con_cero_cupos_pagados(inscripcion_creada):
    """GIVEN una inscripción recién creada
    WHEN  se mira su saldo
    THEN  no hay ningún cupo pagado ni disponible.
    """
    inscripcion_creada.refresh_from_db()

    assert inscripcion_creada.cupos_pagados == 0
    assert inscripcion_creada.cupos_asignados == 0
    assert inscripcion_creada.cupos_solicitados == 10


def test_el_saldo_disponible_es_cero_mientras_el_pago_pendiente(
    flujo, inscripcion_creada
):
    """GIVEN una inscripción con compra PENDIENTE
    WHEN  se consulta su detalle
    THEN  el saldo disponible es CERO: el saldo lo calcula el servidor y
       una compra no pagada no aporta ningún cupo.
    """
    detalle = async_to_sync(flujo.obtener_inscripcion)(inscripcion_creada.id)

    assert detalle.cupos_pagados == 0
    assert detalle.cupos_asignados == 0
    assert detalle.cupos_disponibles == 0


def test_la_compra_queda_pendiente_y_es_recuperable(inscripcion_creada):
    """GIVEN una inscripción creada
    WHEN  se mira su compra
    THEN  la compra sigue PENDIENTE con su orden de pago: cerrar el checkout
       NO cancela y la compra es recuperable (`RN-C03`, `FR-04` I-5).
    """
    compra = Compra.objects.get()

    assert compra.estado == EstadoCompra.PENDIENTE
    assert compra.orden_pago_id is not None
    assert compra.total > 0


def test_la_inscripcion_sobrevive_a_un_pago_no_verificado(flujo, inscripcion_creada):
    """GIVEN una inscripción con compra pendiente
    WHEN  se vuelve a leer la inscripción
    THEN  sigue viva y consultable: el hecho de la inscripción NO depende
       del pago.
    """
    detalle = async_to_sync(flujo.obtener_inscripcion)(inscripcion_creada.id)

    assert detalle.id == str(inscripcion_creada.id)
    assert detalle.estado == "CREADA"
