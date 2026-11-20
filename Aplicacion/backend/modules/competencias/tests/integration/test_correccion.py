"""La CORRECCION declara su impacto y NUNCA hace una cascada oculta.

GIVEN  un encuentro con un ganador propagado a un descendiente
WHEN   el administrador previsualiza o aplica una corrección
THEN   la previa dice QUÉ encuentros cambian y NO escribe; la aplicación exige
       motivo, respeta la propagación (nunca pisa una colocación manual) y
       se BLOQUEA si un descendiente ya transcurrió (`RN-K02`, `QA-K03`).
"""

import pytest
from asgiref.sync import async_to_sync

from modules.competencias.domain.constants import EstadoEncuentro, SlotDestino
from modules.competencias.domain.exceptions import DestinoBloqueadoError
from modules.competencias.domain.models import AuditoriaOperacion, Encuentro
from modules.competencias.domain.schemas.competencias_schemas import (
    AvanceData,
    CorreccionData,
    EncuentroActualizarData,
    ResultadoEncuentroData,
)
from modules.competencias.domain.services.flujos.avance_flujo import AvanceFlujo
from modules.competencias.domain.services.flujos.correccion_flujo import (
    CorreccionFlujo,
)
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


@pytest.fixture
def correccion_flujo(injector):
    """El flujo real de corrección."""
    return injector.get(CorreccionFlujo)


def _preparar(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
    *,
    avanzar: bool = True,
):
    """Deja el encuentro FINALIZADO, con ganador y (opcionalmente) avanzado."""
    async_to_sync(encuentro_flujo.actualizar_encuentro)(
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
    async_to_sync(encuentro_flujo.actualizar_encuentro)(
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
    async_to_sync(encuentro_flujo.actualizar_encuentro)(
        str(competencia.id),
        str(encuentro.id),
        EncuentroActualizarData(
            estado=EstadoEncuentro.EN_CURSO,
            motivo="Inicio del encuentro",
        ),
        expected_version=actual.version,
    )
    actual = Encuentro.objects.get(id=encuentro.id)
    async_to_sync(resultado_flujo.registrar)(
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
    if avanzar:
        actual = Encuentro.objects.get(id=encuentro.id)
        async_to_sync(avance_flujo.confirmar)(
            str(competencia.id),
            str(encuentro.id),
            AvanceData(motivo="Avance confirmado"),
            expected_version=actual.version,
        )
    return Encuentro.objects.get(id=encuentro.id)


def test_la_vista_previa_de_correccion_no_escribe_nada(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    correccion_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un encuentro con un ganador propagado a un descendiente."""
    _preparar(
        encuentro_flujo,
        resultado_flujo,
        avance_flujo,
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

    # WHEN el administrador pide la vista previa de la corrección.
    previa = async_to_sync(correccion_flujo.previsualizar)(
        str(competencia.id),
        str(encuentro.id),
        str(equipo_2_en_cuadro.id),
    )

    # THEN la previa declara el impacto y NO escribe NADA.
    assert previa.total_afectados == 1
    assert previa.requiere_override is False
    assert previa.descendientes[0].encuentro_id == str(encuentro_final.id)
    assert previa.descendientes[0].reemplaza is True
    assert Encuentro.objects.get(id=encuentro.id).version == version_antes
    destino_despues = Encuentro.objects.get(id=encuentro_final.id)
    assert destino_despues.participante_1_id == destino_antes.participante_1_id
    assert destino_despues.version == destino_antes.version
    assert AuditoriaOperacion.objects.count() == actas_antes


def test_la_correccion_propaga_el_ganador_nuevo(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    correccion_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un encuentro con un ganador propagado."""
    _preparar(
        encuentro_flujo,
        resultado_flujo,
        avance_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )
    origen = Encuentro.objects.get(id=encuentro.id)

    # WHEN el administrador corrige el ganador con su motivo.
    resultado = async_to_sync(correccion_flujo.corregir)(
        str(competencia.id),
        str(encuentro.id),
        CorreccionData(
            ganador_id=str(equipo_2_en_cuadro.id),
            motivo="Se corrigió el marcador por error de anotación",
        ),
        expected_version=origen.version,
    )

    # THEN el encuentro corregido tiene el ganador nuevo y el descendiente
    # recibe la propagación corregida.
    assert resultado.ganador_nuevo_equipo_id == str(equipo_2_en_cuadro.equipo_id)
    assert resultado.descendientes_afectados == 1
    assert Encuentro.objects.get(id=encuentro.id).ganador_id == equipo_2_en_cuadro.id
    destino = Encuentro.objects.get(id=encuentro_final.id)
    assert destino.participante_1_id == equipo_2_en_cuadro.id
    assert destino.ganador_propagado_id == equipo_2_en_cuadro.id


def test_la_correccion_limpia_el_marcador_anterior(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    correccion_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un encuentro con marcador registrado."""
    _preparar(
        encuentro_flujo,
        resultado_flujo,
        avance_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )
    origen = Encuentro.objects.get(id=encuentro.id)

    # WHEN se corrige el ganador.
    async_to_sync(correccion_flujo.corregir)(
        str(competencia.id),
        str(encuentro.id),
        CorreccionData(
            ganador_id=str(equipo_2_en_cuadro.id),
            motivo="Se corrigió el marcador por error de anotación",
        ),
        expected_version=origen.version,
    )

    # THEN el marcador que contradecía al ganador se retira.
    corregido = Encuentro.objects.get(id=encuentro.id)
    assert corregido.puntaje_1 is None
    assert corregido.puntaje_2 is None
    assert corregido.marcador_detalle == ""


def test_un_descendiente_ya_transcurrido_bloquea_la_cascada(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    correccion_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un descendiente que YA transcurrió."""
    _preparar(
        encuentro_flujo,
        resultado_flujo,
        avance_flujo,
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
    origen = Encuentro.objects.get(id=encuentro.id)

    # WHEN se corrige SIN autorización explícita.
    with pytest.raises(DestinoBloqueadoError) as error:
        async_to_sync(correccion_flujo.corregir)(
            str(competencia.id),
            str(encuentro.id),
            CorreccionData(
                ganador_id=str(equipo_2_en_cuadro.id),
                motivo="Corrección sobre un descendiente transcurrido",
            ),
            expected_version=origen.version,
        )

    # THEN NADA se escribe: no hay cascada silenciosa.
    assert error.value.code == "DESTINO_BLOQUEADO"
    assert Encuentro.objects.get(id=encuentro.id).ganador_id == equipo_en_cuadro.id


def test_el_override_explicito_permite_la_cascada_bloqueada(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    correccion_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un descendiente bloqueado y una autorización EXPLÍCITA."""
    _preparar(
        encuentro_flujo,
        resultado_flujo,
        avance_flujo,
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
    origen = Encuentro.objects.get(id=encuentro.id)

    # WHEN el administrador autoriza el override y acepta el impacto.
    resultado = async_to_sync(correccion_flujo.corregir)(
        str(competencia.id),
        str(encuentro.id),
        CorreccionData(
            ganador_id=str(equipo_2_en_cuadro.id),
            motivo="Corrección autorizada por el coordinador",
            override=True,
            acepta_impacto=True,
        ),
        expected_version=origen.version,
    )

    # THEN la corrección se aplica y declara el override.
    assert resultado.override_aplicado is True
    assert Encuentro.objects.get(id=encuentro.id).ganador_id == equipo_2_en_cuadro.id


def test_la_correccion_no_pisa_una_colocacion_manual(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    correccion_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN un descendiente cuyo slot se COLOCÓ A MANO después del avance."""
    _preparar(
        encuentro_flujo,
        resultado_flujo,
        avance_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )
    destino = Encuentro.objects.get(id=encuentro_final.id)
    destino.participante_1 = equipo_2_en_cuadro
    destino.ganador_propagado = None
    destino.save()
    origen = Encuentro.objects.get(id=encuentro.id)

    # WHEN se corrige el ganador del encuentro de origen.
    resultado = async_to_sync(correccion_flujo.corregir)(
        str(competencia.id),
        str(encuentro.id),
        CorreccionData(
            ganador_id=str(equipo_2_en_cuadro.id),
            motivo="Corrección del encuentro de origen",
        ),
        expected_version=origen.version,
    )

    # THEN la colocación MANUAL del descendiente NO se toca.
    assert resultado.descendientes_afectados == 0
    destino = Encuentro.objects.get(id=encuentro_final.id)
    assert destino.participante_1_id == equipo_2_en_cuadro.id


def test_la_correccion_deja_su_acta(
    encuentro_flujo,
    resultado_flujo,
    avance_flujo,
    correccion_flujo,
    competencia,
    encuentro,
    encuentro_final,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
    jornada,
):
    """GIVEN una corrección aplicada."""
    from modules.competencias.domain.models.auditoria import AccionAuditada

    _preparar(
        encuentro_flujo,
        resultado_flujo,
        avance_flujo,
        competencia,
        encuentro,
        encuentro_final,
        equipo_en_cuadro,
        equipo_2_en_cuadro,
        jornada,
    )
    origen = Encuentro.objects.get(id=encuentro.id)

    async_to_sync(correccion_flujo.corregir)(
        str(competencia.id),
        str(encuentro.id),
        CorreccionData(
            ganador_id=str(equipo_2_en_cuadro.id),
            motivo="Se corrigió el marcador por error de anotación",
        ),
        expected_version=origen.version,
    )

    # THEN el acta conserva la corrección anterior como antecedente.
    acta = AuditoriaOperacion.objects.filter(
        accion=AccionAuditada.CORRECCION
    ).first()
    assert acta is not None
    assert acta.motivo == "Se corrigió el marcador por error de anotación"
