"""
Integration tests — portabilidad de las restricciones e índices del módulo.

El cuadro eliminatorio se guarda en SQLite (desarrollo) y en PostgreSQL
(producción). Las restricciones del diseño deben ser PORTABLES: los mismos
índices, unicidades y checks deben poder crearse en los dos motores sin SQL
manual ni sintaxis específica de un motor.

Este archivo no necesita un servidor PostgreSQL: renderiza el DDL de la
migración inicial con el ``schema_editor`` de PostgreSQL en modo ``collect_sql``
(sin abrir conexión) y lo compara con el DDL de SQLite. Si alguien introduce
una restricción que sólo funciona en un motor, el test falla.

Referencia: design "Restricciones" / "Índices" + contract/PLAN_REFACTORIZACION.md.
"""
import re

import pytest
from django.db import connections
from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgresDatabaseWrapper,
)
from django.db.migrations.loader import MigrationLoader
from django.db.models.expressions import RawSQL
from django.test import override_settings

from modules.competencias.domain.models import (
    Competencia,
    CompetenciaEquipo,
    Encuentro,
    Ronda,
)

MIGRACION_INICIAL = ("competencias", "0001_initial")

TABLAS_ESPERADAS = {
    "competencias",
    "competencia_equipos",
    "rondas",
    "encuentros",
    "competencias_historicalcompetencia",
    "competencias_historicalcompetenciaequipo",
    "competencias_historicalronda",
    "competencias_historicalencuentro",
}

INDICES_ESPERADOS = {
    "ix_comp_evt_disc_cat_est_fecha",
    "ix_comp_equipo_comp_est_orden",
    "ix_ronda_comp_est_orden",
    "ix_enc_estr_ini_fin",
}

RESTRICCIONES_ESPERADAS = {
    "uq_competencia_evento_disciplina_categoria_nombre",
    "uq_competencia_equipo_competencia_equipo",
    "uq_competencia_equipo_competencia_orden_activo",
    "uq_ronda_competencia_etiqueta",
    "uq_ronda_competencia_orden",
    "uq_encuentro_ronda_orden",
    "ck_encuentro_participantes_distintos",
    "ck_encuentro_horario_intervalo",
    "ck_encuentro_enlace_slot",
    "ck_encuentro_ganador_en_slot",
}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _estado_inicial():
    """State of the project right BEFORE `competencias.0001_initial`.

    The dependencies are resolved through the migration graph so the swappable
    dependency (`usuarios.__first__`) is replaced by its real first migration.

    The suite runs with `--nomigrations` (the tables are created straight from
    the models), so the migration disk must be enabled explicitly.
    """
    with override_settings(MIGRATION_MODULES={}):
        loader = MigrationLoader(None, ignore_no_migrations=True)
        loader.build_graph()
        migration = loader.disk_migrations[MIGRACION_INICIAL]

        dependencias = []
        for padre in migration.dependencies:
            resuelto = loader.check_key(padre, migration.app_label)
            if resuelto is not None:
                dependencias.append(resuelto)

        return loader, migration, loader.project_state(nodes=dependencias)


def _render_ddl(conexion, loader, migration, estado):
    """Render the DDL of the migration with the given connection's dialect."""
    editor = conexion.schema_editor(collect_sql=True)
    editor.deferred_sql = []
    migration.apply(estado, editor)
    return "\n".join(editor.collected_sql)


def _conexion_postgres_offline():
    """PostgreSQL connection wrapper that NEVER opens a socket.

    It is registered under a dedicated alias so Django can resolve it from the
    schema editor, and it is removed again by the caller.
    """
    configuracion = dict(connections["default"].settings_dict)
    configuracion.update(
        {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "offline_ddl",
            "USER": "offline",
            "PASSWORD": "offline",
            "HOST": "localhost",
            "PORT": "5432",
            "OPTIONS": {},
            "TEST": {},
        }
    )
    connections.databases["pg_offline"] = configuracion
    return PostgresDatabaseWrapper(configuracion, alias="pg_offline")


def _inventario(ddl):
    """Extract the named design artifacts from backend-specific rendered DDL."""
    tablas, indices, restricciones = set(), set(), set()

    for nombre in re.findall(r'CREATE TABLE "([^"]+)"', ddl):
        # SQLite rebuilds tables as new__* when adding constraints.
        if not nombre.startswith("new__"):
            tablas.add(nombre)

    for nombre in re.findall(r'CREATE (?:UNIQUE )?INDEX "([^"]+)"', ddl):
        if nombre in INDICES_ESPERADOS:
            indices.add(nombre)
        if nombre in RESTRICCIONES_ESPERADAS:
            restricciones.add(nombre)

    for nombre in re.findall(r'CONSTRAINT "([^"]+)"', ddl):
        if nombre in RESTRICCIONES_ESPERADAS:
            restricciones.add(nombre)

    return tablas, indices, restricciones


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_el_ddl_de_sqlite_contiene_las_cuatro_tablas_y_sus_historicas():
    """GIVEN: the initial migration WHEN: it is rendered in SQLite THEN: 8 tables."""
    loader, migration, estado = _estado_inicial()
    ddl = _render_ddl(connections["default"], loader, migration, estado)

    tablas, _, _ = _inventario(ddl)

    assert TABLAS_ESPERADAS <= tablas


@pytest.mark.django_db
def test_el_ddl_de_postgres_contiene_las_cuatro_tablas_y_sus_historicas():
    """GIVEN: the initial migration WHEN: it is rendered in PostgreSQL THEN: 8 tables.

    No PostgreSQL server is needed: the DDL is rendered offline with the
    PostgreSQL schema editor.
    """
    loader, migration, estado = _estado_inicial()
    conexion = _conexion_postgres_offline()
    try:
        ddl = _render_ddl(conexion, loader, migration, estado)
    finally:
        connections.databases.pop("pg_offline", None)

    tablas, _, _ = _inventario(ddl)

    assert TABLAS_ESPERADAS <= tablas


@pytest.mark.django_db
def test_las_restricciones_e_indices_son_portables_entre_sqlite_y_postgres():
    """GIVEN: the design constraints WHEN: both dialects render them THEN: same set."""
    loader, migration, estado = _estado_inicial()

    ddl_sqlite = _render_ddl(connections["default"], loader, migration, estado)

    conexion = _conexion_postgres_offline()
    try:
        ddl_postgres = _render_ddl(conexion, loader, migration, estado)
    finally:
        connections.databases.pop("pg_offline", None)

    tablas_sqlite, indices_sqlite, restricciones_sqlite = _inventario(ddl_sqlite)
    tablas_postgres, indices_postgres, restricciones_postgres = _inventario(ddl_postgres)

    assert tablas_sqlite == tablas_postgres
    assert indices_sqlite == indices_postgres
    assert restricciones_sqlite == restricciones_postgres


@pytest.mark.django_db
def test_los_indices_del_diseno_existen_en_el_ddl_de_postgres():
    """GIVEN: the design indexes WHEN: PostgreSQL renders them THEN: all exist."""
    loader, migration, estado = _estado_inicial()
    conexion = _conexion_postgres_offline()
    try:
        ddl = _render_ddl(conexion, loader, migration, estado)
    finally:
        connections.databases.pop("pg_offline", None)

    _, indices, _ = _inventario(ddl)

    assert INDICES_ESPERADOS <= indices


@pytest.mark.django_db
def test_las_restricciones_del_diseno_existen_en_el_ddl_de_postgres():
    """GIVEN: the design constraints WHEN: PostgreSQL renders them THEN: all exist."""
    loader, migration, estado = _estado_inicial()
    conexion = _conexion_postgres_offline()
    try:
        ddl = _render_ddl(conexion, loader, migration, estado)
    finally:
        connections.databases.pop("pg_offline", None)

    _, _, restricciones = _inventario(ddl)

    assert RESTRICCIONES_ESPERADAS <= restricciones


@pytest.mark.django_db
def test_la_unicidad_case_insensitive_se_expresa_con_lower_en_postgres():
    """GIVEN: the case-insensitive identity WHEN: Postgres renders it THEN: LOWER().

    `Lower("nombre")` is the portable way to express the case-insensitive
    uniqueness: it is supported by SQLite and PostgreSQL alike.
    """
    loader, migration, estado = _estado_inicial()
    conexion = _conexion_postgres_offline()
    try:
        ddl = _render_ddl(conexion, loader, migration, estado)
    finally:
        connections.databases.pop("pg_offline", None)

    assert "LOWER(" in ddl
    assert "uq_competencia_evento_disciplina_categoria_nombre" in ddl


@pytest.mark.django_db
def test_la_unicidad_parcial_de_orden_se_expresa_con_where_en_postgres():
    """GIVEN: the partial uniqueness of the order WHEN: Postgres renders it THEN: WHERE.

    A conditional `UniqueConstraint` becomes a partial unique index in both
    engines; the predicate is part of the constraint, not of the application.
    """
    loader, migration, estado = _estado_inicial()
    conexion = _conexion_postgres_offline()
    try:
        ddl = _render_ddl(conexion, loader, migration, estado)
    finally:
        connections.databases.pop("pg_offline", None)

    linea = next(
        linea
        for linea in ddl.splitlines()
        if "uq_competencia_equipo_competencia_orden_activo" in linea
    )

    assert "WHERE" in linea
    assert "ACTIVO" in linea


@pytest.mark.django_db
def test_no_hay_sql_manual_ni_restricciones_deprecated_en_los_modelos():
    """GIVEN: the module models WHEN: the Meta is inspected THEN: portable only.

    `CheckConstraint(check=...)` is deprecated since Django 5.1 and `RawSQL` is
    vendor-specific: neither is allowed in the bracket models.
    """
    from django.db.models import CheckConstraint

    modelos = (Competencia, CompetenciaEquipo, Ronda, Encuentro)

    for modelo in modelos:
        for restriccion in modelo._meta.constraints:
            assert not isinstance(restriccion.condition, RawSQL)
            if isinstance(restriccion, CheckConstraint):
                assert restriccion.condition is not None
