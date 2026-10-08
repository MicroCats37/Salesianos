"""
Seed command for Inscripciones module.

Loads reference data from `seed_data/seed_inscripciones.json`.
Idempotent — safe to re-run (uses update_or_create/get_or_create).

Usage:
    python manage.py seed_inscripciones
    python manage.py seed_inscripciones --path /custom/path/to/seed.json
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from modules.inscripciones.domain.models import (
    Evento,
    Promocion,
    Disciplina,
    Categoria,
    Paquete,
    PaqueteDisciplina,
)
from modules.inscripciones.domain.constants import (
    ColegioChoices,
    ModalidadChoices,
    ModoDisciplinasPaqueteChoices,
)


DEFAULT_SEED_PATH = (
    Path(__file__).resolve().parents[2]
    / "seed_data"
    / "seed_inscripciones.json"
)


class Command(BaseCommand):
    help = "Seed reference data for Salesianos FEST from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default=str(DEFAULT_SEED_PATH),
            help=f"Path to the seed JSON file (default: {DEFAULT_SEED_PATH})",
        )

    def handle(self, *args, **options):
        seed_path = Path(options["path"])
        if not seed_path.exists():
            raise CommandError(f"Seed file not found: {seed_path}")

        self.stdout.write(f"Loading seed data from: {seed_path}")
        with seed_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        self.stdout.write("Seeding Salesianos FEST reference data...")
        self._seed_evento(data["evento"])
        self._seed_promociones(data["promociones"])
        self._seed_disciplinas(data["disciplinas"])
        self._seed_categorias(data["categorias"])
        self._seed_paquetes(data["paquetes"])

        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))

    def _seed_evento(self, evento_data):
        evento, created = Evento.objects.update_or_create(
            nombre=evento_data["nombre"],
            defaults={
                "fecha_inicio": evento_data["fecha_inicio"],
                "fecha_fin": evento_data["fecha_fin"],
                "esta_activo": evento_data.get("esta_activo", True),
            },
        )
        action = "Created" if created else "Updated"
        self.stdout.write(f"  {action} Evento: {evento.nombre}")

    def _seed_promociones(self, promos_data):
        anio_inicio = int(promos_data["anio_inicio"])
        anio_fin = int(promos_data["anio_fin"])
        colegio = ColegioChoices(promos_data["colegio"])
        activa = promos_data.get("activa", True)
        created_count = 0
        updated_count = 0

        for anio in range(anio_inicio, anio_fin + 1):
            promo, created = Promocion.objects.update_or_create(
                anio=anio,
                defaults={
                    "colegio": colegio,
                    "nombre": f"Promoción {anio}",
                    "activa": activa,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"  Created {created_count}, updated {updated_count} Promociones "
            f"(range {anio_inicio}-{anio_fin})"
        )

    def _seed_disciplinas(self, disciplinas_data):
        for data in disciplinas_data:
            modalidad = ModalidadChoices(data["modalidad"])
            disc, created = Disciplina.objects.update_or_create(
                sigla=data["sigla"],
                defaults={
                    "nombre": data["nombre"],
                    "modalidad": modalidad,
                    "min_jugadores": data.get("min_jugadores"),
                    "max_jugadores": data.get("max_jugadores"),
                    "esta_activa": True,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} Disciplina: {disc.nombre}")

    def _seed_categorias(self, categorias_data):
        total_created = 0
        total_updated = 0

        for sigla, categorias in categorias_data.items():
            try:
                disciplina = Disciplina.objects.get(sigla=sigla)
            except Disciplina.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Skipping categorias for unknown disciplina: {sigla}"
                    )
                )
                continue

            for cat_data in categorias:
                cat, created = Categoria.objects.update_or_create(
                    disciplina=disciplina,
                    nombre=cat_data["nombre"],
                    defaults={
                        "anio_minimo": int(cat_data["anio_minimo"]),
                        "anio_maximo": int(cat_data["anio_maximo"]),
                        "esta_activa": True,
                    },
                )
                if created:
                    total_created += 1
                else:
                    total_updated += 1

        self.stdout.write(
            f"  Created {total_created}, updated {total_updated} Categorias"
        )

    def _seed_paquetes(self, paquetes_data):
        for data in paquetes_data:
            modo = ModoDisciplinasPaqueteChoices(data["modo_disciplinas"])
            paquete, created = Paquete.objects.update_or_create(
                nombre=data["nombre"],
                defaults={
                    "descripcion": data.get("descripcion", ""),
                    "cantidad_maxima_participantes": int(
                        data["cantidad_maxima_participantes"]
                    ),
                    "precio_regular": data["precio_regular"],
                    "precio_promocional": data.get("precio_promocional"),
                    "valido_desde": data["valido_desde"],
                    "valido_hasta": data["valido_hasta"],
                    "esta_activo": data.get("esta_activo", True),
                    "modo_disciplinas": modo,
                    "cantidad_disciplinas_requeridas": data.get(
                        "cantidad_disciplinas_requeridas"
                    ),
                },
            )
            action = "Created" if created else "Updated"
            promo = data.get("precio_promocional")
            self.stdout.write(
                f"  {action} Paquete: {paquete.nombre} "
                f"(S/{promo if promo is not None else '-'} promo / "
                f"S/{data['precio_regular']} regular)"
            )

            linked_count = 0
            for sigla in data.get("disciplinas_siglas", []):
                try:
                    disciplina = Disciplina.objects.get(sigla=sigla)
                    _, created_link = PaqueteDisciplina.objects.get_or_create(
                        paquete=paquete,
                        disciplina=disciplina,
                    )
                    if created_link:
                        linked_count += 1
                except Disciplina.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"    Skipping unknown disciplina: {sigla}"
                        )
                    )
            self.stdout.write(f"    Linked {linked_count} disciplines to package")
