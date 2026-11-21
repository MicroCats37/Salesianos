"""Safety and idempotency contracts of the reference fixture command."""

from datetime import date
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from modules.competencias.domain.models import (
    Competencia,
    EquipoTorneo,
    GrupoTorneo,
    PartidoTorneo,
)
from modules.competencias.data.fixture import load_reference_fixture
from modules.competencias.management.commands.seed_torneo_referencia import Command
from modules.salesianos_fest.domain.models import (
    Categoria,
    Equipo,
    Inscripcion,
    Participacion,
)
from modules.usuarios.domain.models import Persona, Usuario


pytestmark = pytest.mark.django_db
EVENT_DATE = date(2026, 11, 21)


def _run_seed(**options):
    output = StringIO()
    call_command(
        "seed_torneo_referencia",
        stdout=output,
        event_date=options.pop("event_date", EVENT_DATE),
        **options,
    )
    return output.getvalue()


def test_dry_run_informa_el_diff_sin_escribir(catalogo_torneo_referencia):
    output = _run_seed(dry_run=True)

    assert "DRY-RUN" in output
    assert "CANONICALIZED_TEAM_2001A_TO_2011A" in output
    assert Competencia.objects.count() == 0
    assert GrupoTorneo.objects.count() == 0
    assert EquipoTorneo.objects.count() == 0
    assert PartidoTorneo.objects.count() == 0
    assert Inscripcion.objects.count() == 0
    assert Persona.objects.count() == 0


def test_instalacion_aborta_si_un_id_del_fixture_pertenece_a_otra_competencia(
    catalogo_torneo_referencia,
):
    edicion = catalogo_torneo_referencia["edicion"]
    discipline, _package = catalogo_torneo_referencia["catalogs"]["F7M"]
    category = Categoria.objects.create(
        edicion=edicion,
        nombre="Categoría ajena",
        promocion_desde=1975,
        promocion_hasta=2025,
    )
    foreign_competition = Competencia.objects.create(
        edicion=edicion,
        disciplina=discipline,
        categoria=category,
        nombre="Competencia ajena",
        fecha=EVENT_DATE,
    )
    foreign_group_id = load_reference_fixture()["groups"][0]["id"]
    GrupoTorneo.objects.create(
        id=foreign_group_id,
        competencia=foreign_competition,
    )

    with pytest.raises(CommandError, match="datos ajenos"):
        _run_seed(dry_run=True)

    assert (
        GrupoTorneo.objects.get(id=foreign_group_id).competencia_id
        == foreign_competition.id
    )
    assert Competencia.objects.count() == 1


def test_instalacion_aborta_si_una_referencia_seed_apunta_a_una_persona_real(
    catalogo_torneo_referencia,
):
    fixture = load_reference_fixture()
    first_group = fixture["groups"][0]
    first_team = first_group["teams"][0]
    edicion = catalogo_torneo_referencia["edicion"]
    _discipline, package = catalogo_torneo_referencia["catalogs"][
        first_group["competition_code"]
    ]
    person = Persona.objects.create(
        nombres="Delegación",
        apellidos=f"{first_team['label']} {first_group['competition_code']}",
        tipo_documento="DNI",
        numero_documento="87654321",
    )
    reference = (
        f"torneo-referencia-{edicion.slug}-{package.slug}-{first_team['label']}"
    )
    Inscripcion.objects.create(
        edicion=edicion,
        responsable=person,
        paquete=package,
        promocion=catalogo_torneo_referencia["promotions"][
            first_team["promotion_year"]
        ],
        referencia=reference,
    )

    with pytest.raises(CommandError, match="registro sintético seguro"):
        _run_seed()

    assert Competencia.objects.count() == 0
    assert Persona.objects.filter(id=person.id).exists()


def test_instalacion_es_idempotente_y_preserva_fecha_y_uuids(
    catalogo_torneo_referencia,
):
    _run_seed()
    identities = {
        item.nombre: (item.id, item.fecha) for item in Competencia.objects.all()
    }

    output = _run_seed(event_date=date(2027, 1, 1))

    assert "0 creados, 0 actualizados" in output
    assert {
        item.nombre: (item.id, item.fecha) for item in Competencia.objects.all()
    } == identities
    assert GrupoTorneo.objects.count() == 19
    assert EquipoTorneo.objects.count() == 64
    assert PartidoTorneo.objects.filter(etapa="group").count() == 80
    assert PartidoTorneo.objects.exclude(etapa="group").count() == 22
    assert PartidoTorneo.objects.count() == 102


def test_reset_es_idempotente_y_preserva_los_uuids_de_competencia(
    catalogo_torneo_referencia,
):
    _run_seed()
    competition_ids = set(Competencia.objects.values_list("id", flat=True))

    _run_seed(reset_fixture=True, confirm_reset_fixture=True)
    first_counts = (
        GrupoTorneo.objects.count(),
        EquipoTorneo.objects.count(),
        PartidoTorneo.objects.count(),
        Inscripcion.objects.filter(referencia__startswith="torneo-referencia-").count(),
    )
    _run_seed(reset_fixture=True, confirm_reset_fixture=True)

    assert set(Competencia.objects.values_list("id", flat=True)) == competition_ids
    assert first_counts == (19, 64, 102, 64)
    assert (
        GrupoTorneo.objects.count(),
        EquipoTorneo.objects.count(),
        PartidoTorneo.objects.count(),
        Inscripcion.objects.filter(referencia__startswith="torneo-referencia-").count(),
    ) == first_counts


def test_reset_reemplaza_las_identidades_creadas_por_el_seed_anterior(
    catalogo_torneo_referencia,
):
    _run_seed()
    inscription = Inscripcion.objects.filter(
        referencia__contains="-futbol-7-masculino-"
    ).first()
    legacy_person = inscription.responsable
    legacy_person.tipo_documento = "DNI"
    legacy_person.numero_documento = "99000000"
    legacy_person.save(update_fields=["tipo_documento", "numero_documento"])

    _run_seed(reset_fixture=True, confirm_reset_fixture=True)

    assert not Persona.objects.filter(id=legacy_person.id).exists()
    recreated = Inscripcion.objects.get(referencia=inscription.referencia)
    assert recreated.responsable.tipo_documento == "PAS"
    assert recreated.responsable.numero_documento.startswith("SEED")


def test_reset_no_borra_inscripciones_personas_equipos_ni_usuarios_reales(
    catalogo_torneo_referencia,
):
    _run_seed()
    edicion = catalogo_torneo_referencia["edicion"]
    discipline, package = catalogo_torneo_referencia["catalogs"]["F7M"]
    promotion = catalogo_torneo_referencia["promotions"][1999]
    category = discipline.competencias.get().categoria
    person = Persona.objects.create(
        nombres="Persona",
        apellidos="Real",
        tipo_documento="DNI",
        numero_documento="12345678",
    )
    user = Usuario.objects.create_user(
        username="persona.real",
        password="test-only",
        persona_fk=person,
    )
    inscription = Inscripcion.objects.create(
        edicion=edicion,
        responsable=person,
        paquete=package,
        promocion=promotion,
        referencia="inscripcion-real-no-seed",
    )
    team = Equipo.objects.create(
        inscripcion=inscription,
        disciplina=discipline,
        categoria=category,
        nombre="Equipo real",
    )

    _run_seed(reset_fixture=True, confirm_reset_fixture=True)

    assert Persona.objects.filter(id=person.id).exists()
    assert Usuario.objects.filter(id=user.id).exists()
    assert Inscripcion.objects.filter(id=inscription.id).exists()
    assert Equipo.objects.filter(id=team.id).exists()


def test_reset_aborta_si_un_registro_seed_owned_tiene_dependencias(
    catalogo_torneo_referencia,
):
    _run_seed()
    inscription = Inscripcion.objects.filter(
        referencia__startswith="torneo-referencia-"
    ).first()
    team = inscription.equipos.get()
    Participacion.objects.create(
        inscripcion=inscription,
        persona=inscription.responsable,
        equipo=team,
        edicion=inscription.edicion,
        disciplina=team.disciplina,
    )
    counts = (
        GrupoTorneo.objects.count(),
        EquipoTorneo.objects.count(),
        PartidoTorneo.objects.count(),
    )

    with pytest.raises(CommandError, match="dependencias"):
        _run_seed(reset_fixture=True, confirm_reset_fixture=True)

    assert (
        GrupoTorneo.objects.count(),
        EquipoTorneo.objects.count(),
        PartidoTorneo.objects.count(),
    ) == counts


def test_reset_revierte_todos_los_borrados_si_falla_la_recreacion(
    catalogo_torneo_referencia,
    monkeypatch,
):
    _run_seed()
    before = {
        "groups": set(GrupoTorneo.objects.values_list("id", flat=True)),
        "teams": set(EquipoTorneo.objects.values_list("id", flat=True)),
        "matches": set(PartidoTorneo.objects.values_list("id", flat=True)),
        "inscriptions": set(
            Inscripcion.objects.filter(
                referencia__startswith="torneo-referencia-"
            ).values_list("id", flat=True)
        ),
    }
    command = Command()

    def fail_after_delete(*_args, **_kwargs):
        raise CommandError("fallo controlado después del borrado")

    monkeypatch.setattr(command, "_apply_fixture", fail_after_delete)
    with pytest.raises(CommandError, match="fallo controlado"):
        call_command(
            command,
            reset_fixture=True,
            confirm_reset_fixture=True,
            event_date=EVENT_DATE,
        )

    assert set(GrupoTorneo.objects.values_list("id", flat=True)) == before["groups"]
    assert set(EquipoTorneo.objects.values_list("id", flat=True)) == before["teams"]
    assert set(PartidoTorneo.objects.values_list("id", flat=True)) == before["matches"]
    assert set(
        Inscripcion.objects.filter(
            referencia__startswith="torneo-referencia-"
        ).values_list("id", flat=True)
    ) == before["inscriptions"]


@override_settings(DEBUG=False)
def test_produccion_exige_confirmacion_explicita_para_reset(
    catalogo_torneo_referencia,
    monkeypatch,
):
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.production")
    with pytest.raises(CommandError, match="--confirm-reset-fixture"):
        _run_seed(dry_run=True, reset_fixture=True)

    output = _run_seed(
        dry_run=True,
        reset_fixture=True,
        confirm_reset_fixture=True,
    )
    assert "DRY-RUN" in output
