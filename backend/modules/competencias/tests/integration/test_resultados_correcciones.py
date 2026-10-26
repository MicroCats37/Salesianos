"""
Integration tests — result, advance and correction of the bracket (Phase 2).

The winner is AUTHORITATIVE: it must occupy one of the two slots and the
scores are optional and informative (they never determine nor contradict it).

The advance PROPOSES the placement of the winner in the linked slot of the
next encounter and it propagates it ONCE, recording `ganador_propagado`.

The correction NEVER cascades silently: the preview returns the impact of
the correction and a descendant that already started, finished or was
cancelled demands an EXPLICIT override with an accepted impact and a motive.
"""
import pytest
from asgiref.sync import async_to_sync

from modules.competencias.domain.exceptions import (
    DestinoBloqueadoError,
    InvalidLinkError,
    InvalidWinnerError,
    ReasonRequiredError,
    ResourceChangedError,
    SlotOcupadoError,
)
from modules.competencias.domain.models import Encuentro
from modules.competencias.domain.schemas.competencias_schemas import (
    CorreccionGanadorData,
    EncuentroCreateData,
    EncuentroProgramacionData,
    ResultadoEncuentroData,
)
from modules.competencias.tests.factories import (
    make_horario_payload,
    make_horario_tarde_payload,
)

MOTIVO_RESULTADO = "Registro del resultado del encuentro"
MOTIVO_VINCULO = "Vinculacion del encuentro con la siguiente ronda"
MOTIVO_AVANCE = "Propagacion del ganador al encuentro enlazado"
MOTIVO_CORRECCION = "Correccion administrativa del ganador del encuentro"


# ── Builders ─────────────────────────────────────────────────────────────────


def _incorporar(orquestador_competencia_equipos, competencia, equipo, orden, actor):
    """Register a team inside the bracket of the competition."""
    return async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id),
        str(equipo.id),
        orden,
        actor,
    )


def _crear(orquestador_encuentros, ronda, actor, orden=1, participante_1=None,
           participante_2=None):
    """Create an encounter of the round."""
    data = EncuentroCreateData(
        orden=orden,
        participante_1_id=participante_1,
        participante_2_id=participante_2,
    )
    return async_to_sync(orquestador_encuentros.crear_encuentro_proceso)(
        str(ronda.id),
        data,
        actor,
    )


def _programar(orquestador_encuentros, encuentro_id, actor, tarde=False):
    """Schedule the encounter inside the day of the competition."""
    inicio, fin = (
        make_horario_tarde_payload() if tarde else make_horario_payload()
    )
    return async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro_id),
        EncuentroProgramacionData(inicio_programado=inicio, fin_programado=fin),
        actor,
        "Programacion inicial del encuentro",
    )


def _iniciar(orquestador_encuentros, encuentro_id, actor):
    """Start the encounter."""
    return async_to_sync(orquestador_encuentros.cambiar_estado_encuentro_proceso)(
        str(encuentro_id),
        "EN_CURSO",
        actor,
    )


def _partido(orquestador_competencia_equipos, orquestador_encuentros, competencia, ronda,
             equipos, orden_equipo, orden_encuentro, actor, tarde=False):
    """Build a RUNNING encounter between two registered teams.

    Returns the encounter and the two entries of the bracket.
    """
    entrada_1 = _incorporar(
        orquestador_competencia_equipos, competencia, equipos[0], orden_equipo, actor
    )
    entrada_2 = _incorporar(
        orquestador_competencia_equipos, competencia, equipos[1], orden_equipo + 1, actor
    )
    encuentro = _crear(
        orquestador_encuentros,
        ronda,
        actor,
        orden_encuentro,
        str(entrada_1.id),
        str(entrada_2.id),
    )
    _programar(orquestador_encuentros, encuentro.id, actor, tarde=tarde)
    _iniciar(orquestador_encuentros, encuentro.id, actor)
    return encuentro, entrada_1, entrada_2


def _resultado(orquestador_resultados, encuentro_id, ganador_id, actor,
               motivo=MOTIVO_RESULTADO, puntaje_1=None, puntaje_2=None,
               detalle="", expected_version=None):
    """Register the authoritative winner of the encounter."""
    data = ResultadoEncuentroData(
        ganador_id=str(ganador_id),
        puntaje_1=puntaje_1,
        puntaje_2=puntaje_2,
        marcador_detalle=detalle,
    )
    return async_to_sync(orquestador_resultados.registrar_resultado_proceso)(
        str(encuentro_id),
        data,
        actor,
        motivo,
        expected_version,
    )


def _enlazar(orquestador_encuentros, encuentro_id, siguiente_id, slot, actor,
             motivo=MOTIVO_VINCULO, expected_version=None):
    """Link the encounter to the next encounter of the bracket."""
    return async_to_sync(
        orquestador_encuentros.enlazar_siguiente_encuentro_proceso
    )(
        str(encuentro_id),
        str(siguiente_id),
        slot,
        actor,
        motivo,
        expected_version,
    )


def _avanzar(orquestador_avances, encuentro_id, actor, motivo=MOTIVO_AVANCE,
             expected_version=None):
    """Propagate the winner of the encounter."""
    return async_to_sync(orquestador_avances.confirmar_avance_proceso)(
        str(encuentro_id),
        actor,
        motivo,
        expected_version,
    )


def _corregir(orquestador_correcciones, encuentro_id, ganador_nuevo_id, actor,
              motivo=MOTIVO_CORRECCION, override=False, acepta_impacto=False,
              expected_version=None):
    """Correct the authoritative winner of the encounter."""
    data = CorreccionGanadorData(
        ganador_id=str(ganador_nuevo_id),
        motivo=motivo,
        override=override,
        acepta_impacto=acepta_impacto,
    )
    return async_to_sync(orquestador_correcciones.corregir_ganador_proceso)(
        str(encuentro_id),
        data,
        actor,
        expected_version,
    )


# ── The result: the winner is authoritative ─────────────────────────────────


@pytest.mark.django_db
def test_el_ganador_debe_ocupar_uno_de_los_slots(
    orquestador_resultados,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    crear_equipos_competencia,
):
    """GIVEN: a running encounter WHEN: a team that does not play is declared
    the winner THEN: the result is refused."""
    equipos = crear_equipos_competencia(3, "Alfa")
    actor = usuario_admin_competencias
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos[:2],
        1,
        1,
        actor,
    )
    entrada_ajena = _incorporar(orquestador_competencia_equipos, competencia, equipos[2], 3, actor)

    with pytest.raises(InvalidWinnerError):
        _resultado(orquestador_resultados, encuentro.id, entrada_ajena.id, actor)


@pytest.mark.django_db
def test_el_resultado_finaliza_el_encuentro_y_queda_auditado(
    orquestador_resultados,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    crear_equipos_competencia,
):
    """GIVEN: a running encounter WHEN: the winner is registered THEN: the
    encounter is final and the change is audited with the actor and the motive."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )

    version_previa = Encuentro.objects.get(id=encuentro.id).version
    resultado = _resultado(
        orquestador_resultados, encuentro.id, entrada_1.id, actor
    )

    assert resultado.estado == "FINALIZADO"
    assert resultado.ganador_id == str(entrada_1.id)
    assert resultado.finalizado_en is not None
    assert resultado.version == version_previa + 1

    registro = Encuentro.objects.get(id=encuentro.id).history.latest("history_date")
    assert registro.history_user_id == actor.id
    assert registro.history_change_reason == MOTIVO_RESULTADO


@pytest.mark.django_db
def test_los_puntajes_son_opcionales(
    orquestador_resultados,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    crear_equipos_competencia,
):
    """GIVEN: a running encounter WHEN: the winner is registered without scores
    THEN: the result is accepted and the scores stay empty."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )

    resultado = _resultado(
        orquestador_resultados, encuentro.id, entrada_1.id, actor
    )

    assert resultado.puntaje_1 is None
    assert resultado.puntaje_2 is None
    assert resultado.marcador_detalle == ""
    assert resultado.ganador_id == str(entrada_1.id)


@pytest.mark.django_db
def test_los_puntajes_no_determinan_ni_contradicen_al_ganador(
    orquestador_resultados,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    crear_equipos_competencia,
):
    """GIVEN: a running encounter WHEN: the score contradicts the declared
    winner THEN: the winner stays authoritative and the score is stored."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )

    resultado = _resultado(
        orquestador_resultados,
        encuentro.id,
        entrada_2.id,
        actor,
        puntaje_1=3,
        puntaje_2=0,
        detalle="3-0 sets 1",
    )

    assert resultado.ganador_id == str(entrada_2.id)
    assert resultado.puntaje_1 == 3
    assert resultado.puntaje_2 == 0
    assert resultado.marcador_detalle == "3-0 sets 1"


@pytest.mark.django_db
def test_el_resultado_exige_motivo(
    orquestador_resultados,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    crear_equipos_competencia,
):
    """GIVEN: a running encounter WHEN: the result has no motive THEN: it is
    refused (the winner is a protected mutation)."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )

    with pytest.raises(ReasonRequiredError):
        _resultado(
            orquestador_resultados, encuentro.id, entrada_1.id, actor, motivo=None
        )


@pytest.mark.django_db
def test_el_resultado_repetido_no_escribe_nada(
    orquestador_resultados,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    crear_equipos_competencia,
):
    """GIVEN: an encounter with its result WHEN: the same result is sent again
    THEN: nothing is written (the complete intention is compared first)."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    primero = _resultado(
        orquestador_resultados, encuentro.id, entrada_1.id, actor, puntaje_1=2
    )
    historial_inicial = Encuentro.objects.get(id=encuentro.id).history.count()

    repetido = _resultado(
        orquestador_resultados,
        encuentro.id,
        entrada_1.id,
        actor,
        puntaje_1=2,
        expected_version=encuentro.version,
    )

    assert repetido.version == primero.version
    assert (
        Encuentro.objects.get(id=encuentro.id).history.count() == historial_inicial
    )


@pytest.mark.django_db
def test_el_resultado_con_version_obsoleta_falla(
    orquestador_resultados,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    crear_equipos_competencia,
):
    """GIVEN: a running encounter WHEN: the result is sent with a stale
    version THEN: it fails with a conflict and without partial effects."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )

    with pytest.raises(ResourceChangedError):
        _resultado(
            orquestador_resultados,
            encuentro.id,
            entrada_1.id,
            actor,
            expected_version=encuentro.version + 5,
        )

    guardado = Encuentro.objects.get(id=encuentro.id)
    assert guardado.ganador_id is None
    assert guardado.estado == "EN_CURSO"


# ── The link of the bracket ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_el_vinculo_se_escribe_completo(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    ronda_2,
):
    """GIVEN: two rounds WHEN: the encounter is linked THEN: the link and its
    destination slot are written together."""
    actor = usuario_admin_competencias
    origen = _crear(orquestador_encuentros, ronda, actor, 1)
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)

    resultado = _enlazar(
        orquestador_encuentros, origen.id, destino.id, "PARTICIPANTE_1", actor
    )

    assert resultado.siguiente_encuentro_id == str(destino.id)
    assert resultado.slot_destino == "PARTICIPANTE_1"
    assert resultado.version == origen.version + 1


@pytest.mark.django_db
def test_el_vinculo_hacia_otra_competencia_es_rechazado(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_2,
):
    """GIVEN: an encounter of another bracket WHEN: the link points there THEN:
    the integrity of the link fails."""
    actor = usuario_admin_competencias
    origen = _crear(orquestador_encuentros, ronda, actor, 1)
    destino = _crear(orquestador_encuentros, ronda, actor, 2)

    with pytest.raises(InvalidLinkError):
        _enlazar(
            orquestador_encuentros, origen.id, destino.id, "PARTICIPANTE_1", actor
        )


@pytest.mark.django_db
def test_el_vinculo_consigo_mismo_es_rechazado(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
):
    """GIVEN: an encounter WHEN: it is linked to itself THEN: it is refused."""
    actor = usuario_admin_competencias
    origen = _crear(orquestador_encuentros, ronda, actor, 1)

    with pytest.raises(InvalidLinkError):
        _enlazar(
            orquestador_encuentros, origen.id, origen.id, "PARTICIPANTE_1", actor
        )


@pytest.mark.django_db
def test_el_vinculo_hacia_una_ronda_anterior_es_rechazado(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    ronda_2,
):
    """GIVEN: two rounds WHEN: the link points backwards THEN: it is refused
    (the link always points forward, so no cycle can be built)."""
    actor = usuario_admin_competencias
    origen = _crear(orquestador_encuentros, ronda_2, actor, 1)
    destino = _crear(orquestador_encuentros, ronda, actor, 1)

    with pytest.raises(InvalidLinkError):
        _enlazar(
            orquestador_encuentros, origen.id, destino.id, "PARTICIPANTE_1", actor
        )


@pytest.mark.django_db
def test_el_vinculo_exige_motivo(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    ronda_2,
):
    """GIVEN: two rounds WHEN: the link has no motive THEN: it is refused."""
    actor = usuario_admin_competencias
    origen = _crear(orquestador_encuentros, ronda, actor, 1)
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)

    with pytest.raises(ReasonRequiredError):
        _enlazar(
            orquestador_encuentros,
            origen.id,
            destino.id,
            "PARTICIPANTE_1",
            actor,
            motivo=None,
        )


@pytest.mark.django_db
def test_el_vinculo_repetido_no_escribe_nada(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    ronda_2,
):
    """GIVEN: a linked encounter WHEN: the same link is sent again THEN:
    nothing is written."""
    actor = usuario_admin_competencias
    origen = _crear(orquestador_encuentros, ronda, actor, 1)
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, origen.id, destino.id, "PARTICIPANTE_1", actor)
    historial_inicial = Encuentro.objects.get(id=origen.id).history.count()

    repetido = _enlazar(
        orquestador_encuentros,
        origen.id,
        destino.id,
        "PARTICIPANTE_1",
        actor,
        expected_version=origen.version,
    )

    assert repetido.version == origen.version + 1
    assert Encuentro.objects.get(id=origen.id).history.count() == historial_inicial


@pytest.mark.django_db
def test_el_vinculo_se_puede_quitar(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    ronda_2,
):
    """GIVEN: a linked encounter WHEN: the link is removed THEN: both fields
    are cleared together."""
    actor = usuario_admin_competencias
    origen = _crear(orquestador_encuentros, ronda, actor, 1)
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, origen.id, destino.id, "PARTICIPANTE_1", actor)

    resultado = async_to_sync(
        orquestador_encuentros.desenlazar_siguiente_encuentro_proceso
    )(
        str(origen.id),
        actor,
        "Correccion del vinculo del cuadro",
    )

    assert resultado.siguiente_encuentro_id is None
    assert resultado.slot_destino is None


# ── The advance: the propagation of the winner ──────────────────────────────


@pytest.mark.django_db
def test_la_previsualizacion_propone_el_ganador_en_el_slot_enlazado(
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: an encounter with a winner and a linked destination WHEN: the
    advance is previewed THEN: the placement is proposed and nothing is written."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)

    previsualizacion = async_to_sync(
        orquestador_avances.previsualizar_avance_proceso
    )(str(encuentro.id))

    assert previsualizacion.siguiente_encuentro_id == str(destino.id)
    assert previsualizacion.slot_destino == "PARTICIPANTE_1"
    assert previsualizacion.ganador_id == str(entrada_1.id)
    assert previsualizacion.ocupante_actual_id is None
    assert previsualizacion.ya_propagado is False
    assert previsualizacion.bloqueado is False
    assert Encuentro.objects.get(id=destino.id).participante_1_id is None


@pytest.mark.django_db
def test_el_avance_coloca_el_ganador_una_sola_vez_y_registra_la_propagacion(
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: an encounter with a winner and a linked destination WHEN: the
    advance is confirmed THEN: the winner is placed once and the propagation is
    recorded."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)

    resultado = _avanzar(orquestador_avances, encuentro.id, actor)

    assert resultado.ya_aplicado is False
    assert resultado.ganador_id == str(entrada_1.id)
    assert resultado.destino.participante_1_id == str(entrada_1.id)
    assert resultado.destino.ganador_propagado_id == str(entrada_1.id)
    assert resultado.destino.participante_2_id is None

    guardado = Encuentro.objects.get(id=destino.id)
    assert str(guardado.participante_1_id) == str(entrada_1.id)
    assert str(guardado.ganador_propagado_id) == str(entrada_1.id)

    registro = Encuentro.objects.get(id=destino.id).history.latest("history_date")
    assert registro.history_user_id == actor.id
    assert registro.history_change_reason == MOTIVO_AVANCE


@pytest.mark.django_db
def test_el_avance_repetido_no_escribe_nada(
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: an already propagated winner WHEN: the advance is confirmed
    again THEN: nothing is written (idempotent replay)."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)
    primero = _avanzar(orquestador_avances, encuentro.id, actor)
    historial_inicial = Encuentro.objects.get(id=destino.id).history.count()

    repetido = _avanzar(
        orquestador_avances, encuentro.id, actor, expected_version=encuentro.version
    )

    assert repetido.ya_aplicado is True
    assert repetido.destino.version == primero.destino.version
    assert Encuentro.objects.get(id=destino.id).history.count() == historial_inicial


@pytest.mark.django_db
def test_el_avance_con_version_obsoleta_falla(
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: an encounter with a winner WHEN: the advance is confirmed with a
    stale version THEN: it fails and the destination is untouched."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)

    with pytest.raises(ResourceChangedError):
        _avanzar(
            orquestador_avances,
            encuentro.id,
            actor,
            expected_version=encuentro.version + 7,
        )

    guardado = Encuentro.objects.get(id=destino.id)
    assert guardado.participante_1_id is None
    assert guardado.ganador_propagado_id is None


@pytest.mark.django_db
def test_el_avance_a_un_destino_bloqueado_falla(
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: a destination that already started WHEN: the advance is
    confirmed THEN: it is blocked."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _programar(orquestador_encuentros, destino.id, actor, tarde=True)
    _iniciar(orquestador_encuentros, destino.id, actor)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)

    with pytest.raises(DestinoBloqueadoError):
        _avanzar(orquestador_avances, encuentro.id, actor)


@pytest.mark.django_db
def test_el_avance_a_un_slot_ocupado_falla(
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: a destination slot that already holds another team WHEN: the
    advance is confirmed THEN: the slot is reported as occupied."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(3, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos[:2],
        1,
        1,
        actor,
    )
    entrada_ajena = _incorporar(orquestador_competencia_equipos, competencia, equipos[2], 3, actor)
    destino = _crear(
        orquestador_encuentros,
        ronda_2,
        actor,
        1,
        str(entrada_ajena.id),
    )
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)

    with pytest.raises(SlotOcupadoError):
        _avanzar(orquestador_avances, encuentro.id, actor)


@pytest.mark.django_db
def test_el_avance_sin_vinculo_falla(
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    crear_equipos_competencia,
):
    """GIVEN: an encounter with a winner but WITHOUT a link WHEN: the advance
    is confirmed THEN: the link is invalid."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)

    with pytest.raises(InvalidLinkError):
        _avanzar(orquestador_avances, encuentro.id, actor)


# ── The correction: the impact and the explicit override ────────────────────


@pytest.mark.django_db
def test_la_previsualizacion_de_la_correccion_muestra_el_impacto(
    orquestador_correcciones,
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: a propagated winner WHEN: the correction is previewed THEN: the
    impact over the descendant is shown and nothing is written."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)
    _avanzar(orquestador_avances, encuentro.id, actor)

    previsualizacion = async_to_sync(
        orquestador_correcciones.previsualizar_correccion_proceso
    )(str(encuentro.id), str(entrada_2.id))

    assert previsualizacion.ganador_actual_id == str(entrada_1.id)
    assert previsualizacion.ganador_nuevo_id == str(entrada_2.id)
    assert previsualizacion.requiere_override is False
    assert len(previsualizacion.descendientes) == 1
    impacto = previsualizacion.descendientes[0]
    assert impacto.encuentro_id == str(destino.id)
    assert impacto.bloqueado is False
    assert impacto.se_reemplaza is True
    assert str(Encuentro.objects.get(id=encuentro.id).ganador_id) == str(entrada_1.id)


@pytest.mark.django_db
def test_la_correccion_antes_del_inicio_del_descendiente_lo_reemplaza(
    orquestador_correcciones,
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: a winner propagated to an encounter that did not start WHEN: the
    correction is confirmed THEN: the participant is replaced and BOTH changes
    are audited."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)
    _avanzar(orquestador_avances, encuentro.id, actor)

    resultado = _corregir(
        orquestador_correcciones, encuentro.id, entrada_2.id, actor
    )

    assert resultado.ganador_id == str(entrada_2.id)
    assert resultado.descendientes_afectados == 1

    origen = Encuentro.objects.get(id=encuentro.id)
    assert str(origen.ganador_id) == str(entrada_2.id)
    destino_guardado = Encuentro.objects.get(id=destino.id)
    assert str(destino_guardado.participante_1_id) == str(entrada_2.id)
    assert str(destino_guardado.ganador_propagado_id) == str(entrada_2.id)

    for encuentro_auditado in (encuentro, destino):
        registro = Encuentro.objects.get(
            id=encuentro_auditado.id
        ).history.latest("history_date")
        assert registro.history_user_id == actor.id
        assert registro.history_change_reason == MOTIVO_CORRECCION


@pytest.mark.django_db
def test_la_correccion_con_descendiente_bloqueado_no_cambia_nada(
    orquestador_correcciones,
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: a descendant that already started WHEN: the correction is
    confirmed without an override THEN: it is blocked and NOTHING changes."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)
    _avanzar(orquestador_avances, encuentro.id, actor)
    _programar(orquestador_encuentros, destino.id, actor, tarde=True)
    _iniciar(orquestador_encuentros, destino.id, actor)

    with pytest.raises(DestinoBloqueadoError):
        _corregir(orquestador_correcciones, encuentro.id, entrada_2.id, actor)

    assert str(Encuentro.objects.get(id=encuentro.id).ganador_id) == str(entrada_1.id)
    destino_guardado = Encuentro.objects.get(id=destino.id)
    assert str(destino_guardado.participante_1_id) == str(entrada_1.id)
    assert str(destino_guardado.ganador_propagado_id) == str(entrada_1.id)


@pytest.mark.django_db
def test_la_correccion_con_override_aceptado_reescribe_el_descendiente_bloqueado(
    orquestador_correcciones,
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: a descendant that already started WHEN: the correction is
    confirmed with an explicit override and an accepted impact THEN: the
    descendant is rewritten and the override is audited."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)
    _avanzar(orquestador_avances, encuentro.id, actor)
    _programar(orquestador_encuentros, destino.id, actor, tarde=True)
    _iniciar(orquestador_encuentros, destino.id, actor)

    previsualizacion = async_to_sync(
        orquestador_correcciones.previsualizar_correccion_proceso
    )(str(encuentro.id), str(entrada_2.id))
    assert previsualizacion.requiere_override is True

    resultado = _corregir(
        orquestador_correcciones,
        encuentro.id,
        entrada_2.id,
        actor,
        override=True,
        acepta_impacto=True,
    )

    assert resultado.requirio_override is True
    assert str(Encuentro.objects.get(id=encuentro.id).ganador_id) == str(entrada_2.id)
    destino_guardado = Encuentro.objects.get(id=destino.id)
    assert str(destino_guardado.participante_1_id) == str(entrada_2.id)
    assert str(destino_guardado.ganador_propagado_id) == str(entrada_2.id)

    registro = Encuentro.objects.get(id=destino.id).history.latest("history_date")
    assert registro.history_user_id == actor.id
    assert "override" in registro.history_change_reason
    assert registro.history_change_reason.startswith(MOTIVO_CORRECCION)


@pytest.mark.django_db
def test_la_correccion_sin_impacto_aceptado_no_cambia_nada(
    orquestador_correcciones,
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: a blocked descendant WHEN: the override is sent but the impact is
    NOT accepted THEN: it is blocked and nothing changes."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)
    _avanzar(orquestador_avances, encuentro.id, actor)
    _programar(orquestador_encuentros, destino.id, actor, tarde=True)
    _iniciar(orquestador_encuentros, destino.id, actor)

    with pytest.raises(DestinoBloqueadoError):
        _corregir(
            orquestador_correcciones,
            encuentro.id,
            entrada_2.id,
            actor,
            override=True,
            acepta_impacto=False,
        )

    assert str(Encuentro.objects.get(id=encuentro.id).ganador_id) == str(entrada_1.id)


@pytest.mark.django_db
def test_la_correccion_exige_motivo(
    orquestador_correcciones,
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: a propagated winner WHEN: the correction has a motive that is too
    short THEN: it is refused."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)
    _avanzar(orquestador_avances, encuentro.id, actor)

    with pytest.raises(ReasonRequiredError):
        _corregir(
            orquestador_correcciones,
            encuentro.id,
            entrada_2.id,
            actor,
            motivo="mal",
        )


@pytest.mark.django_db
def test_la_correccion_repetida_no_escribe_nada(
    orquestador_correcciones,
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: an already corrected winner WHEN: the same correction is sent
    again THEN: nothing is written."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)
    _avanzar(orquestador_avances, encuentro.id, actor)
    primero = _corregir(orquestador_correcciones, encuentro.id, entrada_2.id, actor)
    historial_inicial = Encuentro.objects.get(id=encuentro.id).history.count()

    repetido = _corregir(
        orquestador_correcciones,
        encuentro.id,
        entrada_2.id,
        actor,
        expected_version=encuentro.version,
    )

    assert repetido.descendientes_afectados == 0
    assert Encuentro.objects.get(id=encuentro.id).history.count() == historial_inicial
    assert primero.descendientes_afectados == 1


@pytest.mark.django_db
def test_la_correccion_limpia_el_resultado_derivado_y_su_avance(
    orquestador_correcciones,
    orquestador_avances,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    ronda_3,
    crear_equipos_competencia,
):
    """GIVEN: a descendant that already played with the propagated winner
    WHEN: the correction is confirmed with an override THEN: its result is
    voided and ITS advance is voided too (the slot it filled is emptied)."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(3, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos[:2],
        1,
        1,
        actor,
    )
    destino = _crear(orquestador_encuentros, ronda_2, actor, 1)
    descendiente = _crear(orquestador_encuentros, ronda_3, actor, 1)
    _enlazar(orquestador_encuentros, encuentro.id, destino.id, "PARTICIPANTE_1", actor)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)
    _avanzar(orquestador_avances, encuentro.id, actor)

    # The descendant plays the propagated winner and advances it.
    _programar(orquestador_encuentros, destino.id, actor, tarde=True)
    _iniciar(orquestador_encuentros, destino.id, actor)
    _enlazar(
        orquestador_encuentros, destino.id, descendiente.id, "PARTICIPANTE_1", actor
    )
    _resultado(
        orquestador_resultados,
        destino.id,
        entrada_1.id,
        actor,
        puntaje_1=2,
        detalle="2-0",
    )
    _avanzar(orquestador_avances, destino.id, actor)

    assert str(Encuentro.objects.get(id=descendiente.id).participante_1_id) == str(
        entrada_1.id
    )

    _corregir(
        orquestador_correcciones,
        encuentro.id,
        entrada_2.id,
        actor,
        override=True,
        acepta_impacto=True,
    )

    destino_guardado = Encuentro.objects.get(id=destino.id)
    assert str(destino_guardado.participante_1_id) == str(entrada_2.id)
    assert destino_guardado.ganador_id is None
    assert destino_guardado.puntaje_1 is None
    assert destino_guardado.marcador_detalle == ""
    assert destino_guardado.estado == "EN_CURSO"
    assert destino_guardado.finalizado_en is None

    # The advance of the descendant is void too: its slot is emptied.
    descendiente_guardado = Encuentro.objects.get(id=descendiente.id)
    assert descendiente_guardado.participante_1_id is None
    assert descendiente_guardado.ganador_propagado_id is None


@pytest.mark.django_db
def test_la_correccion_no_toca_los_encuentros_sin_propagacion(
    orquestador_correcciones,
    orquestador_encuentros,
    orquestador_competencia_equipos,
    orquestador_resultados,
    usuario_admin_competencias,
    competencia,
    ronda,
    ronda_2,
    crear_equipos_competencia,
):
    """GIVEN: an encounter without a link WHEN: it is corrected THEN: no other
    encounter of the bracket is touched (the cascade never happens silently)."""
    actor = usuario_admin_competencias
    equipos = crear_equipos_competencia(2, "Alfa")
    encuentro, entrada_1, entrada_2 = _partido(
        orquestador_competencia_equipos,
        orquestador_encuentros,
        competencia,
        ronda,
        equipos,
        1,
        1,
        actor,
    )
    otro = _crear(orquestador_encuentros, ronda_2, actor, 1)
    _resultado(orquestador_resultados, encuentro.id, entrada_1.id, actor)

    _corregir(orquestador_correcciones, encuentro.id, entrada_2.id, actor)

    assert str(Encuentro.objects.get(id=encuentro.id).ganador_id) == str(entrada_2.id)
    intacto = Encuentro.objects.get(id=otro.id)
    assert intacto.participante_1_id is None
    assert intacto.ganador_id is None
    assert intacto.version == otro.version
