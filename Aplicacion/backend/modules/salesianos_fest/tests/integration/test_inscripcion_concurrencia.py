"""Dos altas simultáneas de la MISMA inscripción: una sola inscripción.

GIVEN  dos peticiones que confirman la MISMA inscripción a la vez
WHEN   ambas compiten
THEN   queda UNA inscripción y UNA compra: la autoridad es la restricción
       única de la base de datos, no una comprobación de aplicación
       (`RN-I03`, `RN-C06`).

Este test usa `transaction=True`: con la base en memoria compartida, cada
conexión ve los datos ya confirmados, que es lo que ocurre en producción.
"""

import asyncio

import pytest
from django.db import IntegrityError

from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.models import Equipo, Inscripcion
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    EquipoCreateData,
    InscripcionInicialData,
)
from modules.salesianos_fest.domain.services.flujos.inscripcion_flujo import (
    InscripcionFlujo,
)

pytestmark = pytest.mark.django_db(transaction=True)


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


def test_la_base_de_datos_rechaza_la_inscripcion_duplicada(
    edicion_publicada, paquete, disciplina, persona, promocion
):
    """GIVEN una inscripción viva · WHEN se inserta la misma combinación ·
    THEN la base de datos lo rechaza: la restricción única es la autoridad.
    """
    Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable=persona,
        paquete=paquete,
        promocion=promocion,
        referencia="INS-GANADORA",
        cupos_solicitados=10,
    )

    with pytest.raises(IntegrityError):
        Inscripcion.objects.create(
            edicion=edicion_publicada,
            responsable=persona,
            paquete=paquete,
            promocion=promocion,
            referencia="INS-PERDEDORA",
            cupos_solicitados=10,
        )


def test_la_carrera_perdida_reutiliza_la_inscripcion_ganadora(
    flujo, intencion, edicion_publicada, paquete, disciplina, persona, promocion
):
    """GIVEN que otra petición YA creó la inscripción
    WHEN  esta petición confirma la misma inscripción
    THEN  devuelve ESA inscripción y no crea una segunda.
    """
    ganadora = Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable=persona,
        paquete=paquete,
        promocion=promocion,
        referencia="INS-GANADORA",
        cupos_solicitados=10,
    )

    resultado = asyncio.run(_alta(flujo, intencion))

    assert resultado.inscripcion.id == str(ganadora.id)
    assert Inscripcion.objects.count() == 1


def test_dos_altas_simultaneas_no_duplican(flujo, intencion):
    """GIVEN dos peticiones simultáneas con la misma inscripción
    WHEN  ambas confirman
    THEN  queda UNA inscripción y UNA compra (`RN-C06`).
    """
    async def _simultaneas():
        return await asyncio.gather(
            flujo.crear_inscripcion_inicial(intencion),
            flujo.crear_inscripcion_inicial(intencion),
            return_exceptions=True,
        )

    respuestas = asyncio.run(_simultaneas())

    fallidas = [
        respuesta
        for respuesta in respuestas
        if isinstance(respuesta, Exception)
    ]
    assert not fallidas, fallidas

    assert Inscripcion.objects.count() == 1
    assert Equipo.objects.count() == 1
    assert Compra.objects.count() == 1


async def _alta(flujo, intencion):
    """Ejecuta el alta en el bucle de eventos actual."""
    return await flujo.crear_inscripcion_inicial(intencion)
