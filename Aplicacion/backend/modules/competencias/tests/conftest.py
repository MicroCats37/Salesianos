"""Registro de fixtures del módulo `competencias`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3

Este `conftest.py` sólo importa y registra los módulos de fixtures; las
fixtures reales viven en `fixtures/`.
"""

import pytest

from modules.competencias.tests.fixtures.competencias_fixtures import (  # noqa: F401
    competencia,
    disciplina,
    disciplina_exigente,
    disciplina_inactiva,
    disciplina_otra_edicion,
    edicion_otra,
    edicion_publicada,
    encuentro,
    encuentro_final,
    equipo,
    equipo_2,
    equipo_2_en_cuadro,
    equipo_plantilla_incompleta,
    equipo_cancelado,
    equipo_en_cuadro,
    equipo_otra_edicion,
    equipo_sin_plantilla,
    evento,
    injector,
    inscripcion,
    inscripcion_2,
    inscripcion_cancelada,
    jornada,
    jornada_posterior,
    paquete,
    paquete_2,
    participacion,
    participacion_2,
    participacion_plantilla_incompleta,
    persona,
    persona_2,
    persona_3,
    persona_4,
    ronda,
    ronda_final,
    usuario_admin,
    usuario_ajeno,
)


@pytest.fixture(autouse=True)
def permitir_orm_sync_en_harness_async(monkeypatch):
    """The legacy async tests use synchronous assertions after async flows.

    Production ORM access remains guarded; this only keeps test setup and
    assertions on the same Django connection after async service calls.
    """
    monkeypatch.setenv("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
