"""
Integration tests — commands of the encounters of the bracket (Phase 1).

An encounter may be empty or partial: the domain NEVER invents a
participant. The manual bye is configured by the administrator (exactly one
participant, no schedule, no score and the participant is the winner) and it
is never chosen automatically by the system.
"""
import pytest
from asgiref.sync import async_to_sync

from modules.competencias.domain.exceptions import (
    DeleteNotAllowedError,
    InvalidLinkError,
    InvalidScheduleError,
    InvalidStateTransitionError,
    InvalidWinnerError,
    ReasonRequiredError,
)
from modules.competencias.domain.models import CompetenciaEquipo, Encuentro
from modules.competencias.domain.schemas.competencias_schemas import (
    EncuentroCreateData,
)


def _crear(orquestador, ronda, actor, orden=1, **kwargs):
    """Create an encounter through the orchestrator."""
    data = EncuentroCreateData(
        orden=orden,
        participante_1_id=kwargs.get("participante_1_id"),
        participante_2_id=kwargs.get("participante_2_id"),
    )
    return async_to_sync(orquestador.crear_encuentro_proceso)(
        str(ronda.id),
        data,
        actor,
    )


# ── Creation ─────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_encuentro_vacio_se_crea_sin_inventar_participantes(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
):
    """GIVEN: a round WHEN: an empty encounter is created THEN: it stays empty."""
    resultado = _crear(orquestador_encuentros, ronda, usuario_admin_competencias)

    assert resultado.estado == "BORRADOR"
    assert resultado.participante_1_id is None
    assert resultado.participante_2_id is None
    assert resultado.es_bye is False
    assert resultado.version == 1


@pytest.mark.django_db
def test_encuentro_acepta_los_dos_participantes_de_su_competencia(
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    equipo_competencia,
    equipo_competencia_2,
):
    """GIVEN: two eligible teams WHEN: they face each other THEN: both are placed."""
    entrada_1 = async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id), str(equipo_competencia.id), 1, usuario_admin_competencias
    )
    entrada_2 = async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id), str(equipo_competencia_2.id), 2, usuario_admin_competencias
    )

    resultado = _crear(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        participante_1_id=str(entrada_1.id),
        participante_2_id=str(entrada_2.id),
    )

    assert resultado.participante_1_id == str(entrada_1.id)
    assert resultado.participante_2_id == str(entrada_2.id)


@pytest.mark.django_db
def test_participante_de_otra_competencia_es_rechazado(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_2,
    equipo_competencia,
):
    """GIVEN: a team of another bracket WHEN: it is placed THEN: the link fails."""
    entrada_ajena = CompetenciaEquipo.objects.create(
        competencia=competencia_2,
        equipo=equipo_competencia,
        orden=1,
        estado="ACTIVO",
    )

    with pytest.raises(InvalidLinkError):
        _crear(
            orquestador_encuentros,
            ronda,
            usuario_admin_competencias,
            participante_1_id=str(entrada_ajena.id),
        )


@pytest.mark.django_db
def test_mismo_equipo_en_los_dos_slots_es_rechazado(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: the same team twice WHEN: it is placed THEN: the link fails."""
    with pytest.raises(InvalidLinkError):
        _crear(
            orquestador_encuentros,
            ronda,
            usuario_admin_competencias,
            participante_1_id=str(competencia_equipo.id),
            participante_2_id=str(competencia_equipo.id),
        )


# ── Moving the participants ─────────────────────────────────────────────────


@pytest.mark.django_db
def test_mover_participantes_exige_motivo(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a slot move WHEN: it has no motive THEN: it is refused."""
    encuentro = _crear(orquestador_encuentros, ronda, usuario_admin_competencias)

    with pytest.raises(ReasonRequiredError):
        async_to_sync(orquestador_encuentros.asignar_participantes_proceso)(
            str(encuentro.id),
            str(competencia_equipo.id),
            None,
            usuario_admin_competencias,
        )


@pytest.mark.django_db
def test_mover_participantes_con_motivo_deja_rastro_en_la_historia(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a slot move with a motive WHEN: it is applied THEN: it is audited."""
    encuentro = _crear(orquestador_encuentros, ronda, usuario_admin_competencias)

    actualizado = async_to_sync(orquestador_encuentros.asignar_participantes_proceso)(
        str(encuentro.id),
        str(competencia_equipo.id),
        None,
        usuario_admin_competencias,
        "Ingreso manual del equipo al encuentro",
    )

    assert actualizado.participante_1_id == str(competencia_equipo.id)
    assert actualizado.version == encuentro.version + 1

    registro = Encuentro.objects.get(id=encuentro.id).history.latest("history_date")
    assert registro.history_user_id == usuario_admin_competencias.id
    assert registro.history_change_reason == "Ingreso manual del equipo al encuentro"


# ── Manual bye ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_bye_manual_finaliza_el_encuentro_con_el_participante(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a manual bye WHEN: it is configured THEN: it is final and audited."""
    encuentro = _crear(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        participante_1_id=str(competencia_equipo.id),
    )

    resultado = async_to_sync(orquestador_encuentros.configurar_bye_proceso)(
        str(encuentro.id),
        usuario_admin_competencias,
        "Pase manual aplicado por el administrador",
    )

    assert resultado.es_bye is True
    assert resultado.estado == "FINALIZADO"
    assert resultado.ganador_id == str(competencia_equipo.id)
    assert resultado.inicio_programado is None
    assert resultado.version == encuentro.version + 1


@pytest.mark.django_db
def test_bye_con_dos_participantes_es_rechazado(
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    equipo_competencia,
    equipo_competencia_2,
):
    """GIVEN: two participants WHEN: it becomes a bye THEN: it is refused."""
    entrada_1 = async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id), str(equipo_competencia.id), 1, usuario_admin_competencias
    )
    entrada_2 = async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id), str(equipo_competencia_2.id), 2, usuario_admin_competencias
    )
    encuentro = _crear(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        participante_1_id=str(entrada_1.id),
        participante_2_id=str(entrada_2.id),
    )

    with pytest.raises(InvalidWinnerError):
        async_to_sync(orquestador_encuentros.configurar_bye_proceso)(
            str(encuentro.id),
            usuario_admin_competencias,
            "Pase manual sobre un encuentro con dos equipos",
        )


@pytest.mark.django_db
def test_bye_con_horario_es_rechazado(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a scheduled encounter WHEN: it becomes a bye THEN: it is refused."""
    from modules.competencias.domain.schemas.competencias_schemas import (
        EncuentroProgramacionData,
    )
    from modules.competencias.tests.factories import make_horario_payload

    encuentro = _crear(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        participante_1_id=str(competencia_equipo.id),
    )
    inicio, fin = make_horario_payload()
    async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro.id),
        EncuentroProgramacionData(inicio_programado=inicio, fin_programado=fin),
        usuario_admin_competencias,
        "Programacion inicial del encuentro",
    )

    with pytest.raises(InvalidScheduleError):
        async_to_sync(orquestador_encuentros.configurar_bye_proceso)(
            str(encuentro.id),
            usuario_admin_competencias,
            "Pase manual sobre un encuentro programado",
        )


# ── Lifecycle ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_encuentro_recorre_borrador_programado_en_curso_y_suspendido(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a draft WHEN: it is played and suspended THEN: it advances."""
    from modules.competencias.domain.schemas.competencias_schemas import (
        EncuentroProgramacionData,
    )
    from modules.competencias.tests.factories import make_horario_payload

    encuentro = _crear(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        participante_1_id=str(competencia_equipo.id),
    )
    inicio, fin = make_horario_payload()
    programado = async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro.id),
        EncuentroProgramacionData(inicio_programado=inicio, fin_programado=fin),
        usuario_admin_competencias,
        "Programacion inicial del encuentro",
    )
    assert programado.estado == "PROGRAMADO"

    en_curso = async_to_sync(orquestador_encuentros.cambiar_estado_encuentro_proceso)(
        str(encuentro.id),
        "EN_CURSO",
        usuario_admin_competencias,
    )
    assert en_curso.estado == "EN_CURSO"
    assert en_curso.iniciado_en is not None

    suspendido = async_to_sync(orquestador_encuentros.cambiar_estado_encuentro_proceso)(
        str(encuentro.id),
        "SUSPENDIDO",
        usuario_admin_competencias,
    )
    assert suspendido.estado == "SUSPENDIDO"
    assert suspendido.estado_pre_suspension == "EN_CURSO"

    reanudado = async_to_sync(orquestador_encuentros.cambiar_estado_encuentro_proceso)(
        str(encuentro.id),
        "EN_CURSO",
        usuario_admin_competencias,
    )
    assert reanudado.estado == "EN_CURSO"
    assert reanudado.estado_pre_suspension is None


@pytest.mark.django_db
def test_encuentro_programado_puede_volver_al_borrador_sin_horario(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a programmed encounter WHEN: it goes back to the draft THEN: the
    schedule is removed."""
    from modules.competencias.domain.schemas.competencias_schemas import (
        EncuentroProgramacionData,
    )
    from modules.competencias.tests.factories import make_horario_payload

    encuentro = _crear(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        participante_1_id=str(competencia_equipo.id),
    )
    inicio, fin = make_horario_payload()
    async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro.id),
        EncuentroProgramacionData(inicio_programado=inicio, fin_programado=fin),
        usuario_admin_competencias,
        "Programacion inicial del encuentro",
    )

    borrador = async_to_sync(orquestador_encuentros.cambiar_estado_encuentro_proceso)(
        str(encuentro.id),
        "BORRADOR",
        usuario_admin_competencias,
        "Desprogramacion administrativa del encuentro",
    )

    assert borrador.estado == "BORRADOR"
    assert borrador.inicio_programado is None
    assert borrador.fin_programado is None


@pytest.mark.django_db
def test_transicion_invalida_de_encuentro_es_rechazada(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
):
    """GIVEN: a draft WHEN: it starts without a schedule THEN: it is refused."""
    encuentro = _crear(orquestador_encuentros, ronda, usuario_admin_competencias)

    with pytest.raises(InvalidStateTransitionError):
        async_to_sync(orquestador_encuentros.cambiar_estado_encuentro_proceso)(
            str(encuentro.id),
            "EN_CURSO",
            usuario_admin_competencias,
        )


@pytest.mark.django_db
def test_encuentro_no_se_finaliza_sin_ganador(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a running encounter WHEN: it is finished without a winner THEN: refused."""
    from modules.competencias.domain.schemas.competencias_schemas import (
        EncuentroProgramacionData,
    )
    from modules.competencias.tests.factories import make_horario_payload

    encuentro = _crear(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        participante_1_id=str(competencia_equipo.id),
    )
    inicio, fin = make_horario_payload()
    async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro.id),
        EncuentroProgramacionData(inicio_programado=inicio, fin_programado=fin),
        usuario_admin_competencias,
        "Programacion inicial del encuentro",
    )
    async_to_sync(orquestador_encuentros.cambiar_estado_encuentro_proceso)(
        str(encuentro.id),
        "EN_CURSO",
        usuario_admin_competencias,
    )

    with pytest.raises(InvalidWinnerError):
        async_to_sync(orquestador_encuentros.cambiar_estado_encuentro_proceso)(
            str(encuentro.id),
            "FINALIZADO",
            usuario_admin_competencias,
        )


# ── Guarded deletion ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_borrador_sin_uso_se_puede_eliminar(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
):
    """GIVEN: an unused draft WHEN: it is deleted THEN: it goes."""
    encuentro = _crear(orquestador_encuentros, ronda, usuario_admin_competencias)

    async_to_sync(orquestador_encuentros.eliminar_encuentro_proceso)(
        str(encuentro.id),
        usuario_admin_competencias,
    )

    assert not Encuentro.objects.filter(id=encuentro.id).exists()


@pytest.mark.django_db
def test_borrador_con_participantes_no_se_puede_eliminar(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a draft with a team WHEN: it is deleted THEN: it is refused."""
    encuentro = _crear(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        participante_1_id=str(competencia_equipo.id),
    )

    with pytest.raises(DeleteNotAllowedError):
        async_to_sync(orquestador_encuentros.eliminar_encuentro_proceso)(
            str(encuentro.id),
            usuario_admin_competencias,
        )
