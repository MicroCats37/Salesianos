"""La CONFIRMACIÓN del avance propaga al ganador y es versionada.

GIVEN  un encuentro finalizado con ganador y un destino enlazado
WHEN   el administrador CONFIRMA el avance
THEN   el ganador ocupa el slot de destino, la propagación queda REGISTRADA
       (para que una corrección posterior no pise una colocación manual) y
       un destino ya transcurrido BLOQUEA la cascada (`RN-K02`, `QA-K04`).
"""

import pytest

from modules.competencias.domain.constants import EstadoEncuentro, SlotDestino
from modules.competencias.domain.exceptions import (
    DestinoBloqueadoError,
    SlotOcupadoError,
)
from modules.competencias.domain.models import AuditoriaOperacion, Encuentro
from modules.competencias.domain.schemas.competencias_schemas import (
    AvanceData,
    EncuentroActualizarData,
    ResultadoEncuentroData,
)
from modules.competencias.domain.services.flujos.avance_flujo import AvanceFlujo
from modules.competencias.domain.services.flujos.encuentro_flujo import (
    EncuentroFlujo,
)
from modules.competencias.domain.services.flujos.resultado_flujo import (
    ResultadoFlujo,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def encuentro_flujo(injector):
    """El flujo real de edición de encuentros."""
    return injector.get(EncuentroFlujo)


@pytest.fixture
def resultado_flujo(injector):
    """El flujo real de resultado."""
    return injector.get(ResultadoFlujo)


@pytest.fixture
def avance_flujo(injector):
    """El flujo real de avance."""
    return injector.get(AvanceFlujo)


async def _preparar(
    encuentro_flujo,
    resultado_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """Deja el encuentro FINALIZADO, con ganador y con destino enlazado."""
    await encuentro_flujo.actualizar_encuentro(
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
    await encuentro_flujo.actualizar_encuentro(
        str(competencia.id),
        str(encuentro.id),
        EncuentroActualizarData(
            siguiente_encuentro_id=str(encuentro_final.id),
            slot_destino=SlotDestino.PARTICIPANTE_1,
            motivo="Enlace con la final",
        ),
        expected_version=actual.version,
    )
    actual = Encuentro.objects.get(id=encuentro.id)
    await encuentro_flujo.actualizar_encuentro(
        str(competencia.id),
        str(encuentro.id),
        EncuentroActualizarData(
            estado=EstadoEncuentro.EN_CURSO,
            motivo="Inicio del encuentro",
        ),
        expected_version=actual.version,
    )
    actual = Encuentro.objects.get(id=encuentro.id)
    await resultado_flujo.registrar(
        str(competencia.id),
        str(encuentro.id),
        ResultadoEncuentroData(
            ganador_id=str(equipo_en_cuadro.id),
            puntaje_1=3,
            puntaje_2=1,
            motivo="Registro del resultado",
        ),
        expected_version=actual.version,
    )
    return Encuentro.objects.get(id=encuentro.id)


async def test_la_confirmacion_propaga_al_ganador_al_slot_de_destino(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un encuentro finalizado con ganador y un destino enlazado."""
    origen = await _preparar(
        encuentro_flujo,
        resultado_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )

    # WHEN el administrador confirma el avance.
    resultado = await avance_flujo.confirmar(
        str(competencia.id),
        str(encuentro.id),
        AvanceData(motivo="Avance confirmado"),
        expected_version=origen.version,
    )

    # THEN el ganador ocupa el slot de destino y la propagación queda
    # registrada como tal.
    destino = Encuentro.objects.get(id=encuentro_final.id)
    assert destino.participante_1_id == equipo_en_cuadro.id
    assert destino.ganador_propagado_id == equipo_en_cuadro.id
    assert resultado.ya_aplicado is False
    assert resultado.ganador_equipo_id == str(equipo_en_cuadro.equipo_id)


async def test_la_confirmacion_deja_su_acta(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un avance confirmado."""
    from modules.competencias.domain.models.auditoria import AccionAuditada

    origen = await _preparar(
        encuentro_flujo,
        resultado_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )
    await avance_flujo.confirmar(
        str(competencia.id),
        str(encuentro.id),
        AvanceData(motivo="Avance confirmado"),
        expected_version=origen.version,
    )

    # THEN existe el acta del avance con su motivo.
    acta = AuditoriaOperacion.objects.filter(
        accion=AccionAuditada.AVANCE
    ).first()
    assert acta is not None
    assert acta.motivo == "Avance confirmado"


async def test_el_avance_confirmado_es_idempotente(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un avance YA confirmado."""
    origen = await _preparar(
        encuentro_flujo,
        resultado_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )
    await avance_flujo.confirmar(
        str(competencia.id),
        str(encuentro.id),
        AvanceData(motivo="Avance confirmado"),
        expected_version=origen.version,
    )
    version_destino = Encuentro.objects.get(id=encuentro_final.id).version
    origen = Encuentro.objects.get(id=encuentro.id)

    # WHEN se repite el mismo avance.
    resultado = await avance_flujo.confirmar(
        str(competencia.id),
        str(encuentro.id),
        AvanceData(motivo="Avance confirmado"),
        expected_version=origen.version,
    )

    # THEN el reintento NO escribe nada.
    assert resultado.ya_aplicado is True
    assert Encuentro.objects.get(id=encuentro_final.id).version == version_destino


async def test_un_destino_ya_transcurrido_bloquea_la_cascada(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un destino que YA transcurrió."""
    origen = await _preparar(
        encuentro_flujo,
        resultado_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )
    destino = Encuentro.objects.get(id=encuentro_final.id)
    destino.estado = EstadoEncuentro.FINALIZADO
    destino.save()

    # WHEN se confirma el avance.
    with pytest.raises(DestinoBloqueadoError) as error:
        await avance_flujo.confirmar(
            str(competencia.id),
            str(encuentro.id),
            AvanceData(motivo="Avance sobre un destino transcurrido"),
            expected_version=origen.version,
        )

    # THEN la cascada se rechaza y el destino NO cambia.
    assert error.value.code == "DESTINO_BLOQUEADO"
    destino = Encuentro.objects.get(id=encuentro_final.id)
    assert destino.participante_1_id is None
    assert destino.ganador_propagado_id is None


async def test_un_slot_ocupado_por_otro_equipo_se_rechaza(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un slot de destino ya ocupado por OTRO equipo."""
    origen = await _preparar(
        encuentro_flujo,
        resultado_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )
    destino = Encuentro.objects.get(id=encuentro_final.id)
    destino.participante_1 = equipo_2_en_cuadro
    destino.save()

    # WHEN se confirma el avance.
    with pytest.raises(SlotOcupadoError) as error:
        await avance_flujo.confirmar(
            str(competencia.id),
            str(encuentro.id),
            AvanceData(motivo="Avance sobre un slot ocupado"),
            expected_version=origen.version,
        )

    # THEN el backend rechaza la operación.
    assert error.value.code == "SLOT_OCUPADO"
