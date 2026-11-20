"""El BYE manual exige EXACTAMENTE un equipo y lo decide el administrador.

GIVEN  un encuentro del cuadro
WHEN   el administrador marca un bye manual
THEN   el bye resuelve el encuentro (su único equipo es el ganador), exige
       un motivo auditado y NUNCA lo inventa el sistema
       (`frontend/05` §4 y §6, `QA-K01`).
"""

import pytest
from asgiref.sync import async_to_sync

from modules.competencias.domain.constants import EstadoEncuentro
from modules.competencias.domain.exceptions import (
    ByeInvalidoError,
    HorarioInvalidoError,
    MotivoRequeridoError,
    TransicionInvalidaError,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    EncuentroActualizarData,
)
from modules.competencias.domain.services.flujos.encuentro_flujo import (
    EncuentroFlujo,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def flujo(injector):
    """El flujo real de edición de encuentros."""
    return injector.get(EncuentroFlujo)


def test_el_bye_manual_resuelve_el_encuentro(
    flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
):
    """GIVEN un encuentro con EXACTAMENTE un equipo."""
    # WHEN el administrador lo marca como bye manual.
    resultado = async_to_sync(flujo.actualizar_encuentro)(
        str(competencia.id),
        str(encuentro.id),
        EncuentroActualizarData(
            participante_1_id=str(equipo_en_cuadro.id),
            es_bye=True,
            motivo="Bye manual por inasistencia del rival",
        ),
        expected_version=encuentro.version,
    )

    # THEN el encuentro queda FINALIZADO y su único equipo es el ganador.
    assert resultado.es_bye is True
    assert resultado.estado == EstadoEncuentro.FINALIZADO
    assert resultado.ganador_equipo_id == str(equipo_en_cuadro.equipo_id)


def test_el_bye_sin_equipos_se_rechaza(
    flujo,
    competencia,
    encuentro,
):
    """GIVEN un encuentro SIN equipos."""
    # WHEN se marca como bye manual.
    with pytest.raises(ByeInvalidoError) as error:
        async_to_sync(flujo.actualizar_encuentro)(
            str(competencia.id),
            str(encuentro.id),
            EncuentroActualizarData(
                es_bye=True,
                motivo="Bye manual sin equipo",
            ),
            expected_version=encuentro.version,
        )

    # THEN el backend lo rechaza con su propio código.
    assert error.value.code == "BYE_INVALIDO"


def test_el_bye_con_dos_equipos_se_rechaza(
    flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
):
    """GIVEN un encuentro con DOS equipos: no es un bye."""
    with pytest.raises(ByeInvalidoError):
        async_to_sync(flujo.actualizar_encuentro)(
            str(competencia.id),
            str(encuentro.id),
            EncuentroActualizarData(
                participante_1_id=str(equipo_en_cuadro.id),
                participante_2_id=str(equipo_2_en_cuadro.id),
                es_bye=True,
                motivo="Bye manual con dos equipos",
            ),
            expected_version=encuentro.version,
        )


def test_el_bye_exige_motivo_auditado(
    flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
):
    """GIVEN un bye sin motivo auditado."""
    with pytest.raises(MotivoRequeridoError) as error:
        async_to_sync(flujo.actualizar_encuentro)(
            str(competencia.id),
            str(encuentro.id),
            EncuentroActualizarData(
                participante_1_id=str(equipo_en_cuadro.id),
                es_bye=True,
            ),
            expected_version=encuentro.version,
        )

    # THEN el motivo es obligatorio (`MOTIVO_REQUERIDO`).
    assert error.value.code == "MOTIVO_REQUERIDO"


def test_el_bye_no_se_puede_quitar_de_un_encuentro_resuelto(
    flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
):
    """GIVEN un encuentro YA resuelto como bye."""
    resultado = async_to_sync(flujo.actualizar_encuentro)(
        str(competencia.id),
        str(encuentro.id),
        EncuentroActualizarData(
            participante_1_id=str(equipo_en_cuadro.id),
            es_bye=True,
            motivo="Bye manual por inasistencia del rival",
        ),
        expected_version=encuentro.version,
    )

    # WHEN se intenta quitar el bye.
    with pytest.raises(TransicionInvalidaError):
        async_to_sync(flujo.actualizar_encuentro)(
            str(competencia.id),
            str(encuentro.id),
            EncuentroActualizarData(
                es_bye=False,
                motivo="Quitar el bye",
            ),
            expected_version=resultado.version,
        )


def test_un_encuentro_programado_no_puede_ser_bye(
    flujo,
    competencia,
    encuentro,
    equipo_en_cuadro,
    jornada,
):
    """GIVEN un encuentro YA PROGRAMADO: un bye no se juega."""
    resultado = async_to_sync(flujo.actualizar_encuentro)(
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

    # WHEN se marca como bye.
    with pytest.raises(HorarioInvalidoError):
        async_to_sync(flujo.actualizar_encuentro)(
            str(competencia.id),
            str(encuentro.id),
            EncuentroActualizarData(
                es_bye=True,
                motivo="Bye manual sobre un encuentro programado",
            ),
            expected_version=resultado.version,
        )
