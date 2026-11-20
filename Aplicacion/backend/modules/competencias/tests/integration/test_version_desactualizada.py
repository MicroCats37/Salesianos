"""Una versión OBSOLETA se rechaza y NO se aplica ningún cambio.

GIVEN  un recurso que otro administrador ya modificó
WHEN   el cliente envía una versión que ya no es la actual
THEN   el backend responde `RESOURCE_CHANGED` (409) y NO escribe nada:
        el cliente recarga y reintenta (`frontend/05` §5, `QA-K05`).
"""

import pytest

from modules.competencias.domain.constants import EstadoEncuentro
from modules.competencias.domain.exceptions import VersionDesactualizadaError
from modules.competencias.domain.models import (
    AuditoriaOperacion,
    CompetenciaEquipo,
    Encuentro,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    EncuentroActualizarData,
    ResultadoEncuentroData,
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


async def test_la_edicion_con_version_obsoleta_se_rechaza(
    flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
):
    """GIVEN un encuentro cuya versión conocida ya no es la actual."""
    version_obsoleta = encuentro.version

    # WHEN otro administrador modifica el encuentro.
    await flujo.actualizar_encuentro(
        str(competencia.id),
        str(encuentro.id),
        EncuentroActualizarData(
            participante_1_id=str(equipo_en_cuadro.id),
            motivo="Primera modificación",
        ),
        expected_version=version_obsoleta,
    )

    # WHEN el cliente vuelve a enviar la versión OBSOLETA.
    with pytest.raises(VersionDesactualizadaError) as error:
        await flujo.actualizar_encuentro(
            str(competencia.id),
            str(encuentro.id),
            EncuentroActualizarData(
                participante_2_id=str(equipo_en_cuadro.id),
                motivo="Segunda modificación obsoleta",
            ),
            expected_version=version_obsoleta,
        )

    # THEN el backend lo rechaza con `RESOURCE_CHANGED` y NO escribe.
    assert error.value.code == "RESOURCE_CHANGED"
    actual = Encuentro.objects.get(id=encuentro.id)
    assert actual.participante_2_id is None
    assert actual.version == version_obsoleta + 1


async def test_la_version_obsoleta_no_deja_acta(
    flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
):
    """GIVEN un comando rechazado por versión obsoleta."""
    version_obsoleta = encuentro.version
    await flujo.actualizar_encuentro(
        str(competencia.id),
        str(encuentro.id),
        EncuentroActualizarData(
            participante_1_id=str(equipo_en_cuadro.id),
            motivo="Primera modificación",
        ),
        expected_version=version_obsoleta,
    )
    actas = AuditoriaOperacion.objects.count()

    # WHEN se repite con la versión obsoleta.
    with pytest.raises(VersionDesactualizadaError):
        await flujo.actualizar_encuentro(
            str(competencia.id),
            str(encuentro.id),
            EncuentroActualizarData(
                participante_2_id=str(equipo_en_cuadro.id),
                motivo="Modificación obsoleta",
            ),
            expected_version=version_obsoleta,
        )

    # THEN no hay acta nueva: la operación NO ocurrió.
    assert AuditoriaOperacion.objects.count() == actas


async def test_la_edicion_de_equipo_con_version_obsoleta_se_rechaza(
    injector,
    competencia,
    equipo_en_cuadro,
):
    """GIVEN la participación de un equipo en el cuadro."""
    from modules.competencias.domain.exceptions import VersionDesactualizadaError as _Error
    from modules.competencias.domain.schemas.competencias_schemas import (
        EquipoCompetenciaEditData,
    )
    from modules.competencias.domain.services.flujos.cuadro_flujo import CuadroFlujo

    flujo = injector.get(CuadroFlujo)
    version_obsoleta = equipo_en_cuadro.version

    # WHEN se edita con una versión que ya no es la actual.
    with pytest.raises(_Error) as error:
        await flujo.editar_equipo(
            str(competencia.id),
            str(equipo_en_cuadro.id),
            EquipoCompetenciaEditData(orden=7),
            expected_version=version_obsoleta - 1,
            motivo="Cambio de semilla obsoleto",
        )

    # THEN el backend lo rechaza y la participación NO cambia.
    assert error.value.code == "RESOURCE_CHANGED"
    assert (
        CompetenciaEquipo.objects.get(id=equipo_en_cuadro.id).orden
        == equipo_en_cuadro.orden
    )


async def test_el_resultado_con_version_obsoleta_se_rechaza(
    flujo,
    resultado_flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un encuentro EN CURSO con una versión ya superada."""
    await flujo.actualizar_encuentro(
        str(competencia.id),
        str(encuentro.id),
        EncuentroActualizarData(
            participante_1_id=str(equipo_en_cuadro.id),
            participante_2_id=str(equipo_2_en_cuadro.id),
            inicio_programado=jornada["inicio"],
            fin_programado=jornada["fin"],
            motivo="Programación del encuentro",
        ),
        expected_version=encuentro.version,
    )
    actual = Encuentro.objects.get(id=encuentro.id)
    await flujo.actualizar_encuentro(
        str(competencia.id),
        str(encuentro.id),
        EncuentroActualizarData(
            estado=EstadoEncuentro.EN_CURSO,
            motivo="Inicio del encuentro",
        ),
        expected_version=actual.version,
    )
    version_obsoleta = Encuentro.objects.get(id=encuentro.id).version - 1

    # WHEN se registra el resultado con la versión obsoleta.
    with pytest.raises(VersionDesactualizadaError) as error:
        await resultado_flujo.registrar(
            str(competencia.id),
            str(encuentro.id),
            ResultadoEncuentroData(
                ganador_id=str(equipo_en_cuadro.id),
                motivo="Resultado con versión obsoleta",
            ),
            expected_version=version_obsoleta,
        )

    # THEN el resultado NO se registra: el encuentro sigue sin ganador.
    assert error.value.code == "RESOURCE_CHANGED"
    assert Encuentro.objects.get(id=encuentro.id).ganador_id is None
