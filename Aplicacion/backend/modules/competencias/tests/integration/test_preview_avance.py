"""La VISTA PREVIA del avance NO ESCRIBE NADA.

GIVEN  un encuentro finalizado con ganador y un destino enlazado
WHEN   el administrador pide la vista previa del avance
THEN   el backend devuelve el efecto exacto del avance y NO escribe: ni la
       versión, ni el slot de destino, ni el acta (`QA-K04`, `RN-K02`).
"""

import pytest

from modules.competencias.domain.constants import EstadoEncuentro, SlotDestino
from modules.competencias.domain.models import AuditoriaOperacion
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


async def _preparar_encuentro_finalizado(
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
    from modules.competencias.domain.models import Encuentro

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


async def test_la_vista_previa_informa_el_efecto_del_avance(
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
    await _preparar_encuentro_finalizado(
        encuentro_flujo,
        resultado_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )

    # WHEN el administrador pide la vista previa.
    previa = await avance_flujo.previsualizar(
        str(competencia.id),
        str(encuentro.id),
    )

    # THEN la previa dice a dónde llegaría el ganador y por qué slot.
    assert previa.siguiente_encuentro_id == str(encuentro_final.id)
    assert previa.slot_destino == SlotDestino.PARTICIPANTE_1
    assert previa.ganador_equipo_id == str(equipo_en_cuadro.equipo_id)
    assert previa.ocupante_actual_equipo_id is None
    assert previa.bloqueado is False
    assert previa.puede_confirmar is True


async def test_la_vista_previa_no_escribe_nada(
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
    from modules.competencias.domain.models import Encuentro

    await _preparar_encuentro_finalizado(
        encuentro_flujo,
        resultado_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )
    version_antes = Encuentro.objects.get(id=encuentro.id).version
    destino_antes = Encuentro.objects.get(id=encuentro_final.id)
    actas_antes = AuditoriaOperacion.objects.count()

    # WHEN el administrador pide la vista previa.
    await avance_flujo.previsualizar(str(competencia.id), str(encuentro.id))

    # THEN NADA se escribe: ni versiones, ni slots, ni actas.
    assert Encuentro.objects.get(id=encuentro.id).version == version_antes
    destino_despues = Encuentro.objects.get(id=encuentro_final.id)
    assert destino_despues.participante_1_id == destino_antes.participante_1_id
    assert destino_despues.ganador_propagado_id == destino_antes.ganador_propagado_id
    assert destino_despues.version == destino_antes.version
    assert AuditoriaOperacion.objects.count() == actas_antes


async def test_la_vista_previa_de_un_destino_bloqueado_lo_dice(
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
    from modules.competencias.domain.models import Encuentro

    await _preparar_encuentro_finalizado(
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

    # WHEN se pide la vista previa.
    previa = await avance_flujo.previsualizar(
        str(competencia.id),
        str(encuentro.id),
    )

    # THEN la cascada está BLOQUEADA y la previa lo explica.
    assert previa.bloqueado is True
    assert previa.motivo_bloqueo
    assert previa.puede_confirmar is False


async def test_la_vista_previa_de_un_avance_ya_aplicado_lo_dice(
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
    from modules.competencias.domain.models import Encuentro

    await _preparar_encuentro_finalizado(
        encuentro_flujo,
        resultado_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )
    origen = Encuentro.objects.get(id=encuentro.id)
    await avance_flujo.confirmar(
        str(competencia.id),
        str(encuentro.id),
        AvanceData(motivo="Avance confirmado"),
        expected_version=origen.version,
    )

    # WHEN se pide la vista previa de nuevo.
    previa = await avance_flujo.previsualizar(
        str(competencia.id),
        str(encuentro.id),
    )

    # THEN la previa informa del reintento idempotente.
    assert previa.ya_propagado is True
    assert previa.puede_confirmar is False
