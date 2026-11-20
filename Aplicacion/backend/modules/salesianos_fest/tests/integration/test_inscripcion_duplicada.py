"""Un reintento del alta NO duplica la inscripción ni la compra.

GIVEN  una inscripción inicial ya creada
WHEN   se confirma de nuevo la MISMA inscripción
THEN   se devuelve la MISMA inscripción y su MISMA compra pendiente, sin
       duplicar equipos (`RN-I02`, `FR-04` I-4, `RN-C06`).
"""

import pytest
from asgiref.sync import async_to_sync

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


def test_el_reintento_devuelve_la_misma_inscripcion(flujo, intencion):
    """GIVEN una inscripción ya creada
    WHEN  se confirma de nuevo
    THEN  se devuelve la MISMA inscripción y la causa lo dice.
    """
    primera = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)
    segunda = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert primera.inscripcion.id == segunda.inscripcion.id
    assert (
        segunda.causa_operativa
        == CausaOperativaInscripcion.INSCRIPCION_REUTILIZADA
    )
    assert Inscripcion.objects.count() == 1


def test_el_reintento_no_crea_una_segunda_compra(flujo, intencion):
    """GIVEN una inscripción ya creada
    WHEN  se confirma de nuevo
    THEN  no hay una segunda compra: se reutiliza la pendiente.
    """
    primera = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)
    segunda = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Compra.objects.count() == 1
    assert primera.compra.compra_id == segunda.compra.compra_id
    assert segunda.compra.reutilizada is True


def test_el_reintento_no_duplica_los_equipos(flujo, intencion):
    """GIVEN una inscripción ya creada con su equipo
    WHEN  se confirma de nuevo
    THEN  no se duplica el equipo.
    """
    async_to_sync(flujo.crear_inscripcion_inicial)(intencion)
    async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Equipo.objects.count() == 1


def test_el_reintento_no_habilita_cupos(flujo, intencion):
    """GIVEN una inscripción ya creada
    WHEN  se confirma de nuevo
    THEN  los cupos siguen en cero: reintentar no es pagar.
    """
    async_to_sync(flujo.crear_inscripcion_inicial)(intencion)
    async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    inscripcion = Inscripcion.objects.get()
    assert inscripcion.cupos_pagados == 0
    assert inscripcion.cupos_asignados == 0
