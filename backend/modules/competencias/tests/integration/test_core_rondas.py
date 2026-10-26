"""
Integration tests — commands of the rounds of the bracket (Phase 1).

A round has a label and an order unique inside the competition and it is
invalidated — never deleted — when it leaves the bracket, so the history of
the bracket is preserved.
"""
import pytest
from asgiref.sync import async_to_sync

from modules.competencias.domain.exceptions import (
    CompetenciaDuplicadaError,
    DeleteNotAllowedError,
    InvalidStateTransitionError,
    RondaNotFoundError,
)
from modules.competencias.domain.models import Ronda
from modules.competencias.domain.schemas.competencias_schemas import (
    RondaCreateData,
    RondaUpdateData,
)


def _crear(orquestador, competencia, actor, etiqueta="Cuartos de final", orden=1):
    """Create a round through the orchestrator."""
    return async_to_sync(orquestador.crear_ronda_proceso)(
        str(competencia.id),
        RondaCreateData(etiqueta=etiqueta, orden=orden),
        actor,
    )


@pytest.mark.django_db
def test_ronda_se_crea_activa_con_etiqueta_y_orden(
    orquestador_rondas,
    usuario_admin_competencias,
    competencia,
):
    """GIVEN: a competition WHEN: a round is created THEN: it is active."""
    resultado = _crear(orquestador_rondas, competencia, usuario_admin_competencias)

    assert resultado.estado == "ACTIVA"
    assert resultado.etiqueta == "Cuartos de final"
    assert resultado.orden == 1
    assert resultado.version == 1


@pytest.mark.django_db
def test_etiqueta_duplicada_en_la_misma_competencia_es_rechazada(
    orquestador_rondas,
    usuario_admin_competencias,
    competencia,
):
    """GIVEN: a label already used WHEN: it is reused THEN: it conflicts."""
    _crear(orquestador_rondas, competencia, usuario_admin_competencias, orden=1)

    with pytest.raises(CompetenciaDuplicadaError):
        _crear(
            orquestador_rondas,
            competencia,
            usuario_admin_competencias,
            etiqueta="Cuartos de final",
            orden=2,
        )


@pytest.mark.django_db
def test_orden_duplicado_en_la_misma_competencia_es_rechazado(
    orquestador_rondas,
    usuario_admin_competencias,
    competencia,
):
    """GIVEN: an order already used WHEN: it is reused THEN: it conflicts."""
    _crear(orquestador_rondas, competencia, usuario_admin_competencias, orden=1)

    with pytest.raises(CompetenciaDuplicadaError):
        _crear(
            orquestador_rondas,
            competencia,
            usuario_admin_competencias,
            etiqueta="Semifinal",
            orden=1,
        )


@pytest.mark.django_db
def test_ronda_se_invalida_y_conserva_la_historia(
    orquestador_rondas,
    usuario_admin_competencias,
    competencia,
):
    """GIVEN: an active round WHEN: it is invalidated THEN: it is kept."""
    ronda = _crear(orquestador_rondas, competencia, usuario_admin_competencias)

    invalidada = async_to_sync(orquestador_rondas.invalidar_ronda_proceso)(
        str(ronda.id),
        usuario_admin_competencias,
        "Invalidacion de la ronda",
    )

    assert invalidada.estado == "INVALIDADA"
    assert invalidada.version == ronda.version + 1
    assert Ronda.objects.filter(id=ronda.id).exists()
    assert Ronda.objects.get(id=ronda.id).history.count() >= 1


@pytest.mark.django_db
def test_ronda_invalida_no_admite_mas_cambios(
    orquestador_rondas,
    usuario_admin_competencias,
    competencia,
):
    """GIVEN: an invalidated round WHEN: it is edited THEN: it is refused."""
    ronda = _crear(orquestador_rondas, competencia, usuario_admin_competencias)
    async_to_sync(orquestador_rondas.invalidar_ronda_proceso)(
        str(ronda.id),
        usuario_admin_competencias,
        "Invalidacion de la ronda",
    )

    with pytest.raises(InvalidStateTransitionError):
        async_to_sync(orquestador_rondas.actualizar_ronda_proceso)(
            str(ronda.id),
            RondaUpdateData(etiqueta="Nueva etiqueta"),
            usuario_admin_competencias,
        )


@pytest.mark.django_db
def test_ronda_sin_encuentros_se_puede_eliminar(
    orquestador_rondas,
    usuario_admin_competencias,
    competencia,
):
    """GIVEN: a round that was never used WHEN: it is deleted THEN: it goes."""
    ronda = _crear(orquestador_rondas, competencia, usuario_admin_competencias)

    async_to_sync(orquestador_rondas.eliminar_ronda_proceso)(
        str(ronda.id),
        usuario_admin_competencias,
    )

    assert not Ronda.objects.filter(id=ronda.id).exists()


@pytest.mark.django_db
def test_ronda_con_historia_no_se_puede_eliminar(
    orquestador_rondas,
    usuario_admin_competencias,
    competencia,
):
    """GIVEN: a round already changed WHEN: it is deleted THEN: it is refused."""
    ronda = _crear(orquestador_rondas, competencia, usuario_admin_competencias)
    async_to_sync(orquestador_rondas.actualizar_ronda_proceso)(
        str(ronda.id),
        RondaUpdateData(etiqueta="Cuartos de final (editada)"),
        usuario_admin_competencias,
    )

    with pytest.raises(DeleteNotAllowedError):
        async_to_sync(orquestador_rondas.eliminar_ronda_proceso)(
            str(ronda.id),
            usuario_admin_competencias,
        )


@pytest.mark.django_db
def test_ronda_inexistente_da_404(
    orquestador_rondas,
    usuario_admin_competencias,
):
    """GIVEN: an unknown round WHEN: it is edited THEN: it does not exist."""
    with pytest.raises(RondaNotFoundError):
        async_to_sync(orquestador_rondas.actualizar_ronda_proceso)(
            "6f0a1f8e-0000-4000-8000-000000000000",
            RondaUpdateData(etiqueta="No existe"),
            usuario_admin_competencias,
        )
