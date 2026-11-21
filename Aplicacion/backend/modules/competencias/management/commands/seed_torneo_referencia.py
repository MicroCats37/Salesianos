"""Install or safely replace the normalized Salesianos 2026 reference fixture."""

from __future__ import annotations

import hashlib
import os
import re
from collections import defaultdict
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.competencias.data.fixture import (
    FixtureDataError,
    load_reference_fixture,
)
from modules.competencias.domain.constants import EstadoCompetencia
from modules.competencias.domain.models import (
    Competencia,
    EquipoTorneo,
    GrupoTorneo,
    PartidoTorneo,
)
from modules.eventos.domain.models import Edicion
from modules.salesianos_fest.domain.models import (
    Categoria,
    Disciplina,
    Equipo,
    Inscripcion,
    Paquete,
    Promocion,
)
from modules.usuarios.domain.models import Persona


LOCAL_ZONE = ZoneInfo("America/Lima")
REFERENCE_CATEGORY = "Interpromociones"
REFERENCE_PREFIX = "torneo-referencia-"
LEGACY_FOOTBALL_NAME = "Fulbito Interpromociones"
SYNTHETIC_DOCUMENT_PREFIX = "SEED"
LEGACY_SYNTHETIC_DOCUMENT_PREFIX = {
    "futbol-7-masculino": "99",
    "voley-mixto": "92",
    "basquet-masculino": "93",
}
REFERENCE_COMPETITION_NAMES = {
    "Fútbol 7 Masculino Interpromociones",
    "Vóley Mixto Interpromociones",
    "Básquet Masculino Interpromociones",
    LEGACY_FOOTBALL_NAME,
}


class Command(BaseCommand):
    help = "Carga, compara o reemplaza el fixture multideporte de referencia."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra el diff validado sin ejecutar escrituras.",
        )
        parser.add_argument(
            "--reset-fixture",
            action="store_true",
            help="Reemplaza únicamente los datos identificables del fixture de referencia.",
        )
        parser.add_argument(
            "--event-date",
            type=date.fromisoformat,
            metavar="YYYY-MM-DD",
            help="Fecha para una instalación que todavía no tiene competencias de referencia.",
        )
        parser.add_argument(
            "--confirm-reset-fixture",
            action="store_true",
            help="Confirmación no interactiva obligatoria para reset fuera de development/debug.",
        )

    def handle(self, *args, **options):
        try:
            fixture = load_reference_fixture()
        except FixtureDataError as exc:
            raise CommandError(str(exc)) from exc

        reset = options["reset_fixture"]
        dry_run = options["dry_run"]
        if reset and not self._is_development() and not options["confirm_reset_fixture"]:
            raise CommandError(
                "Fuera de development/debug, --reset-fixture exige "
                "--confirm-reset-fixture."
            )

        edicion = (
            Edicion.objects.filter(estado="PUBLICADA").first()
            or Edicion.objects.first()
        )
        if edicion is None:
            raise CommandError("No existe una edición para cargar el torneo.")

        catalogs = self._resolve_catalogs(edicion, fixture)
        existing = self._reference_competitions(edicion, fixture)
        existing_dates = [competition.fecha for competition in existing.values()]
        event_date = options["event_date"]
        if event_date is None and not existing_dates:
            raise CommandError(
                "El Excel no documenta una fecha. Una instalación nueva exige "
                "--event-date YYYY-MM-DD."
            )
        fallback_date = event_date or existing_dates[0]

        self._report_manifest(fixture)
        self._check_id_collisions(existing, fixture)
        stale = self._stale_fixture_rows(existing, fixture)
        if any(stale.values()) and not reset:
            raise CommandError(
                "Hay filas del seed anterior fuera del fixture normalizado "
                f"({stale}). Ejecuta primero con --dry-run --reset-fixture y, "
                "tras revisar el diagnóstico, con --reset-fixture."
            )

        cleanup = self._collect_seed_owned(edicion) if reset else None
        if cleanup is not None:
            self._assert_safe_cleanup(edicion, cleanup)

        plan = self._build_plan(existing, fixture, cleanup)
        self._report_plan(plan, dry_run=dry_run, reset=reset)
        if dry_run:
            return

        with transaction.atomic():
            existing = self._reference_competitions(edicion, fixture, for_update=True)
            cleanup = self._collect_seed_owned(edicion, for_update=True) if reset else None
            if cleanup is not None:
                self._assert_safe_cleanup(edicion, cleanup)
                self._delete_fixture(existing, cleanup)
            changes = self._apply_fixture(
                edicion,
                fixture,
                catalogs,
                existing,
                fallback_date,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Fixture reconciliado: "
                f"{changes['created']} creados, {changes['updated']} actualizados, "
                f"{changes['unchanged']} sin cambios."
            )
        )

    @staticmethod
    def _is_development() -> bool:
        from django.conf import settings

        settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
        return bool(settings.DEBUG) or settings_module.endswith(".development")

    def _report_manifest(self, fixture):
        manifest = fixture["manifest"]
        self.stdout.write(
            "Fuente: "
            f"{manifest['source']['path']} sha256={manifest['source']['sha256']}"
        )
        for warning in manifest["warnings"]:
            self.stdout.write(
                self.style.WARNING(
                    f"ADVERTENCIA {warning['code']}: {warning['message']} "
                    f"[{', '.join(warning['source_references'])}]"
                )
            )

    def _resolve_catalogs(self, edicion, fixture):
        catalogs = {}
        missing = []
        for competition in fixture["competitions"]:
            discipline = Disciplina.objects.filter(
                edicion=edicion, slug=competition["slug"]
            ).first()
            package = Paquete.objects.filter(
                edicion=edicion, slug=competition["slug"]
            ).first()
            if discipline is None or package is None:
                missing.append(competition["name"])
                continue
            catalogs[competition["code"]] = (discipline, package)
        if missing:
            raise CommandError(
                "Falta el catálogo oficial para "
                f"{', '.join(missing)}. Ejecuta seed_catalogo."
            )

        years = {
            team["promotion_year"]
            for group in fixture["groups"]
            for team in group["teams"]
        }
        missing_years = sorted(
            year
            for year in years
            if not Promocion.objects.filter(anio=year).exists()
        )
        if missing_years:
            raise CommandError(
                f"Faltan promociones en el catálogo oficial: {missing_years}."
            )
        return catalogs

    @staticmethod
    def _reference_competitions(edicion, fixture, for_update=False):
        queryset = Competencia.objects.filter(edicion=edicion)
        if for_update:
            queryset = queryset.select_for_update()
        found = {}
        for item in fixture["competitions"]:
            names = [item["name"]]
            if item["code"] == "F7M":
                names.append(LEGACY_FOOTBALL_NAME)
            matches = list(queryset.filter(nombre__in=names).order_by("created_at"))
            if len(matches) > 1:
                raise CommandError(
                    f"Hay varias competencias candidatas para {item['code']}: "
                    f"{[str(value.id) for value in matches]}."
                )
            if matches:
                found[item["code"]] = matches[0]
        return found

    @staticmethod
    def _desired_ids(fixture):
        return {
            "groups": {item["id"] for item in fixture["groups"]},
            "teams": {
                team["id"]
                for group in fixture["groups"]
                for team in group["teams"]
            },
            "matches": {item["id"] for item in fixture["matches"]},
        }

    def _check_id_collisions(self, existing, fixture):
        desired = self._desired_ids(fixture)
        competition_ids = {item.id for item in existing.values()}
        checks = (
            (GrupoTorneo, desired["groups"]),
            (EquipoTorneo, desired["teams"]),
            (PartidoTorneo, desired["matches"]),
        )
        for model, ids in checks:
            collisions = list(
                model.objects.filter(id__in=ids)
                .exclude(competencia_id__in=competition_ids)
                .values_list("id", flat=True)
            )
            if collisions:
                raise CommandError(
                    f"IDs del fixture ya pertenecen a datos ajenos ({model.__name__}): "
                    f"{collisions}."
                )

    def _stale_fixture_rows(self, existing, fixture):
        desired = self._desired_ids(fixture)
        competition_ids = [item.id for item in existing.values()]
        if not competition_ids:
            return {"partidos": 0, "equipos": 0, "grupos": 0}
        return {
            "partidos": PartidoTorneo.objects.filter(
                competencia_id__in=competition_ids
            ).exclude(id__in=desired["matches"]).count(),
            "equipos": EquipoTorneo.objects.filter(
                competencia_id__in=competition_ids
            ).exclude(id__in=desired["teams"]).count(),
            "grupos": GrupoTorneo.objects.filter(
                competencia_id__in=competition_ids
            ).exclude(id__in=desired["groups"]).count(),
        }

    @staticmethod
    def _collect_seed_owned(edicion, for_update=False):
        queryset = Inscripcion.objects.filter(
            edicion=edicion,
            referencia__startswith=f"{REFERENCE_PREFIX}{edicion.slug}-",
        ).select_related("responsable", "paquete", "promocion")
        if for_update:
            queryset = queryset.select_for_update()
        inscriptions = list(queryset)
        teams = list(
            Equipo.objects.filter(inscripcion__in=inscriptions).select_related(
                "inscripcion", "disciplina", "categoria"
            )
        )
        people = list({item.responsable_id: item.responsable for item in inscriptions}.values())
        return {"inscriptions": inscriptions, "teams": teams, "people": people}

    def _assert_safe_cleanup(self, edicion, cleanup):
        inscriptions = cleanup["inscriptions"]
        teams = cleanup["teams"]
        people = cleanup["people"]
        inscription_ids = {item.id for item in inscriptions}
        team_ids = {item.id for item in teams}
        scoped_tournament_ids = set(
            EquipoTorneo.objects.filter(
                equipo_id__in=team_ids,
                competencia__edicion=edicion,
                competencia__nombre__in=REFERENCE_COMPETITION_NAMES,
            ).values_list("id", flat=True)
        )

        teams_by_inscription = defaultdict(list)
        for team in teams:
            teams_by_inscription[team.inscripcion_id].append(team)

        diagnostics = []
        expected_prefix = f"{REFERENCE_PREFIX}{edicion.slug}-"
        for inscription in inscriptions:
            suffix = inscription.referencia.removeprefix(expected_prefix)
            try:
                slug, label = next(
                    (slug, suffix.removeprefix(f"{slug}-"))
                    for slug in (
                        "futbol-7-masculino",
                        "voley-mixto",
                        "basquet-masculino",
                    )
                    if suffix.startswith(f"{slug}-")
                )
            except StopIteration:
                diagnostics.append(
                    f"referencia no reconocida {inscription.referencia}"
                )
                continue
            expected_code = {
                "futbol-7-masculino": "F7M",
                "voley-mixto": "VOL",
                "basquet-masculino": "BAS",
            }[slug]
            person = inscription.responsable
            expected_document = self._synthetic_document(
                edicion.slug, slug, label
            )
            owned_teams = teams_by_inscription[inscription.id]
            if (
                not self._is_seed_person(
                    person,
                    label=label,
                    competition_code=expected_code,
                    discipline_slug=slug,
                    expected_document=expected_document,
                )
                or inscription.paquete.slug != slug
                or inscription.cupos_pagados
                or inscription.cupos_asignados
                or len(owned_teams) != 1
            ):
                diagnostics.append(
                    f"inscripción {inscription.referencia} ya no conserva la identidad sintética"
                )
                continue
            team = owned_teams[0]
            if (
                team.disciplina.slug != slug
                or team.nombre != f"Promoción {label}"
                or team.categoria.nombre != REFERENCE_CATEGORY
            ):
                diagnostics.append(
                    f"equipo {team.id} ya no conserva la identidad sintética"
                )

        allowed = {
            Inscripcion: {Equipo: team_ids},
            Equipo: {EquipoTorneo: scoped_tournament_ids},
            Persona: {Inscripcion: inscription_ids},
        }
        for instance in [*inscriptions, *teams, *people]:
            diagnostics.extend(self._unexpected_dependencies(instance, allowed))

        if diagnostics:
            raise CommandError(
                "Reset abortado: hay datos seed-owned con dependencias o identidad "
                "no segura:\n- " + "\n- ".join(sorted(set(diagnostics)))
            )

    @staticmethod
    def _unexpected_dependencies(instance, allowed):
        diagnostics = []
        allowed_models = allowed.get(type(instance), {})
        for relation in instance._meta.related_objects:
            accessor = relation.get_accessor_name()
            if not accessor:
                continue
            try:
                related = getattr(instance, accessor)
                if relation.one_to_one:
                    objects = [related]
                else:
                    objects = list(related.all())
            except ObjectDoesNotExist:
                objects = []
            if not objects:
                continue
            allowed_ids = allowed_models.get(relation.related_model)
            unexpected = (
                objects
                if allowed_ids is None
                else [item for item in objects if item.pk not in allowed_ids]
            )
            if unexpected:
                diagnostics.append(
                    f"{type(instance).__name__} {instance.pk}: "
                    f"{relation.related_model._meta.label} x{len(unexpected)}"
                )
        return diagnostics

    @staticmethod
    def _is_seed_person(
        person,
        *,
        label,
        competition_code,
        discipline_slug,
        expected_document,
    ):
        if (
            person.nombres != "Delegación"
            or person.apellidos != f"{label} {competition_code}"
        ):
            return False

        if (
            person.tipo_documento == "PAS"
            and person.numero_documento == expected_document
        ):
            return True

        legacy_prefix = LEGACY_SYNTHETIC_DOCUMENT_PREFIX[discipline_slug]
        return person.tipo_documento == "DNI" and bool(
            re.fullmatch(rf"{legacy_prefix}\d{{6}}", person.numero_documento)
        )

    def _build_plan(self, existing, fixture, cleanup):
        desired = self._desired_ids(fixture)
        competition_ids = [item.id for item in existing.values()]
        current = {
            "competitions": len(existing),
            "groups": GrupoTorneo.objects.filter(id__in=desired["groups"]).count(),
            "teams": EquipoTorneo.objects.filter(id__in=desired["teams"]).count(),
            "matches": PartidoTorneo.objects.filter(id__in=desired["matches"]).count(),
        }
        deleted = {
            "matches": PartidoTorneo.objects.filter(
                competencia_id__in=competition_ids
            ).count(),
            "teams": EquipoTorneo.objects.filter(
                competencia_id__in=competition_ids
            ).count(),
            "groups": GrupoTorneo.objects.filter(
                competencia_id__in=competition_ids
            ).count(),
            "synthetic_inscriptions": len(cleanup["inscriptions"]) if cleanup else 0,
            "synthetic_teams": len(cleanup["teams"]) if cleanup else 0,
            "synthetic_people": len(cleanup["people"]) if cleanup else 0,
        }
        return {
            "create": {
                "competitions": 3 - current["competitions"],
                "groups": len(desired["groups"]) - (0 if cleanup else current["groups"]),
                "teams": len(desired["teams"]) - (0 if cleanup else current["teams"]),
                "matches": len(desired["matches"]) - (0 if cleanup else current["matches"]),
            },
            "delete": deleted,
        }

    def _report_plan(self, plan, *, dry_run, reset):
        mode = "DRY-RUN" if dry_run else "APPLY"
        self.stdout.write(f"{mode}: reset_fixture={reset}")
        self.stdout.write(f"  crear/reconciliar: {plan['create']}")
        if reset:
            self.stdout.write(f"  eliminar: {plan['delete']}")

    @staticmethod
    def _delete_fixture(existing, cleanup):
        competition_ids = [item.id for item in existing.values()]
        PartidoTorneo.objects.filter(competencia_id__in=competition_ids).delete()
        EquipoTorneo.objects.filter(competencia_id__in=competition_ids).delete()
        GrupoTorneo.objects.filter(competencia_id__in=competition_ids).delete()
        Equipo.objects.filter(id__in=[item.id for item in cleanup["teams"]]).delete()
        Inscripcion.objects.filter(
            id__in=[item.id for item in cleanup["inscriptions"]]
        ).delete()
        Persona.objects.filter(id__in=[item.id for item in cleanup["people"]]).delete()

    def _apply_fixture(
        self,
        edicion,
        fixture,
        catalogs,
        existing,
        fallback_date,
    ):
        changes = {"created": 0, "updated": 0, "unchanged": 0}
        category = Categoria.objects.filter(
            edicion=edicion, nombre=REFERENCE_CATEGORY
        ).first()
        if category is None:
            category = Categoria.objects.create(
                edicion=edicion,
                nombre=REFERENCE_CATEGORY,
                promocion_desde=1975,
                promocion_hasta=2025,
            )
            changes["created"] += 1
        else:
            self._update(
                category,
                {"promocion_desde": 1975, "promocion_hasta": 2025},
                changes,
            )

        competitions = {}
        for item in fixture["competitions"]:
            discipline, _package = catalogs[item["code"]]
            competition = existing.get(item["code"])
            if competition is None:
                competition = Competencia.objects.create(
                    edicion=edicion,
                    disciplina=discipline,
                    categoria=category,
                    nombre=item["name"],
                    fecha=fallback_date,
                    estado=EstadoCompetencia.EN_CURSO,
                )
                changes["created"] += 1
            else:
                self._update(
                    competition,
                    {
                        "disciplina_id": discipline.id,
                        "categoria_id": category.id,
                        "nombre": item["name"],
                        "estado": EstadoCompetencia.EN_CURSO,
                    },
                    changes,
                )
            competitions[item["code"]] = competition

        groups = {}
        tournament_teams = {}
        for item in fixture["groups"]:
            competition = competitions[item["competition_code"]]
            group = GrupoTorneo.objects.filter(id=item["id"]).first()
            if group is None:
                group = GrupoTorneo.objects.create(
                    id=item["id"],
                    competencia=competition,
                    etiqueta=item["label"],
                )
                changes["created"] += 1
            else:
                self._update(
                    group,
                    {
                        "competencia_id": competition.id,
                        "etiqueta": item["label"],
                    },
                    changes,
                )
            groups[item["id"]] = group

            discipline, package = catalogs[item["competition_code"]]
            for team_data in item["teams"]:
                team = self._ensure_synthetic_team(
                    edicion,
                    category,
                    discipline,
                    package,
                    item["competition_code"],
                    team_data,
                    changes,
                )
                tournament_team = EquipoTorneo.objects.filter(id=team_data["id"]).first()
                if tournament_team is None:
                    tournament_team = EquipoTorneo.objects.create(
                        id=team_data["id"],
                        equipo=team,
                        competencia=competition,
                        grupo=group,
                    )
                    changes["created"] += 1
                else:
                    self._update(
                        tournament_team,
                        {
                            "equipo_id": team.id,
                            "competencia_id": competition.id,
                            "grupo_id": group.id,
                        },
                        changes,
                    )
                tournament_teams[team_data["id"]] = tournament_team

        for item in fixture["matches"]:
            competition = competitions[item["competition_code"]]
            scheduled = datetime.combine(
                competition.fecha,
                time.fromisoformat(item["start"]),
                tzinfo=LOCAL_ZONE,
            )
            fields = {
                "competencia_id": competition.id,
                "grupo_id": item["group_id"],
                "etapa": item["stage"],
                "categoria_fixture": item["category"],
                "posicion": item["position"],
                "local_id": item["home_id"],
                "visitante_id": item["away_id"],
                "etiqueta_local": item["home_label"] or "",
                "etiqueta_visitante": item["away_label"] or "",
                "titulo_fixture": item["title"],
                "programado_en": scheduled,
                "cancha": item["court"],
                "duracion_minutos": item["duration_minutes"],
            }
            match = PartidoTorneo.objects.filter(id=item["id"]).first()
            if match is None:
                PartidoTorneo.objects.create(id=item["id"], **fields)
                changes["created"] += 1
            else:
                self._update(match, fields, changes)
        return changes

    def _ensure_synthetic_team(
        self,
        edicion,
        category,
        discipline,
        package,
        competition_code,
        team_data,
        changes,
    ):
        label = team_data["label"]
        reference = (
            f"{REFERENCE_PREFIX}{edicion.slug}-{discipline.slug}-{label}"
        )
        document = self._synthetic_document(
            edicion.slug, discipline.slug, label
        )
        inscription = Inscripcion.objects.filter(referencia=reference).first()
        if inscription is None:
            person = Persona.objects.filter(
                tipo_documento="PAS", numero_documento=document
            ).first()
            expected_person = {
                "nombres": "Delegación",
                "apellidos": f"{label} {competition_code}",
            }
            if person is None:
                person = Persona.objects.create(
                    tipo_documento="PAS",
                    numero_documento=document,
                    **expected_person,
                )
                changes["created"] += 1
            elif any(
                getattr(person, field) != value
                for field, value in expected_person.items()
            ):
                raise CommandError(
                    f"La identidad sintética estable {document} pertenece a una persona real."
                )
            else:
                changes["unchanged"] += 1
            promotion = Promocion.objects.get(anio=team_data["promotion_year"])
            inscription = Inscripcion.objects.create(
                edicion=edicion,
                responsable=person,
                paquete=package,
                promocion=promotion,
                referencia=reference,
                cupos_solicitados=package.minimo_compra_inicial,
            )
            changes["created"] += 1
        else:
            expected = (
                inscription.edicion_id == edicion.id
                and inscription.paquete_id == package.id
                and inscription.promocion.anio == team_data["promotion_year"]
                and inscription.responsable.nombres == "Delegación"
                and inscription.responsable.apellidos
                == f"{label} {competition_code}"
                and inscription.responsable.tipo_documento == "PAS"
                and inscription.responsable.numero_documento == document
            )
            if not expected:
                raise CommandError(
                    f"La referencia {reference} ya existe y no es un registro sintético seguro."
                )
            changes["unchanged"] += 1

        team = Equipo.objects.filter(
            inscripcion=inscription, disciplina=discipline
        ).first()
        fields = {
            "categoria_id": category.id,
            "nombre": f"Promoción {label}",
            "estado": "ACTIVO",
        }
        if team is None:
            team = Equipo.objects.create(
                inscripcion=inscription,
                disciplina=discipline,
                **fields,
            )
            changes["created"] += 1
        else:
            self._update(team, fields, changes)
        return team

    @staticmethod
    def _synthetic_document(edicion_slug, discipline_slug, label):
        identity = f"{edicion_slug}|{discipline_slug}|{label}".encode("utf-8")
        return f"{SYNTHETIC_DOCUMENT_PREFIX}{hashlib.sha256(identity).hexdigest()[:16].upper()}"

    @staticmethod
    def _update(instance, fields, changes):
        changed = []
        for field, value in fields.items():
            if getattr(instance, field) != value:
                setattr(instance, field, value)
                changed.append(field.removesuffix("_id"))
        if changed:
            instance.save(update_fields=[*changed, "updated_at"] if hasattr(instance, "updated_at") else changed)
            changes["updated"] += 1
        else:
            changes["unchanged"] += 1
