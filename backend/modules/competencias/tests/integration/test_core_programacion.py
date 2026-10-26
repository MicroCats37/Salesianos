"""
Integration tests — scheduling of the encounters (Phase 1).

The intervals are SEMI-OPEN: two encounters that only touch are valid, two
that overlap are not. The check is PORTABLE: a physical team cannot play
two matches at the same time even when the encounters belong to two
different competitions of the same day.
"""
from datetime import datetime, timedelta

import pytest
from asgiref.sync import async_to_sync
from django.utils import timezone

from modules.competencias.domain.exceptions import (
    EquipoSolapadoError,
    InvalidScheduleError,
    InvalidStateTransitionError,
    ReasonRequiredError,
)
from modules.competencias.domain.models import CompetenciaEquipo, Encuentro, Ronda
from modules.competencias.domain.schemas.competencias_schemas import (
    EncuentroCreateData,
    EncuentroProgramacionData,
)

DIA = timezone.make_aware(datetime(2026, 11, 16, 10, 0))


def _horario(hora: int, duracion_horas: int = 1):
    """Return a valid interval of the day of the competition."""
    inicio = DIA.replace(hour=hora)
    return EncuentroProgramacionData(
        inicio_programado=inicio,
        fin_programado=inicio + timedelta(hours=duracion_horas),
    )


def _crear_encuentro(orquestador, ronda, actor, orden, entrada_1=None, entrada_2=None):
    """Create an encounter through the orchestrator."""
    data = EncuentroCreateData(
        orden=orden,
        participante_1_id=str(entrada_1.id) if entrada_1 else None,
        participante_2_id=str(entrada_2.id) if entrada_2 else None,
    )
    return async_to_sync(orquestador.crear_encuentro_proceso)(
        str(ronda.id),
        data,
        actor,
    )


def _programar(orquestador, encuentro, actor, horario, motivo="Programacion del encuentro"):
    """Schedule the encounter through the orchestrator."""
    return async_to_sync(orquestador.programar_encuentro_proceso)(
        str(encuentro.id),
        horario,
        actor,
        motivo,
    )


# ── Basic scheduling ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_encuentro_se_programa_y_pasa_a_programado(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a draft WHEN: it is scheduled THEN: it becomes programmed."""
    encuentro = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=competencia_equipo,
    )

    resultado = _programar(
        orquestador_encuentros,
        encuentro,
        usuario_admin_competencias,
        _horario(10),
    )

    assert resultado.estado == "PROGRAMADO"
    assert resultado.inicio_programado == DIA
    assert resultado.fin_programado == DIA + timedelta(hours=1)
    assert resultado.version == encuentro.version + 1


@pytest.mark.django_db
def test_horario_con_intervalo_no_positivo_es_rechazado(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: an empty interval WHEN: it is scheduled THEN: it is invalid."""
    encuentro = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=competencia_equipo,
    )
    horario = EncuentroProgramacionData(
        inicio_programado=DIA,
        fin_programado=DIA,
    )

    with pytest.raises(InvalidScheduleError):
        _programar(orquestador_encuentros, encuentro, usuario_admin_competencias, horario)


@pytest.mark.django_db
def test_horario_en_otro_dia_es_rechazado(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a day other than the one of the bracket THEN: it is invalid."""
    encuentro = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=competencia_equipo,
    )
    otro_dia = DIA + timedelta(days=1)

    with pytest.raises(InvalidScheduleError):
        _programar(
            orquestador_encuentros,
            encuentro,
            usuario_admin_competencias,
            EncuentroProgramacionData(
                inicio_programado=otro_dia,
                fin_programado=otro_dia + timedelta(hours=1),
            ),
        )


@pytest.mark.django_db
def test_programar_exige_motivo(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a schedule change WHEN: it has no motive THEN: it is refused."""
    encuentro = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=competencia_equipo,
    )

    with pytest.raises(ReasonRequiredError):
        async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
            str(encuentro.id),
            _horario(10),
            usuario_admin_competencias,
        )


# ── Overlap ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_el_mismo_equipo_no_puede_solaparse_consigo_mismo(
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    equipo_competencia,
    equipo_competencia_2,
):
    """GIVEN: two encounters with a shared team WHEN: they overlap THEN: refused."""
    entrada_1 = async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id), str(equipo_competencia.id), 1, usuario_admin_competencias
    )
    entrada_2 = async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id), str(equipo_competencia_2.id), 2, usuario_admin_competencias
    )
    primero = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=entrada_1,
        entrada_2=entrada_2,
    )
    segundo = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        2,
        entrada_1=entrada_1,
    )

    _programar(orquestador_encuentros, primero, usuario_admin_competencias, _horario(10))

    with pytest.raises(EquipoSolapadoError):
        _programar(
            orquestador_encuentros,
            segundo,
            usuario_admin_competencias,
            _horario(10, duracion_horas=2),
        )


@pytest.mark.django_db
def test_equipos_distintos_pueden_jugar_a_la_vez(
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    equipo_competencia,
    equipo_competencia_2,
):
    """GIVEN: two encounters with different teams WHEN: they overlap THEN: allowed."""
    entrada_1 = async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id), str(equipo_competencia.id), 1, usuario_admin_competencias
    )
    entrada_2 = async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id), str(equipo_competencia_2.id), 2, usuario_admin_competencias
    )
    primero = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=entrada_1,
    )
    segundo = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        2,
        entrada_2=entrada_2,
    )

    _programar(orquestador_encuentros, primero, usuario_admin_competencias, _horario(10))
    resultado = _programar(
        orquestador_encuentros,
        segundo,
        usuario_admin_competencias,
        _horario(10),
    )

    assert resultado.estado == "PROGRAMADO"


@pytest.mark.django_db
def test_contacto_exacto_es_valido(
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    equipo_competencia,
    equipo_competencia_2,
):
    """GIVEN: two encounters that only touch WHEN: they are scheduled THEN: allowed."""
    entrada_1 = async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id), str(equipo_competencia.id), 1, usuario_admin_competencias
    )
    primero = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=entrada_1,
    )
    segundo = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        2,
        entrada_1=entrada_1,
    )

    _programar(orquestador_encuentros, primero, usuario_admin_competencias, _horario(10))
    resultado = _programar(
        orquestador_encuentros,
        segundo,
        usuario_admin_competencias,
        _horario(11),
    )

    assert resultado.estado == "PROGRAMADO"


@pytest.mark.django_db
def test_encuentro_cancelado_no_reserva_el_horario(
    orquestador_encuentros,
    orquestador_competencia_equipos,
    usuario_admin_competencias,
    competencia,
    ronda,
    equipo_competencia,
):
    """GIVEN: a cancelled encounter WHEN: the team plays again THEN: it is allowed."""
    entrada_1 = async_to_sync(orquestador_competencia_equipos.incorporar_equipo_proceso)(
        str(competencia.id), str(equipo_competencia.id), 1, usuario_admin_competencias
    )
    primero = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=entrada_1,
    )
    segundo = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        2,
        entrada_1=entrada_1,
    )

    _programar(orquestador_encuentros, primero, usuario_admin_competencias, _horario(10))
    async_to_sync(orquestador_encuentros.cambiar_estado_encuentro_proceso)(
        str(primero.id),
        "CANCELADO",
        usuario_admin_competencias,
        "Cancelacion administrativa del encuentro",
    )

    resultado = _programar(
        orquestador_encuentros,
        segundo,
        usuario_admin_competencias,
        _horario(10),
    )

    assert resultado.estado == "PROGRAMADO"


# ── Portable overlap ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_el_solape_es_portable_entre_competencias(
    orquestador_encuentros,
    usuario_admin_competencias,
    competencia,
    competencia_2,
    ronda,
    equipo_competencia,
):
    """GIVEN: the same team in two brackets WHEN: they overlap THEN: refused."""
    entrada_ajena = CompetenciaEquipo.objects.create(
        competencia=competencia_2,
        equipo=equipo_competencia,
        orden=1,
        estado="ACTIVO",
    )
    ronda_2 = Ronda.objects.create(
        competencia=competencia_2,
        etiqueta="Primera ronda",
        orden=1,
        estado="ACTIVA",
    )
    encuentro_ajeno = Encuentro.objects.create(
        ronda=ronda_2,
        orden=1,
        participante_1=entrada_ajena,
        estado="BORRADOR",
    )

    entrada = CompetenciaEquipo.objects.create(
        competencia=competencia,
        equipo=equipo_competencia,
        orden=1,
        estado="ACTIVO",
    )
    encuentro = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=entrada,
    )

    async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro_ajeno.id),
        _horario(10),
        usuario_admin_competencias,
        "Programacion del encuentro de la otra competencia",
    )

    with pytest.raises(EquipoSolapadoError):
        _programar(orquestador_encuentros, encuentro, usuario_admin_competencias, _horario(10))


# ── Idempotency and terminal states ──────────────────────────────────────────


@pytest.mark.django_db
def test_reprogramar_el_mismo_horario_es_idempotente(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a programmed encounter WHEN: it is programmed again THEN: no write."""
    encuentro = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=competencia_equipo,
    )
    primero = _programar(
        orquestador_encuentros,
        encuentro,
        usuario_admin_competencias,
        _horario(10),
    )

    repetido = _programar(
        orquestador_encuentros,
        encuentro,
        usuario_admin_competencias,
        _horario(10),
    )

    assert repetido.version == primero.version
    assert repetido.estado == "PROGRAMADO"


@pytest.mark.django_db
def test_encuentro_cancelado_no_se_puede_reprogramar(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a cancelled encounter WHEN: it is scheduled THEN: it is refused."""
    encuentro = _crear_encuentro(
        orquestador_encuentros,
        ronda,
        usuario_admin_competencias,
        1,
        entrada_1=competencia_equipo,
    )
    async_to_sync(orquestador_encuentros.cambiar_estado_encuentro_proceso)(
        str(encuentro.id),
        "CANCELADO",
        usuario_admin_competencias,
        "Cancelacion administrativa del encuentro",
    )

    with pytest.raises(InvalidStateTransitionError):
        _programar(
            orquestador_encuentros,
            encuentro,
            usuario_admin_competencias,
            _horario(10),
        )
