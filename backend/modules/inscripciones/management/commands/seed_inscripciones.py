"""
Seed command for Inscripciones module.

Seeds reference data: Evento, Promociones, Disciplinas, Categorias, Paquetes.
Idempotent — safe to re-run (uses get_or_create/update_or_create).
"""

from django.core.management.base import BaseCommand

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


class Command(BaseCommand):
    help = "Seed reference data for Salesianos FEST 2026"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Salesianos FEST reference data...")

        self._seed_evento()
        self._seed_promociones()
        self._seed_disciplinas()
        self._seed_categorias()
        self._seed_paquetes()

        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))

    def _seed_evento(self):
        """Seed the main event."""
        evento, created = Evento.objects.update_or_create(
            nombre="Salesianos FEST 2026",
            defaults={
                "fecha_inicio": "2026-10-01",
                "fecha_fin": "2026-10-31",
                "esta_activo": True,
            },
        )
        action = "Created" if created else "Updated"
        self.stdout.write(f"  {action} Evento: {evento.nombre}")

    def _seed_promociones(self):
        """Seed promotions from 1970 to 2026."""
        current_year = 2026
        start_year = 1970
        created_count = 0
        updated_count = 0

        for anio in range(start_year, current_year + 1):
            promo, created = Promocion.objects.update_or_create(
                anio=anio,
                defaults={
                    "colegio": ColegioChoices.MA,
                    "nombre": f"Promoción {anio}",
                    "activa": True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"  Created {created_count}, updated {updated_count} Promociones (range {start_year}-{current_year})"
        )

    def _seed_disciplinas(self):
        """Seed disciplines from the mockup."""
        disciplinas_data = [
            {
                "nombre": "Fulbito Varones",
                "sigla": "fulbito_var",
                "modalidad": ModalidadChoices.MASCULINO,
                "min_jugadores": None,
                "max_jugadores": 12,
            },
            {
                "nombre": "Fulbito Mujeres",
                "sigla": "fulbito_dam",
                "modalidad": ModalidadChoices.FEMENINO,
                "min_jugadores": None,
                "max_jugadores": 12,
            },
            {
                "nombre": "Vóley Mixto",
                "sigla": "voley_mix",
                "modalidad": ModalidadChoices.MIXTO,
                "min_jugadores": None,
                "max_jugadores": 12,
            },
            {
                "nombre": "Básquet Varones",
                "sigla": "basket_var",
                "modalidad": ModalidadChoices.MASCULINO,
                "min_jugadores": None,
                "max_jugadores": 10,
            },
        ]

        for data in disciplinas_data:
            disc, created = Disciplina.objects.update_or_create(
                sigla=data["sigla"],
                defaults={
                    "nombre": data["nombre"],
                    "modalidad": data["modalidad"],
                    "min_jugadores": data["min_jugadores"],
                    "max_jugadores": data["max_jugadores"],
                    "esta_activa": True,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} Disciplina: {disc.nombre}")

    def _seed_categorias(self):
        """Seed categories from the mockup."""
        # Map of disciplina sigla -> list of (nombre, anio_min, anio_max)
        categorias_data = {
            "fulbito_var": [
                ("Junior", 2012, 2025),
                ("Senior", 1998, 2011),
                ("Master", 1987, 1997),
                ("Super Master", 1970, 1986),
            ],
            "fulbito_dam": [
                ("Junior", 2001, 2024),
                ("Master", 1975, 2000),
            ],
            "voley_mix": [
                ("Junior", 2012, 2025),
                ("Senior", 1998, 2011),
                ("Master", 1975, 1986),
            ],
            "basket_var": [
                ("Junior", 2012, 2025),
                ("Senior", 1998, 2011),
                ("Master", 1970, 1997),
            ],
        }

        total_created = 0
        total_updated = 0

        for sigla, categorias in categorias_data.items():
            try:
                disciplina = Disciplina.objects.get(sigla=sigla)
            except Disciplina.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"  Skipping categorias for unknown disciplina: {sigla}")
                )
                continue

            for nombre, anio_min, anio_max in categorias:
                cat, created = Categoria.objects.update_or_create(
                    disciplina=disciplina,
                    nombre=nombre,
                    defaults={
                        "anio_minimo": anio_min,
                        "anio_maximo": anio_max,
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

    def _seed_paquetes(self):
        """
        Seed packages from user reference image.

        Four package cards:
        1. PREVENTA BOX TRIO — ELEGIBLE, 3 disciplines (fulbito_var, fulbito_dam, voley_mix),
           promo S/1300, regular S/1500, up to 20 persons.
        2. PREVENTA BOX DUO — ELEGIBLE, 2 disciplines (fulbito_var, voley_mix),
           promo S/1100, regular S/1300, up to 20 persons.
        3. PREVENTA STAND UP F7M — FIJO, 1 discipline (fulbito_var),
           promo S/500, regular S/600, up to 10 persons.
        4. PREVENTA STAND UP BVF — ELEGIBLE, 1 of 3 disciplines (basket_var, voley_mix, fulbito_dam),
           promo S/500, regular S/600, up to 10 persons.

        Note on discipline mapping:
        - fulbito_var = football/futsal masculine (modalidad=M, max_jugadores=12)
        - fulbito_dam = football/futsal feminine (modalidad=F, max_jugadores=12)
        - voley_mix = volleyball mixed (modalidad=X, max_jugadores=12)
        - basket_var = basketball masculine (modalidad=M, max_jugadores=10)
        """
        paquetes_data = [
            {
                "nombre": "PREVENTA BOX TRIO",
                "descripcion": "3 disciplinas: fulbito masculino, fulbito femenino, vóley mixto. Hasta 20 personas.",
                "cantidad_maxima_participantes": 20,
                "precio_regular": 1500.00,
                "precio_promocional": 1300.00,
                "disciplinas_siglas": ["fulbito_var", "fulbito_dam", "voley_mix"],
                "modo_disciplinas": ModoDisciplinasPaqueteChoices.ELEGIBLE,
                "cantidad_disciplinas_requeridas": 3,
            },
            {
                "nombre": "PREVENTA BOX DUO",
                "descripcion": "2 disciplinas: fulbito masculino, vóley mixto. Hasta 20 personas.",
                "cantidad_maxima_participantes": 20,
                "precio_regular": 1300.00,
                "precio_promocional": 1100.00,
                "disciplinas_siglas": ["fulbito_var", "voley_mix"],
                "modo_disciplinas": ModoDisciplinasPaqueteChoices.ELEGIBLE,
                "cantidad_disciplinas_requeridas": 2,
            },
            {
                "nombre": "PREVENTA STAND UP F7M",
                "descripcion": "Fútbol 7 Masculino. Hasta 10 personas.",
                "cantidad_maxima_participantes": 10,
                "precio_regular": 600.00,
                "precio_promocional": 500.00,
                "disciplinas_siglas": ["fulbito_var"],
                "modo_disciplinas": ModoDisciplinasPaqueteChoices.FIJO,
                "cantidad_disciplinas_requeridas": 1,
            },
            {
                "nombre": "PREVENTA STAND UP BVF",
                "descripcion": "Elegir 1 disciplina: Básquet Varones, Vóley Mixto o Fulbito Femenino. Hasta 10 personas.",
                "cantidad_maxima_participantes": 10,
                "precio_regular": 500.00,
                "precio_promocional": 400.00,
                "disciplinas_siglas": ["basket_var", "voley_mix", "fulbito_dam"],
                "modo_disciplinas": ModoDisciplinasPaqueteChoices.ELEGIBLE,
                "cantidad_disciplinas_requeridas": 1,
            },
        ]

        for data in paquetes_data:
            paquete, created = Paquete.objects.update_or_create(
                nombre=data["nombre"],
                defaults={
                    "descripcion": data["descripcion"],
                    "cantidad_maxima_participantes": data["cantidad_maxima_participantes"],
                    "precio_regular": data["precio_regular"],
                    "precio_promocional": data["precio_promocional"],
                    "valido_desde": "2026-09-01",
                    "valido_hasta": "2026-10-31",
                    "esta_activo": True,
                    "modo_disciplinas": data["modo_disciplinas"],
                    "cantidad_disciplinas_requeridas": data["cantidad_disciplinas_requeridas"],
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} Paquete: {paquete.nombre} (S/{data['precio_promocional']} promo / S/{data['precio_regular']} regular)")

            # Link disciplines to package
            linked_count = 0
            for sigla in data["disciplinas_siglas"]:
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
                        self.style.WARNING(f"    Skipping unknown disciplina: {sigla}")
                    )
            self.stdout.write(f"    Linked {linked_count} disciplines to package")
