"""El catálogo de disciplinas de inscripción: por edición y sólo activas.

GIVEN  una edición publicada con sus disciplinas
WHEN   se consulta el catálogo de disciplinas
THEN   devuelve las disciplinas ACTIVAS de ESA edición — y nada de otra
       edición ni las Retireadas (`RN-E01`, `RN-I05`).

El nombre del archivo lleva "inscripcion" para que el comando focalizado del
paquete (`-k "paquete or inscripcion"`) lo cubra.
"""

import pytest
from asgiref.sync import async_to_sync

from modules.salesianos_fest.domain.services.flujos.catalogo_flujo import CatalogoFlujo

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real del catálogo."""
    return injector.get(CatalogoFlujo)


def test_el_catalogo_publica_las_disciplinas_activas_de_la_edicion(
    flujo, edicion_publicada, disciplina, disciplina_inactiva
):
    """GIVEN una disciplina activa y una inactiva de la MISMA edición
    WHEN  se consulta el catálogo de disciplinas
    THEN  sólo se publica la activa.
    """
    resultado = async_to_sync(flujo.listar_disciplinas)(edicion_publicada.id)

    assert [publicada.nombre for publicada in resultado.disciplinas] == ["Vóley Mixto"]
    assert resultado.disciplinas[0].estado == "ACTIVA"
    assert resultado.disciplinas[0].modalidad == "MIXTO"
    assert resultado.disciplinas[0].minimo_por_equipo == 5
    assert resultado.disciplinas[0].maximo_por_equipo == 12
    assert resultado.edicion_id == str(edicion_publicada.id)


def test_el_catalogo_de_disciplinas_no_mezcla_ediciones(
    flujo, edicion_publicada, edicion_otra, disciplina, disciplina_otra_edicion
):
    """GIVEN disciplinas de DOS ediciones
    WHEN  se consulta el catálogo de una de ellas
    THEN  sólo aparecen las de esa edición.
    """
    resultado = async_to_sync(flujo.listar_disciplinas)(edicion_otra.id)

    assert [publicada.nombre for publicada in resultado.disciplinas] == [
        "Fútbol de Otro FEST"
    ]

    resultado_publicada = async_to_sync(flujo.listar_disciplinas)(edicion_publicada.id)
    assert [publicada.nombre for publicada in resultado_publicada.disciplinas] == [
        "Vóley Mixto"
    ]
