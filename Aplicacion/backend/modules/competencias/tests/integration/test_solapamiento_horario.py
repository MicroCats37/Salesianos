"""La PROGRAMACIÓN no solapa un equipo y la agenda no cambia cuando se rechaza.

GIVEN  un equipo con un encuentro ya programado
WHEN   el administrador programa otro encuentro en la misma franja
THEN   el backend RECHAZA la programación (`SOLAPAMIENTO_HORARIO`), NO
       escribe nada y la agenda queda como estaba (`RN-K03`, `QA-K02`).

Los intervalos son SEMI-ABERTOS: dos encuentros que sólo se tocan NO se
solapan. Un encuentro CANCELADO no reserva la franja del equipo.
"""

import pytest

from modules.competencias.domain.constants import EstadoEncuentro
from modules.competencias.domain.exceptions import (
    HorarioInvalidoError,
    SolapamientoHorarioError,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    EncuentroActualizarData,
)
from modules.competencias.domain.services.flujos.encuentro_flujo import (
    EncuentroFlujo,
)
from modules.competencias.domain.services.flujos.resultado_flujo import (
    ResultadoFlujo,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def flujo(injector):
    """El flujo real de edición de encuentros."""
    return injector.get(EncuentroFlujo)


@pytest.fixture
def resultado_flujo(injector):
    """El flujo real de resultado."""
    return injector.get(ResultadoFlujo)


async def _programar(flujo, competencia, encuentro, equipo_en_cuadro, jornada):
    """Programa el encuentro con el equipo indicado en la franja dada."""
    return await flujo.actualizar_encuentro(
        str(competencia.id),
        str(encuentro.id),
        EncuentroActualizarData(
            participante_1_id=str(equipo_en_cuadro.id),
            inicio_programado=jornada["inicio"],
            fin_programado=jornada["fin"],
            motivo="Programación del encuentro",
        ),
        expected_version=encuentro.version,
    )


async def test_la_programacion_valida_se_guarda(
    flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
    jornada,
):
    """GIVEN un encuentro con un equipo elegible en el cuadro."""
    # WHEN se programa en una franja del día de la competencia.
    resultado = await _programar(
        flujo,
        competencia,
        encuentro,
        equipo_en_cuadro,
        jornada,
    )

    # THEN el encuentro queda PROGRAMADO con su horario.
    assert resultado.estado == EstadoEncuentro.PROGRAMADO
    assert resultado.inicio_programado == jornada["inicio"]
    assert resultado.fin_programado == jornada["fin"]


async def test_el_horario_debe_ser_un_intervalo_positivo(
    flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
    jornada,
):
    """GIVEN una franja cuyo fin NO es posterior a su inicio."""
    from datetime import datetime

    with pytest.raises(HorarioInvalidoError):
        await flujo.actualizar_encuentro(
            str(competencia.id),
            str(encuentro.id),
            EncuentroActualizarData(
                participante_1_id=str(equipo_en_cuadro.id),
                inicio_programado=datetime(2027, 3, 14, 12, 0),
                fin_programado=datetime(2027, 3, 14, 11, 0),
                motivo="Programación inválida",
            ),
            expected_version=encuentro.version,
        )


async def test_el_horario_debe_caer_en_el_dia_de_la_competencia(
    flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
):
    """GIVEN una franja de OTRO día."""
    from datetime import datetime

    with pytest.raises(HorarioInvalidoError):
        await flujo.actualizar_encuentro(
            str(competencia.id),
            str(encuentro.id),
            EncuentroActualizarData(
                participante_1_id=str(equipo_en_cuadro.id),
                inicio_programado=datetime(2027, 3, 15, 10, 0),
                fin_programado=datetime(2027, 3, 15, 11, 0),
                motivo="Programación fuera del día",
            ),
            expected_version=encuentro.version,
        )


async def test_el_equipo_no_se_solapa_consigo_mismo(
    flujo,
    competencia,
    ronda,
    encuentro,
    equipo_en_cuadro,
    jornada,
):
    """GIVEN un equipo que ya juega en la franja."""
    from modules.competencias.domain.models import Encuentro

    otro = Encuentro.objects.create(
        ronda=ronda,
        orden=2,
        estado=EstadoEncuentro.BORRADOR,
    )
    await _programar(flujo, competencia, encuentro, equipo_en_cuadro, jornada)

    # WHEN se programa OTRO encuentro del mismo equipo en la misma franja.
    with pytest.raises(SolapamientoHorarioError) as error:
        await _programar(flujo, competencia, otro, equipo_en_cuadro, jornada)

    # THEN el backend rechaza la operación con el código de solapamiento.
    assert error.value.code == "SOLAPAMIENTO_HORARIO"


async def test_la_agenda_no_cambia_cuando_el_solapamiento_se_rechaza(
    flujo,
    competencia,
    ronda,
    encuentro,
    equipo_en_cuadro,
    jornada,
):
    """GIVEN un equipo con un encuentro ya programado."""
    from modules.competencias.domain.models import Encuentro
    from modules.competencias.domain.selectors.encuentro_selector import (
        EncuentroSelector,
    )

    otro = Encuentro.objects.create(
        ronda=ronda,
        orden=2,
        estado=EstadoEncuentro.BORRADOR,
    )
    await _programar(flujo, competencia, encuentro, equipo_en_cuadro, jornada)

    # WHEN el segundo intento de programación es rechazado.
    with pytest.raises(SolapamientoHorarioError):
        await _programar(flujo, competencia, otro, equipo_en_cuadro, jornada)

    # THEN la agenda conserva UN solo encuentro en esa franja.
    agenda = EncuentroSelector().agenda(
        competencia.edicion_id,
        jornada["inicio"].date(),
    )
    assert agenda.total == 1


async def test_los_intervalos_que_solo_se_tocan_no_se_solapan(
    flujo,
    competencia,
    ronda,
    encuentro,
    equipo_en_cuadro,
    jornada,
):
    """GIVEN un encuentro que TERMINA cuando empieza el otro."""
    from datetime import datetime

    from modules.competencias.domain.models import Encuentro

    otro = Encuentro.objects.create(
        ronda=ronda,
        orden=2,
        estado=EstadoEncuentro.BORRADOR,
    )
    await _programar(flujo, competencia, encuentro, equipo_en_cuadro, jornada)

    # WHEN se programa el segundo justo cuando acaba el primero.
    resultado = await flujo.actualizar_encuentro(
        str(competencia.id),
        str(otro.id),
        EncuentroActualizarData(
            participante_1_id=str(equipo_en_cuadro.id),
            inicio_programado=datetime(2027, 3, 14, 11, 0),
            fin_programado=datetime(2027, 3, 14, 12, 0),
            motivo="Programación contigua",
        ),
        expected_version=otro.version,
    )

    # THEN la programación se acepta: los intervalos son semi-abiertos.
    assert resultado.estado == EstadoEncuentro.PROGRAMADO


async def test_un_encuentro_cancelado_no_reserva_la_franja(
    flujo,
    competencia,
    ronda,
    encuentro,
    equipo_en_cuadro,
    jornada,
):
    """GIVEN un encuentro CANCELADO en la franja."""
    from modules.competencias.domain.models import Encuentro

    otro = Encuentro.objects.create(
        ronda=ronda,
        orden=2,
        estado=EstadoEncuentro.CANCELADO,
        inicio_programado=jornada["inicio"],
        fin_programado=jornada["fin"],
    )
    otro.participante_1 = equipo_en_cuadro
    otro.save()

    # WHEN se programa el primer encuentro en la MISMA franja.
    resultado = await _programar(flujo, competencia, encuentro, equipo_en_cuadro, jornada)

    # THEN la franja está libre: un encuentro cancelado no la reserva.
    assert resultado.estado == EstadoEncuentro.PROGRAMADO
