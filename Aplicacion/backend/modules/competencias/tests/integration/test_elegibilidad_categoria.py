"""La CATEGORÍA es la segunda mitad de la ELEGIBILIDAD deportiva.

GIVEN  un equipo de otra categoría y un torneo de una categoría concreta
WHEN   el administrador consulta el veredicto del equipo o intenta
       incorporarlo al cuadro
THEN   el motivo es un CÓDIGO estable —`CATEGORIA_DISTINTA` o
       `CATEGORIA_NO_ASIGNADA`— y la PRECEDENCIA es determinista: el
       cliente recibe una única razón y nunca la adivina (`QA-K01`).

El veredicto lo produce el DUEÑO de la inscripción por el puerto
`IEquipoElegibleService`: este fichero NO reimplementa ninguna regla.
"""

import pytest

from modules.competencias.domain.constants import MotivoNoElegibilidad
from modules.competencias.domain.exceptions import EquipoNoElegibleError
from modules.competencias.domain.ports import IEquipoElegibleService
from modules.competencias.domain.schemas.competencias_schemas import (
    EquipoCompetenciaCreateData,
)
from modules.competencias.domain.services.flujos.cuadro_flujo import CuadroFlujo

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def elegibilidad(injector):
    """El PUERTO real de elegibilidad (adaptador sobre el dueño real)."""
    return injector.get(IEquipoElegibleService)


@pytest.fixture
def flujo(injector):
    """El flujo real del cuadro."""
    return injector.get(CuadroFlujo)


# ── El veredicto de la categoría ────────────────────────────────────────────


def test_el_equipo_de_la_misma_categoria_es_elegible(
    elegibilidad,
    equipo,
    participacion,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN un equipo de la MISMA categoría que el torneo."""
    veredicto = elegibilidad.verificar_elegibilidad(
        str(equipo.id),
        str(edicion_publicada.id),
        str(disciplina.id),
        str(categoria.id),
    )

    # THEN el veredicto lo declara ELEGIBLE y publica su categoría.
    assert veredicto.es_elegible is True
    assert veredicto.motivo == MotivoNoElegibilidad.ELEGIBLE
    assert veredicto.categoria_id == str(categoria.id)
    assert veredicto.categoria_nombre == categoria.nombre


def test_el_equipo_de_otra_categoria_no_es_elegible(
    elegibilidad,
    equipo_categoria_otra,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN un equipo de la MISMA edición y disciplina, pero de OTRA categoría."""
    veredicto = elegibilidad.verificar_elegibilidad(
        str(equipo_categoria_otra.id),
        str(edicion_publicada.id),
        str(disciplina.id),
        str(categoria.id),
    )

    # THEN el motivo es CATEGORIA_DISTINTA y el equipo no es elegible.
    assert veredicto.es_elegible is False
    assert veredicto.motivo == MotivoNoElegibilidad.CATEGORIA_DISTINTA
    # El veredicto publica la categoría REAL del equipo, para que la
    # interfaz pueda explicar el rechazo.
    assert veredicto.categoria_id == str(equipo_categoria_otra.categoria_id)
    assert veredicto.categoria_nombre == equipo_categoria_otra.categoria.nombre


def test_un_torneo_sin_categoria_no_hace_elegible_a_nadie(
    elegibilidad,
    equipo,
    participacion,
    edicion_publicada,
    disciplina,
):
    """GIVEN un torneo cuya categoría NO está asignada."""
    veredicto = elegibilidad.verificar_elegibilidad(
        str(equipo.id),
        str(edicion_publicada.id),
        str(disciplina.id),
        None,
    )

    # THEN el motivo es CATEGORIA_NO_ASIGNADA: la categoría nunca se adivina.
    assert veredicto.es_elegible is False
    assert veredicto.motivo == MotivoNoElegibilidad.CATEGORIA_NO_ASIGNADA


# ── La PRECEDENCIA es determinista ──────────────────────────────────────────


def test_la_categoria_distinta_gana_a_la_inscripcion_cancelada(
    elegibilidad,
    equipo_cancelado,
    edicion_publicada,
    disciplina,
    categoria_2,
):
    """GIVEN un equipo cuya inscripción está CANCELADA y de OTRA categoría."""
    veredicto = elegibilidad.verificar_elegibilidad(
        str(equipo_cancelado.id),
        str(edicion_publicada.id),
        str(disciplina.id),
        str(categoria_2.id),
    )

    # THEN manda la CATEGORÍA: la precedencia la publica el backend.
    assert veredicto.motivo == MotivoNoElegibilidad.CATEGORIA_DISTINTA


def test_el_listado_no_oculta_a_los_equipos_de_otra_categoria(
    elegibilidad,
    equipo_categoria_otra,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN un candidato de otra categoría."""
    veredictos = elegibilidad.listar_equipos_elegibles(
        str(edicion_publicada.id),
        str(disciplina.id),
        str(categoria.id),
    )

    # THEN el listado lo INCLUYE con su motivo: la interfaz puede explicarlo.
    motivos = {veredicto.equipo_id: veredicto.motivo for veredicto in veredictos}
    assert motivos[str(equipo_categoria_otra.id)] == (
        MotivoNoElegibilidad.CATEGORIA_DISTINTA
    )


# ── La incorporación respeta el veredicto ───────────────────────────────────


async def test_el_equipo_de_otra_categoria_no_entra_al_cuadro(
    flujo,
    competencia,
    equipo_categoria_otra,
):
    """GIVEN un equipo de OTRA categoría que el cuadro no admite."""
    from modules.competencias.domain.models import CompetenciaEquipo

    # WHEN el administrador intenta incorporarlo.
    with pytest.raises(EquipoNoElegibleError) as error:
        await flujo.incorporar_equipo(
            str(competencia.id),
            EquipoCompetenciaCreateData(
                competencia_id=str(competencia.id),
                equipo_id=str(equipo_categoria_otra.id),
                orden=1,
            ),
        )

    # THEN el dominio publica el MOTIVO y NO crea la participación.
    assert error.value.code == "EQUIPO_NO_ELEGIBLE"
    assert error.value.motivo == MotivoNoElegibilidad.CATEGORIA_DISTINTA
    assert not CompetenciaEquipo.objects.filter(
        competencia=competencia,
        equipo=equipo_categoria_otra,
    ).exists()
