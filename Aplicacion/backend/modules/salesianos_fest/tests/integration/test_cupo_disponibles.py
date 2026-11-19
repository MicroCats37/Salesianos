"""La aritmética del pool: pagados, asignados y disponibles.

GIVEN  una inscripción con capacidad pagada
WHEN   se asignan y se retiran participantes
THEN   el saldo disponible lo calcula el servidor, NUNCA es negativo y dos
       asignaciones simultáneas NO pueden sobre-suscribir el pool
       (`RN-I03`, `QA-I05`).
"""

import pytest
from asgiref.sync import async_to_sync
from django.db import IntegrityError, transaction

from modules.salesianos_fest.domain.exceptions import SinCuposDisponiblesError
from modules.salesianos_fest.domain.models import Inscripcion, Participacion
from modules.salesianos_fest.domain.schemas.pool_schemas import (
    ParticipanteAsignarData,
)
from modules.salesianos_fest.domain.services.flujos.pool_flujo import PoolFlujo

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real del pool."""
    return injector.get(PoolFlujo)


@pytest.fixture
def intencion(inscripcion, equipo, persona_participante):
    """La intención de agregar un participante al pool."""
    return ParticipanteAsignarData(
        inscripcion_id=inscripcion.id,
        persona_id=persona_participante.id,
        equipo_id=equipo.id,
    )


def test_el_pool_publica_los_tres_numeros_de_la_aritmetica(
    flujo, inscripcion
):
    """GIVEN una inscripción con 10 cupos pagados y ninguno asignado
    WHEN  se consulta el pool
    THEN  el servidor publica pagados, asignados y disponibles, y el
       disponible NUNCA es negativo (`RN-I03`).
    """
    pool = async_to_sync(flujo.obtener_pool)(inscripcion.id)

    assert pool.cupos_pagados == 10
    assert pool.cupos_asignados == 0
    assert pool.cupos_disponibles == 10
    assert pool.cupos_disponibles >= 0


def test_asignar_un_participante_consume_un_cupo(
    flujo, intencion, inscripcion
):
    """GIVEN un pool con disponibilidad
    WHEN  se agrega un participante
    THEN  el cupo asignado sube en uno y el disponible baja en uno.
    """
    async_to_sync(flujo.agregar_participante)(intencion)

    inscripcion.refresh_from_db()
    assert inscripcion.cupos_asignados == 1
    assert inscripcion.cupos_pagados == 10

    pool = async_to_sync(flujo.obtener_pool)(inscripcion.id)
    assert pool.cupos_asignados == 1
    assert pool.cupos_disponibles == 9
    assert len(pool.participaciones) == 1
    assert pool.participaciones[0].ocupa_cupo is True


def test_sin_cupos_disponibles_la_asignacion_se_rechaza(
    flujo, intencion, inscripcion
):
    """GIVEN una inscripción SIN cupos pagados
    WHEN  se intenta asignar un participante
    THEN  se rechaza con `SIN_CUPOS_DISPONIBLES` y NO se crea la
       participación: el saldo nunca se vuelve negativo (`RN-I03`).
    """
    inscripcion.cupos_pagados = 0
    inscripcion.cupos_asignados = 0
    inscripcion.save(update_fields=["cupos_pagados", "cupos_asignados"])

    with pytest.raises(SinCuposDisponiblesError):
        async_to_sync(flujo.agregar_participante)(intencion)

    assert Participacion.objects.count() == 0
    inscripcion.refresh_from_db()
    assert inscripcion.cupos_asignados == 0


def test_retirar_libera_el_cupo_sin_tocar_la_compra(
    flujo, intencion, inscripcion
):
    """GIVEN un participante asignado
    WHEN  se retira
    THEN  su cupo vuelve al pool y la COMPRA no cambia: retirar no es
       devolver dinero (`RN-I04`, `QA-I04`).
    """
    from modules.commerce.domain.models import Compra

    async_to_sync(flujo.agregar_participante)(intencion)
    participacion = Participacion.objects.get()

    pool = async_to_sync(flujo.retirar_participante)(inscripcion.id, participacion.id)

    inscripcion.refresh_from_db()
    assert inscripcion.cupos_asignados == 0
    assert inscripcion.cupos_pagados == 10
    assert pool.cupos_disponibles == 10

    # La retirada no borra: la historia de la plantilla se conserva.
    participacion.refresh_from_db()
    assert participacion.estado == "RETIRADA"
    assert participacion.retirada_en is not None
    retirada = [
        item for item in pool.participaciones if item.id == str(participacion.id)
    ]
    assert retirada[0].ocupa_cupo is False

    # Y NO hay ninguna compra: el módulo no la crea ni la modifica.
    assert Compra.objects.count() == 0


def test_la_base_de_datos_impide_sobre_suscribir_el_pool(inscripcion):
    """GIVEN una inscripción con 10 cupos pagados
    WHEN  se intenta dejar 11 asignados
    THEN  la base de datos lo rechaza: la restricción es la segunda línea
       de defensa (`RN-I03`).
    """
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Inscripcion.objects.filter(id=inscripcion.id).update(cupos_asignados=11)


def test_el_saldo_disponible_se_deriva_y_no_se_declara(flujo, inscripcion):
    """GIVEN una inscripción con 10 pagados y 4 asignados
    WHEN  se lee el saldo
    THEN  el disponible es 6: lo deriva el servidor, el cliente no resta.
    """
    inscripcion.cupos_asignados = 4
    inscripcion.save(update_fields=["cupos_asignados"])

    pool = async_to_sync(flujo.obtener_pool)(inscripcion.id)

    assert pool.cupos_disponibles == 6
    assert pool.cupos_disponibles == pool.cupos_pagados - pool.cupos_asignados
