"""La ELEGIBILIDAD de un equipo se resuelve por PUERTO, no por reglas duplicadas.

GIVEN  una edición, una disciplina, una categoría y equipos que compiten o no
WHEN   el administrador consulta los equipos candidatos o incorpora uno
THEN   el veredicto lo produce el DUEÑO de la inscripción
       (`modules.salesianos_fest`) y el motivo del rechazo es un CÓDIGO
       estable; el backend publica la razón y el cliente nunca la adivina
       (`RN-K01`, `QA-K01`).

Este fichero NO duplica ninguna regla de inscripción: comprueba que el
veredicto del puerto llega, que el motivo es el correcto y que el cuadro sólo
rechaza equipos fuera de su alcance competitivo.

**La CATEGORÍA es obligatoria en el veredicto** (`RN-K01`): la elegibilidad
deportiva es la coincidencia de EDICIÓN + DISCIPLINA + CATEGORÍA. El puerto
`IEquipoElegibleService` la exige en las dos operaciones (`verificar_elegibilidad`
y `listar_equipos_elegibles`) porque el torneo del que se habla TIENE una
categoría: sin ella no hay contra qué comparar y el motivo sería ambiguo.
"""

import pytest

from modules.competencias.domain.constants import MotivoNoElegibilidad
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


# ── El veredicto del puerto ─────────────────────────────────────────────────


def test_el_equipo_de_la_edicion_y_disciplina_es_elegible(
    elegibilidad,
    equipo,
    participacion,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN un equipo con roster de la edición y la disciplina del torneo."""
    veredicto = elegibilidad.verificar_elegibilidad(
        str(equipo.id),
        str(edicion_publicada.id),
        str(disciplina.id),
        str(categoria.id),
    )

    # THEN el veredicto lo declara ELEGIBLE.
    assert veredicto.es_elegible is True
    assert veredicto.motivo == MotivoNoElegibilidad.ELEGIBLE
    assert veredicto.participantes_activos == 1
    assert veredicto.minimo_requerido == disciplina.minimo_por_equipo


def test_el_equipo_de_otra_edicion_no_es_elegible(
    elegibilidad,
    equipo_otra_edicion,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN un equipo de OTRA edición."""
    veredicto = elegibilidad.verificar_elegibilidad(
        str(equipo_otra_edicion.id),
        str(edicion_publicada.id),
        str(disciplina.id),
        str(categoria.id),
    )

    # THEN el motivo es EDICION_DISTINTA y el equipo no es elegible.
    assert veredicto.es_elegible is False
    assert veredicto.motivo == MotivoNoElegibilidad.EDICION_DISTINTA


def test_el_equipo_de_otra_disciplina_no_es_elegible(
    elegibilidad,
    equipo_sin_plantilla,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN un equipo de otra disciplina de la misma edición."""
    veredicto = elegibilidad.verificar_elegibilidad(
        str(equipo_sin_plantilla.id),
        str(edicion_publicada.id),
        str(disciplina.id),
        str(categoria.id),
    )

    # THEN el motivo es DISCIPLINA_DISTINTA.
    assert veredicto.es_elegible is False
    assert veredicto.motivo == MotivoNoElegibilidad.DISCIPLINA_DISTINTA


def test_el_equipo_de_inscripcion_cancelada_no_es_elegible(
    elegibilidad,
    equipo_cancelado,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN un equipo cuya inscripción está CANCELADA."""
    veredicto = elegibilidad.verificar_elegibilidad(
        str(equipo_cancelado.id),
        str(edicion_publicada.id),
        str(disciplina.id),
        str(categoria.id),
    )

    # THEN el motivo es INSCRIPCION_CANCELADA.
    assert veredicto.es_elegible is False
    assert veredicto.motivo == MotivoNoElegibilidad.INSCRIPCION_CANCELADA


def test_el_equipo_sin_plantilla_es_elegible_para_el_cuadro(
    elegibilidad,
    equipo_sin_plantilla,
    edicion_publicada,
    disciplina_exigente,
    categoria,
):
    """GIVEN un equipo ACTIVO sin ninguna participación activa."""
    veredicto = elegibilidad.verificar_elegibilidad(
        str(equipo_sin_plantilla.id),
        str(edicion_publicada.id),
        str(disciplina_exigente.id),
        str(categoria.id),
    )

    # THEN la capacidad de plantilla no excluye al equipo del cuadro.
    assert veredicto.es_elegible is True
    assert veredicto.motivo == MotivoNoElegibilidad.ELEGIBLE


def test_el_equipo_con_plantilla_incompleta_es_elegible_para_el_cuadro(
    elegibilidad,
    equipo_plantilla_incompleta,
    participacion_plantilla_incompleta,
    edicion_publicada,
    disciplina_exigente,
    categoria,
):
    """GIVEN un equipo con MENOS participantes que el mínimo de la disciplina."""
    veredicto = elegibilidad.verificar_elegibilidad(
        str(equipo_plantilla_incompleta.id),
        str(edicion_publicada.id),
        str(disciplina_exigente.id),
        str(categoria.id),
    )

    # THEN la capacidad de plantilla no excluye al equipo del cuadro.
    assert veredicto.es_elegible is True
    assert veredicto.motivo == MotivoNoElegibilidad.ELEGIBLE
    assert veredicto.participantes_activos == 1
    assert veredicto.minimo_requerido == 3


def test_el_equipo_inexistente_tiene_su_propio_veredicto(
    elegibilidad,
    edicion_publicada,
    disciplina,
    categoria,
):
    """GIVEN un equipo que NO existe."""
    veredicto = elegibilidad.verificar_elegibilidad(
        "00000000-0000-0000-0000-000000000000",
        str(edicion_publicada.id),
        str(disciplina.id),
        str(categoria.id),
    )

    # THEN el puerto NO lanza: devuelve el veredicto EQUIPO_NO_ENCONTRADO.
    assert veredicto.es_elegible is False
    assert veredicto.motivo == MotivoNoElegibilidad.EQUIPO_NO_ENCONTRADO


def test_el_listado_devuelve_el_veredicto_de_cada_candidato(
    elegibilidad,
    equipo,
    participacion,
    equipo_sin_plantilla,
    edicion_publicada,
    disciplina,
    disciplina_exigente,
    categoria,
):
    """GIVEN candidatos elegibles y no elegibles de la misma disciplina."""
    veredictos = elegibilidad.listar_equipos_elegibles(
        str(edicion_publicada.id),
        str(disciplina.id),
        str(categoria.id),
    )

    # THEN el listado trae UN veredicto por candidato, con su motivo.
    motivos = {veredicto.equipo_id: veredicto.motivo for veredicto in veredictos}
    assert motivos[str(equipo.id)] == MotivoNoElegibilidad.ELEGIBLE


# ── La incorporación respeta el veredicto ───────────────────────────────────


async def test_el_equipo_elegible_entra_al_cuadro(
    flujo,
    competencia,
    equipo,
    participacion,
):
    """GIVEN un equipo elegible."""
    # WHEN el administrador lo incorpora con su semilla manual.
    participacion_en_cuadro = await flujo.incorporar_equipo(
        str(competencia.id),
        EquipoCompetenciaCreateData(
            competencia_id=str(competencia.id),
            equipo_id=str(equipo.id),
            orden=1,
        ),
    )

    # THEN la participación existe con su semilla y su estado ACTIVO.
    assert participacion_en_cuadro.equipo_id == str(equipo.id)
    assert participacion_en_cuadro.orden == 1
    assert participacion_en_cuadro.estado == "ACTIVO"


async def test_el_equipo_sin_plantilla_entra_al_cuadro(
    flujo,
    competencia,
    equipo_sin_plantilla,
    edicion_publicada,
    disciplina_exigente,
):
    """GIVEN un equipo sin plantilla pero del alcance de la competencia."""

    competencia.disciplina = disciplina_exigente
    competencia.save(update_fields=["disciplina"])

    # WHEN el administrador lo incorpora con una semilla manual.
    participacion = await flujo.incorporar_equipo(
        str(competencia.id),
        EquipoCompetenciaCreateData(
            competencia_id=str(competencia.id),
            equipo_id=str(equipo_sin_plantilla.id),
            orden=1,
        ),
    )

    # THEN la falta de plantilla no excluye al equipo del cuadro.
    assert participacion.equipo_id == str(equipo_sin_plantilla.id)


async def test_el_equipo_ya_incorporado_no_se_duplicate(
    flujo,
    competencia,
    equipo_en_cuadro,
    equipo,
):
    """GIVEN un equipo YA incorporado al cuadro."""
    from modules.competencias.domain.exceptions import CompetenciaEquipoDuplicadoError

    # WHEN se intenta incorporarlo de nuevo.
    with pytest.raises(CompetenciaEquipoDuplicadoError):
        await flujo.incorporar_equipo(
            str(competencia.id),
            EquipoCompetenciaCreateData(
                competencia_id=str(competencia.id),
                equipo_id=str(equipo.id),
                orden=3,
            ),
        )
