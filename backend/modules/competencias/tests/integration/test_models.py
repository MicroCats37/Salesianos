"""
Integration tests — models, constraints, indexes and audit trail of
`modules.competencias` (Phase 0: domain foundation).

The bracket is deliberately tolerant with EMPTY and PARTIAL data: an
encounter may exist without participants, without schedule and without
winner. What it must never allow is an ambiguous or duplicated state, and
that is what these tests lock down.
"""
from contextlib import contextmanager
from datetime import date
from io import StringIO

import pytest
from django.apps import apps
from django.core.management import call_command
from django.db import IntegrityError, connection, models, transaction
from django.test import override_settings

from modules.competencias.domain.models import (
    Competencia,
    CompetenciaEquipo,
    Encuentro,
    Ronda,
)
from modules.competencias.tests.factories import (
    HORA_FIN,
    HORA_INICIO,
    make_competencia_equipo_payload,
    make_competencia_payload,
    make_encuentro_payload,
    make_ronda_payload,
)

MODELOS = (Competencia, CompetenciaEquipo, Ronda, Encuentro)


@contextmanager
def _migraciones_habilitadas():
    """Run the block with the real migrations enabled.

    The test suite runs with `--nomigrations` (tables are created straight
    from the models), so the migration disk must be enabled explicitly to
    inspect it.
    """
    with override_settings(MIGRATION_MODULES={}):
        yield


# ── Defaults ───────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_competencia_usa_los_defaults_del_diseno(competencia):
    """GIVEN: a new competition WHEN: it is created THEN: PLANIFICADA and v1."""
    assert competencia.estado == "PLANIFICADA"
    assert competencia.version == 1
    assert competencia.fecha == date(2026, 11, 16)


@pytest.mark.django_db
def test_competencia_equipo_usa_los_defaults_del_diseno(competencia_equipo):
    """GIVEN: a new entry WHEN: it is created THEN: ACTIVO and v1."""
    assert competencia_equipo.estado == "ACTIVO"
    assert competencia_equipo.version == 1


@pytest.mark.django_db
def test_ronda_usa_los_defaults_del_diseno(ronda):
    """GIVEN: a new round WHEN: it is created THEN: ACTIVA and v1."""
    assert ronda.estado == "ACTIVA"
    assert ronda.version == 1


@pytest.mark.django_db
def test_encuentro_usa_los_defaults_del_diseno(encuentro):
    """GIVEN: a new encounter WHEN: it is created THEN: BORRADOR, empty."""
    assert encuentro.estado == "BORRADOR"
    assert encuentro.version == 1
    assert encuentro.es_bye is False
    assert encuentro.marcador_detalle == ""
    assert encuentro.puntaje_1 is None
    assert encuentro.puntaje_2 is None
    assert encuentro.inicio_programado is None
    assert encuentro.fin_programado is None
    assert encuentro.iniciado_en is None
    assert encuentro.finalizado_en is None
    assert encuentro.estado_pre_suspension is None
    assert encuentro.ganador is None
    assert encuentro.siguiente_encuentro is None
    assert encuentro.slot_destino is None
    assert encuentro.ganador_propagado is None


# ── Nullable future bracket slots and byes ────────────────────────────────────


@pytest.mark.django_db
def test_encuentro_sin_participantes_es_valido(ronda):
    """GIVEN: an empty slot WHEN: the encounter is created THEN: it is valid."""
    encuentro = Encuentro.objects.create(ronda=ronda, orden=10)

    assert encuentro.participante_1 is None
    assert encuentro.participante_2 is None
    assert Encuentro.objects.filter(ronda=ronda, orden=10).exists()


@pytest.mark.django_db
def test_encuentro_con_un_solo_participante_es_valido(ronda, competencia_equipo):
    """GIVEN: a partial slot WHEN: it is created THEN: the bracket is editable."""
    encuentro = Encuentro.objects.create(
        ronda=ronda,
        orden=11,
        participante_1=competencia_equipo,
    )

    assert encuentro.participante_2 is None


@pytest.mark.django_db
def test_bye_manual_con_un_solo_participante_es_valido(ronda, competencia_equipo):
    """GIVEN: a manual bye WHEN: it is created THEN: es_bye is recorded."""
    encuentro = Encuentro.objects.create(
        ronda=ronda,
        orden=12,
        participante_1=competencia_equipo,
        es_bye=True,
    )

    assert encuentro.es_bye is True


@pytest.mark.django_db
def test_cuadro_parcial_es_legible_sin_inventar_participantes(
    ronda, competencia_equipo
):
    """GIVEN: a partial bracket WHEN: it is read THEN: the empty slots stay empty."""
    Encuentro.objects.create(ronda=ronda, orden=20)
    Encuentro.objects.create(ronda=ronda, orden=21, participante_1=competencia_equipo)
    Encuentro.objects.create(ronda=ronda, orden=22, es_bye=True)

    encuentros = list(Encuentro.objects.filter(ronda=ronda).order_by("orden"))

    assert len(encuentros) == 3
    assert encuentros[0].participante_1 is None
    assert encuentros[1].participante_2 is None
    assert encuentros[2].es_bye is True


# ── Constraints ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_competencia_duplicada_en_la_misma_identidad_falla(
    competencia, evento_competencia, disciplina_competencia, categoria_competencia
):
    """GIVEN: the same event+discipline+category+name WHEN: it is repeated THEN: error."""
    payload = make_competencia_payload(
        evento_competencia.id,
        disciplina_competencia.id,
        categoria_competencia.id,
        nombre="Eliminatoria F7",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Competencia.objects.create(**payload)


@pytest.mark.django_db
def test_competencia_duplicada_ignora_mayusculas_falla(
    competencia, evento_competencia, disciplina_competencia, categoria_competencia
):
    """GIVEN: the same name in other case WHEN: it is repeated THEN: error."""
    payload = make_competencia_payload(
        evento_competencia.id,
        disciplina_competencia.id,
        categoria_competencia.id,
        nombre="ELIMINATORIA F7",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Competencia.objects.create(**payload)


@pytest.mark.django_db
def test_competencia_con_otra_disciplina_es_valida(
    competencia,
    evento_competencia,
    disciplina_competencia_2,
    categoria_competencia,
):
    """GIVEN: another discipline WHEN: the name is repeated THEN: it is valid."""
    payload = make_competencia_payload(
        evento_competencia.id,
        disciplina_competencia_2.id,
        categoria_competencia.id,
        nombre="Eliminatoria F7",
    )

    creada = Competencia.objects.create(**payload)

    assert creada.pk != competencia.pk


@pytest.mark.django_db
def test_equipo_no_ingresa_dos_veces_a_la_misma_competencia(
    competencia, competencia_equipo, equipo_competencia, equipo_competencia_2
):
    """GIVEN: a team already in the bracket WHEN: it is added again THEN: error."""
    payload = make_competencia_equipo_payload(
        competencia.id, equipo_competencia.id, orden=2
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CompetenciaEquipo.objects.create(**payload)


@pytest.mark.django_db
def test_orden_de_entrada_es_unico_entre_los_activos(
    competencia, competencia_equipo, equipo_competencia_2
):
    """GIVEN: an ACTIVE entry with order 1 WHEN: another takes order 1 THEN: error."""
    payload = make_competencia_equipo_payload(
        competencia.id, equipo_competencia_2.id, orden=1
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CompetenciaEquipo.objects.create(**payload)


@pytest.mark.django_db
def test_orden_de_entrada_se_libera_cuando_el_anterior_se_retira(
    competencia, competencia_equipo, equipo_competencia_2
):
    """GIVEN: a RETIRED entry WHEN: another takes the same order THEN: it is valid."""
    competencia_equipo.estado = "RETIRADO"
    competencia_equipo.save()

    payload = make_competencia_equipo_payload(
        competencia.id, equipo_competencia_2.id, orden=1
    )
    creada = CompetenciaEquipo.objects.create(**payload)

    assert creada.orden == 1


@pytest.mark.django_db
def test_ronda_etiqueta_unica_por_competencia(competencia, ronda):
    """GIVEN: a round WHEN: the label is repeated THEN: error."""
    payload = make_ronda_payload(competencia.id, etiqueta="Cuartos de final", orden=2)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Ronda.objects.create(**payload)


@pytest.mark.django_db
def test_ronda_orden_unico_por_competencia(competencia, ronda):
    """GIVEN: a round WHEN: the order is repeated THEN: error."""
    payload = make_ronda_payload(competencia.id, etiqueta="Semifinal", orden=1)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Ronda.objects.create(**payload)


@pytest.mark.django_db
def test_encuentro_orden_unico_por_ronda(encuentro, ronda, competencia_equipo):
    """GIVEN: an encounter WHEN: the order is repeated in the round THEN: error."""
    payload = make_encuentro_payload(
        ronda.id, orden=1, participante_1_id=competencia_equipo.id
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Encuentro.objects.create(**payload)


@pytest.mark.django_db
def test_encuentro_no_puede_tener_el_mismo_participante_en_los_dos_slots(
    ronda, competencia_equipo
):
    """GIVEN: the same team twice WHEN: it is saved THEN: error."""
    payload = make_encuentro_payload(
        ronda.id,
        orden=30,
        participante_1_id=competencia_equipo.id,
        participante_2_id=competencia_equipo.id,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Encuentro.objects.create(**payload)


@pytest.mark.django_db
def test_encuentro_con_horario_incompleto_falla(ronda):
    """GIVEN: only the start of the schedule WHEN: it is saved THEN: error."""
    payload = make_encuentro_payload(
        ronda.id, orden=31, inicio_programado=HORA_INICIO, fin_programado=None
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Encuentro.objects.create(**payload)


@pytest.mark.django_db
def test_encuentro_con_intervalo_no_positivo_falla(ronda):
    """GIVEN: end <= start WHEN: it is saved THEN: error."""
    payload = make_encuentro_payload(
        ronda.id,
        orden=32,
        inicio_programado=HORA_INICIO,
        fin_programado=HORA_INICIO,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Encuentro.objects.create(**payload)


@pytest.mark.django_db
def test_encuentro_con_horario_completo_es_valido(ronda):
    """GIVEN: a positive interval WHEN: it is saved THEN: it is valid."""
    payload = make_encuentro_payload(
        ronda.id,
        orden=33,
        inicio_programado=HORA_INICIO,
        fin_programado=HORA_FIN,
    )
    encuentro = Encuentro.objects.create(**payload)

    assert encuentro.inicio_programado == HORA_INICIO


@pytest.mark.django_db
def test_encuentro_con_enlace_sin_slot_falla(ronda, encuentro):
    """GIVEN: the next encounter without a slot WHEN: it is saved THEN: error."""
    destino = Encuentro.objects.create(ronda=ronda, orden=40)
    encuentro.siguiente_encuentro = destino
    encuentro.slot_destino = None

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            encuentro.save()


@pytest.mark.django_db
def test_encuentro_con_slot_sin_enlace_falla(ronda, encuentro):
    """GIVEN: a slot without the next encounter WHEN: it is saved THEN: error."""
    encuentro.siguiente_encuentro = None
    encuentro.slot_destino = "PARTICIPANTE_1"

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            encuentro.save()


@pytest.mark.django_db
def test_encuentro_con_enlace_y_slot_es_valido(ronda, encuentro):
    """GIVEN: the link and its slot WHEN: it is saved THEN: it is valid."""
    destino = Encuentro.objects.create(ronda=ronda, orden=41)
    encuentro.siguiente_encuentro = destino
    encuentro.slot_destino = "PARTICIPANTE_1"
    encuentro.save()

    assert encuentro.slot_destino == "PARTICIPANTE_1"


@pytest.mark.django_db
def test_ganador_que_no_ocupa_un_slot_falla(
    ronda, encuentro, competencia, equipo_competencia_2
):
    """GIVEN: a winner outside the slots WHEN: it is saved THEN: error."""
    intruso = CompetenciaEquipo.objects.create(
        competencia=competencia,
        equipo=equipo_competencia_2,
        orden=9,
        estado="ACTIVO",
    )
    encuentro.ganador = intruso

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            encuentro.save()


@pytest.mark.django_db
def test_ganador_que_ocupa_un_slot_es_valido(encuentro, competencia_equipo):
    """GIVEN: a winner that occupies a slot WHEN: it is saved THEN: it is valid."""
    encuentro.ganador = competencia_equipo
    encuentro.save()

    assert encuentro.ganador_id == competencia_equipo.id


@pytest.mark.django_db
def test_puntaje_negativo_falla(ronda, competencia_equipo):
    """GIVEN: a negative score WHEN: it is saved THEN: error (no negatives)."""
    payload = make_encuentro_payload(
        ronda.id, orden=50, participante_1_id=competencia_equipo.id, puntaje_1=-1
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Encuentro.objects.create(**payload)


# ── Meta contracts: tables, indexes, PROTECT and history ─────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize(
    "modelo,tabla",
    [
        (Competencia, "competencias"),
        (CompetenciaEquipo, "competencia_equipos"),
        (Ronda, "rondas"),
        (Encuentro, "encuentros"),
    ],
)
def test_tablas_de_la_base_de_datos(modelo, tabla):
    """GIVEN: the module models WHEN: the table is inspected THEN: the name matches."""
    assert modelo._meta.db_table == tabla


@pytest.mark.django_db
@pytest.mark.parametrize(
    "modelo,indice,campos",
    [
        (
            Competencia,
            "ix_comp_evt_disc_cat_est_fecha",
            ["evento", "disciplina", "categoria", "estado", "fecha"],
        ),
        (
            CompetenciaEquipo,
            "ix_comp_equipo_comp_est_orden",
            ["competencia", "estado", "orden"],
        ),
        (
            Ronda,
            "ix_ronda_comp_est_orden",
            ["competencia", "estado", "orden"],
        ),
        (
            Encuentro,
            "ix_enc_estr_ini_fin",
            ["estado", "inicio_programado", "fin_programado"],
        ),
    ],
)
def test_indices_del_diseno(modelo, indice, campos):
    """GIVEN: the design indexes WHEN: the Meta is inspected THEN: they exist."""
    indices = {index.name: list(index.fields) for index in modelo._meta.indexes}

    assert indice in indices
    assert indices[indice] == campos


@pytest.mark.django_db
@pytest.mark.parametrize("modelo", MODELOS)
def test_todas_las_relaciones_usan_protect(modelo):
    """GIVEN: the module models WHEN: the FKs are inspected THEN: all are PROTECT."""
    relaciones = [
        field
        for field in modelo._meta.get_fields()
        if field.is_relation and field.many_to_one
    ]

    assert relaciones
    for relacion in relaciones:
        assert relacion.remote_field.on_delete is models.PROTECT, relacion.name


@pytest.mark.django_db
@pytest.mark.parametrize("modelo", MODELOS)
def test_todos_los_modelos_tienen_historial(modelo):
    """GIVEN: the module models WHEN: the history is inspected THEN: it exists."""
    historico = apps.get_model("competencias", f"Historical{modelo.__name__}")

    assert historico is not None
    assert modelo.history.model is historico


@pytest.mark.django_db
def test_historial_registra_la_creacion(competencia):
    """GIVEN: a new competition WHEN: it is saved THEN: a '+' record exists."""
    assert competencia.history.count() == 1
    assert competencia.history.latest("history_date").history_type == "+"


@pytest.mark.django_db
def test_historial_registra_actor_motivo_y_cambio(
    competencia, usuario_admin_competencias
):
    """GIVEN: a change with an actor and a motive WHEN: it is saved THEN: it is audited."""
    competencia.nombre = "Eliminatoria F7 (corregida)"
    competencia.save(
        history_user=usuario_admin_competencias,
        history_change_reason="Corrección de nombre por el administrador",
    )

    registro = competencia.history.latest("history_date")

    assert registro.history_type == "~"
    assert registro.history_user_id == usuario_admin_competencias.id
    assert (
        registro.history_change_reason
        == "Corrección de nombre por el administrador"
    )


@pytest.mark.django_db
def test_historial_admite_motivos_largos(competencia, usuario_admin_competencias):
    """GIVEN: a 500-char motive WHEN: it is saved THEN: it is stored complete."""
    motivo = "M" * 500
    competencia.nombre = "Eliminatoria F7 (motivado)"
    competencia.save(
        history_user=usuario_admin_competencias,
        history_change_reason=motivo,
    )

    registro = competencia.history.latest("history_date")

    assert registro.history_change_reason == motivo


@pytest.mark.django_db
def test_los_metadatos_de_historial_no_se_reutilizan_en_otro_save(
    competencia, usuario_admin_competencias
):
    """GIVEN: an audited save WHEN: the instance is saved again THEN: metadata does not leak."""
    competencia.nombre = "Eliminatoria F7 (auditada)"
    competencia.save(
        history_user=usuario_admin_competencias,
        history_change_reason="Corrección administrativa",
    )
    competencia.nombre = "Eliminatoria F7 (sin actor explícito)"
    competencia.save()

    registro = competencia.history.latest("history_date")

    assert registro.history_user_id is None
    assert registro.history_change_reason is None


# ── Migration / model consistency ─────────────────────────────────────────────


@pytest.mark.django_db
def test_no_hay_migraciones_pendientes():
    """GIVEN: the models WHEN: makemigrations runs THEN: nothing is left pending."""
    salida = StringIO()

    with _migraciones_habilitadas():
        try:
            call_command(
                "makemigrations",
                "competencias",
                "--check",
                "--dry-run",
                stdout=salida,
                stderr=salida,
                verbosity=1,
            )
        except SystemExit:  # pragma: no cover - only on drift
            pytest.fail(
                "There are pending migrations for competencias:\n"
                f"{salida.getvalue()}"
            )


@pytest.mark.django_db
def test_la_migracion_inicial_cubre_las_cuatro_tablas():
    """GIVEN: the app WHEN: the migrations are inspected THEN: 0001 creates them."""
    from django.db.migrations.loader import MigrationLoader

    with _migraciones_habilitadas():
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        migraciones = [
            nombre for app, nombre in loader.disk_migrations if app == "competencias"
        ]

        assert migraciones == ["0001_initial"]

        operacion = loader.disk_migrations[("competencias", "0001_initial")]
        modelos_creados = {
            operacion.name
            for operacion in operacion.operations
            if operacion.__class__.__name__ == "CreateModel"
        }

    assert {
        "Competencia",
        "CompetenciaEquipo",
        "Ronda",
        "Encuentro",
        "HistoricalCompetencia",
        "HistoricalCompetenciaEquipo",
        "HistoricalRonda",
        "HistoricalEncuentro",
    } <= modelos_creados


@pytest.mark.django_db
def test_el_historial_acepta_el_motivo_largo_en_la_base_de_datos(
    competencia, usuario_admin_competencias
):
    """GIVEN: the audit motive WHEN: it reaches the DB THEN: nothing is truncated."""
    motivo = "M" * 500
    competencia.nombre = "Eliminatoria F7 (persistido)"
    competencia.save(
        history_user=usuario_admin_competencias,
        history_change_reason=motivo,
    )

    almacenado = (
        competencia.history.filter(history_change_reason=motivo).count()
    )

    assert almacenado == 1


@pytest.mark.django_db
def test_horarios_compartidos_por_equipos_distintos_son_validos(ronda):
    """GIVEN: two encounters at the same time WHEN: they are saved THEN: both exist.

    The overlap rule is a service rule (Phase 1): the model only forbids a
    team against itself.
    """
    primero = Encuentro.objects.create(
        ronda=ronda,
        orden=60,
        inicio_programado=HORA_INICIO,
        fin_programado=HORA_FIN,
    )
    segundo = Encuentro.objects.create(
        ronda=ronda,
        orden=61,
        inicio_programado=HORA_INICIO,
        fin_programado=HORA_FIN,
    )

    assert primero.pk != segundo.pk
    assert primero.inicio_programado == segundo.inicio_programado
