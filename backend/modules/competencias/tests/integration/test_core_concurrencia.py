"""
Integration tests — concurrency, optimistic lock and idempotency (Phase 1).

Three guarantees of the spec are locked down here:

- a repeated command with the same intention is idempotent (no second write),
- an update over a stale version fails with a conflict and WITHOUT partial
  effects,
- the teams are locked in ascending UUID order so two concurrent schedulers
  can never deadlock.
"""
import pytest
from asgiref.sync import async_to_sync
from django.db import transaction

from datetime import timedelta

from modules.competencias.domain.exceptions import ResourceChangedError
from modules.competencias.domain.models import CompetenciaEquipo, Encuentro
from modules.competencias.domain.schemas.competencias_schemas import (
    EncuentroCreateData,
    EncuentroProgramacionData,
)
from modules.competencias.domain.services.core.programacion_service import (
    ProgramacionCoreService,
)
from modules.competencias.tests.factories import make_horario_payload


# ── Optimistic lock ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_dos_ediciones_con_la_misma_version_solo_aplica_una(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: two editors WHEN: both confirm THEN: only the first one applies."""
    encuentro = async_to_sync(orquestador_encuentros.crear_encuentro_proceso)(
        str(ronda.id),
        EncuentroCreateData(orden=1),
        usuario_admin_competencias,
    )

    inicio, fin = make_horario_payload()
    horario = EncuentroProgramacionData(
        inicio_programado=inicio,
        fin_programado=fin,
    )
    horario_distinto = EncuentroProgramacionData(
        inicio_programado=inicio + timedelta(hours=4),
        fin_programado=fin + timedelta(hours=4),
    )

    # First editor: it works on the current version.
    async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro.id),
        horario,
        usuario_admin_competencias,
        "Programacion del primer administrador",
        encuentro.version,
    )

    # Second editor: it still works on the version it read before and it
    # wants a DIFFERENT schedule.
    with pytest.raises(ResourceChangedError):
        async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
            str(encuentro.id),
            horario_distinto,
            usuario_admin_competencias,
            "Programacion del segundo administrador",
            encuentro.version,
        )

    # The conflict left no partial effect: the schedule is the one of the
    # first editor and the version was bumped exactly once.
    guardado = Encuentro.objects.get(id=encuentro.id)
    assert guardado.inicio_programado == inicio
    assert guardado.fin_programado == fin
    assert guardado.version == encuentro.version + 1


@pytest.mark.django_db
def test_programacion_con_version_obsoleta_no_escribe_nada(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a stale version WHEN: the schedule is written THEN: nothing changes."""
    encuentro = async_to_sync(orquestador_encuentros.crear_encuentro_proceso)(
        str(ronda.id),
        EncuentroCreateData(orden=1),
        usuario_admin_competencias,
    )

    inicio, fin = make_horario_payload()
    with pytest.raises(ResourceChangedError):
        async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
            str(encuentro.id),
            EncuentroProgramacionData(
                inicio_programado=inicio,
                fin_programado=fin,
            ),
            usuario_admin_competencias,
            "Programacion con version obsoleta",
            encuentro.version + 5,
        )

    guardado = Encuentro.objects.get(id=encuentro.id)
    assert guardado.inicio_programado is None
    assert guardado.fin_programado is None
    assert guardado.estado == "BORRADOR"
    assert guardado.version == encuentro.version


# ── Idempotency ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_comando_repetido_es_idempotente(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: the same command twice WHEN: it is repeated THEN: it writes once."""
    encuentro = async_to_sync(orquestador_encuentros.crear_encuentro_proceso)(
        str(ronda.id),
        EncuentroCreateData(orden=1),
        usuario_admin_competencias,
    )
    inicio, fin = make_horario_payload()
    horario = EncuentroProgramacionData(
        inicio_programado=inicio,
        fin_programado=fin,
    )

    primero = async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro.id),
        horario,
        usuario_admin_competencias,
        "Programacion del encuentro",
    )
    segundo = async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro.id),
        horario,
        usuario_admin_competencias,
        "Programacion del encuentro",
    )

    assert segundo.version == primero.version
    assert Encuentro.objects.get(id=encuentro.id).version == primero.version


@pytest.mark.django_db
def test_reintento_con_version_obsoleta_es_idempotente(
    orquestador_encuentros,
    usuario_admin_competencias,
    ronda,
    competencia_equipo,
):
    """GIVEN: a retry of the same intention WHEN: the version is stale THEN: no-op.

    The design compares the COMPLETE intention first: when it already
    matches, the command returns without writing anything — even if the
    version the caller read is already stale.
    """
    encuentro = async_to_sync(orquestador_encuentros.crear_encuentro_proceso)(
        str(ronda.id),
        EncuentroCreateData(orden=1),
        usuario_admin_competencias,
    )
    inicio, fin = make_horario_payload()
    horario = EncuentroProgramacionData(
        inicio_programado=inicio,
        fin_programado=fin,
    )

    primero = async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro.id),
        horario,
        usuario_admin_competencias,
        "Programacion del encuentro",
    )
    repetido = async_to_sync(orquestador_encuentros.programar_encuentro_proceso)(
        str(encuentro.id),
        horario,
        usuario_admin_competencias,
        "Programacion del encuentro",
        encuentro.version,
    )

    assert repetido.version == primero.version
    assert Encuentro.objects.get(id=encuentro.id).version == primero.version


# ── Deterministic locking order ──────────────────────────────────────────────


@pytest.mark.django_db
def test_los_equipos_se_bloquean_en_orden_por_uuid(
    competencia,
    equipo_competencia,
    equipo_competencia_2,
):
    """GIVEN: several teams WHEN: they are locked THEN: the order is by UUID."""
    equipos = [equipo_competencia, equipo_competencia_2]
    ids = [str(equipo.id) for equipo in equipos]

    with transaction.atomic():
        bloqueados = ProgramacionCoreService.bloquear_equipos(list(reversed(ids)))

    orden = [str(equipo.id) for equipo in bloqueados]
    assert orden == sorted(orden)
    assert set(orden) == set(ids)


@pytest.mark.django_db
def test_los_equipos_del_encuentro_son_los_equipos_subyacentes(
    competencia,
    ronda,
    equipo_competencia,
    equipo_competencia_2,
):
    """GIVEN: an encounter WHEN: its teams are read THEN: they are the real ones."""
    entrada_1 = CompetenciaEquipo.objects.create(
        competencia=competencia,
        equipo=equipo_competencia,
        orden=1,
        estado="ACTIVO",
    )
    entrada_2 = CompetenciaEquipo.objects.create(
        competencia=competencia,
        equipo=equipo_competencia_2,
        orden=2,
        estado="ACTIVO",
    )
    encuentro = Encuentro.objects.create(
        ronda=ronda,
        orden=1,
        participante_1=entrada_1,
        participante_2=entrada_2,
        estado="BORRADOR",
    )

    equipos = ProgramacionCoreService.equipos_de_encuentro(encuentro)

    assert set(equipos) == {str(equipo_competencia.id), str(equipo_competencia_2.id)}
