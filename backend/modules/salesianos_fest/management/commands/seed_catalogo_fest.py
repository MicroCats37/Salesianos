"""
Seed command for salesianos_fest catalog data (Fase 2).

Creates the base evento, promociones, disciplinas, y ofertas comerciales.

Idempotente: usa get_or_create para no duplicar datos.

Usage:
    python manage.py seed_catalogo_fest
    python manage.py seed_catalogo_fest --clear  # Borra y recrea
"""
from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Promocion,
    Categoria,
    Paquete,
    PaqueteDisciplina,
    PaquetePrecio,
    PaqueteBeneficio,
    Pase,
    PasePrecio,
)
from modules.salesianos_fest.domain.constants import (
    ModalidadChoices,
    TipoPaqueteChoices,
    ModoDisciplinasChoices,
    EtapaChoices,
    TipoBeneficioChoices,
    AlcanceBeneficioChoices,
    ModoCalculoBeneficioChoices,
    CANTIDAD_MAXIMA_SIN_LIMITE,
)

# ── Supuestos del seed del catálogo de pases ────────────────────────────────
#
# Defaults de PRIMERA creación, aislados aquí a propósito. El operador puede
# ajustarlos (precio, inventario, activación) desde el admin del módulo y el
# seed NO vuelve a escribirlos: reejecutar el seed no debe deshacer la
# configuración de la organización. Por eso el bloque del pase usa
# `get_or_create` y no `update_or_create`.
#
# Los montos son un supuesto de producto pendiente de confirmación.
PASE_FIESTA_NOMBRE = "Pase de Fiesta"
PASE_FIESTA_DESCRIPCION = "Acceso nominativo a la fiesta de cierre."
PASE_FIESTA_PREVENTA = Decimal("25.00")
PASE_FIESTA_REGULAR = Decimal("35.00")


class Command(BaseCommand):
    help = "Seed initial catalog data for Salesianos FEST Fase 2."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing catalog data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        clear = options.get("clear", False)

        if clear:
            self.stdout.write("  Clearing existing catalog data...")
            PaqueteBeneficio.objects.all().delete()
            PaquetePrecio.objects.all().delete()
            PaqueteDisciplina.objects.all().delete()
            Paquete.objects.all().delete()
            # Los pases protegen al Evento (PROTECT): se borran antes.
            PasePrecio.objects.all().delete()
            Pase.objects.all().delete()
            Disciplina.objects.all().delete()
            Promocion.objects.all().delete()
            Categoria.objects.all().delete()
            Evento.objects.all().delete()
            self.stdout.write(self.style.WARNING("  Catalog data cleared."))

        self.stdout.write("  Seeding Evento...")
        evento, _ = Evento.objects.get_or_create(
            nombre="Salesianos FEST 2026",
            defaults={
                "fecha_inicio": date(2026, 11, 15),
                "fecha_fin": date(2026, 11, 20),
                "esta_activo": True,
            },
        )
        self.stdout.write(f"    Evento: {evento.nombre} ({evento.fecha_inicio} - {evento.fecha_fin})")

        self.stdout.write("  Seeding Promociones (1970-2025)...")
        # Official category boundaries
        CATEGORY_RANGES = [
            ("Junior", 2012, 2025),
            ("Senior", 1998, 2011),
            ("Master", 1985, 1997),
            ("Super Master", 1970, 1984),
        ]

        def get_category_name(anio: int) -> str:
            """Deterministic category name based on birth year."""
            for nombre, desde, hasta in CATEGORY_RANGES:
                if desde <= anio <= hasta:
                    return nombre
            return "Unknown"

        # Create one Promocion per year 1970-2025
        for anio in range(1970, 2026):
            nombre = get_category_name(anio)
            promo, created = Promocion.objects.update_or_create(
                anio=anio,
                defaults={"nombre": nombre, "activa": True},
            )
            self.stdout.write(f"    {'Created' if created else 'Updated'}: {promo.nombre} ({promo.anio})")

        self.stdout.write("  Reconciling Categorías for FEST 2026...")
        # This seed is destructive for the superseded FEST 2026 categories.
        obsolete_nombres = ["Sub-14", "Sub-16", "Sub-18", "Sub-20"]
        deleted_count, _ = Categoria.objects.filter(
            evento=evento,
            nombre__in=obsolete_nombres,
        ).delete()
        self.stdout.write(f"    Deleted {deleted_count} obsolete categories")

        # Reconcile to official 4 categories
        official_categorias = [
            ("Junior", 2012, 2025),
            ("Senior", 1998, 2011),
            ("Master", 1985, 1997),
            ("Super Master", 1970, 1984),
        ]
        for nombre, desde, hasta in official_categorias:
            cat, created = Categoria.objects.update_or_create(
                evento=evento,
                nombre=nombre,
                defaults={
                    "promocion_desde": desde,
                    "promocion_hasta": hasta,
                    "esta_activa": True,
                },
            )
            self.stdout.write(f"    {'Created' if created else 'Updated'}: {cat.nombre} ({cat.promocion_desde}-{cat.promocion_hasta})")

        self.stdout.write("  Seeding Disciplinas...")
        disciplinas_data = [
            ("Fútbol 7 Masculino", "F7M", ModalidadChoices.MASCULINO, 7, 10),
            ("Fútbol 7 Femenino", "F7F", ModalidadChoices.FEMENINO, 7, 10),
            ("Vóley Mixto", "VOL", ModalidadChoices.MIXTO, 6, 8),
            ("Básquet Masculino", "BAS", ModalidadChoices.MASCULINO, 5, 10),
        ]
        disciplina_map = {}
        for nombre, sigla, modalidad, min_j, max_j in disciplinas_data:
            disc, created = Disciplina.objects.get_or_create(
                sigla=sigla,
                defaults={
                    "nombre": nombre,
                    "modalidad": modalidad,
                    "min_jugadores": min_j,
                    "max_jugadores": max_j,
                    "esta_activa": True,
                },
            )
            disciplina_map[sigla] = disc
            self.stdout.write(f"    {'Created' if created else 'Exists'}: {disc.nombre} ({sigla})")

        self.stdout.write("  Seeding Paquetes y Precios...")
        hoy = date.today()
        fecha_limite_preventa = date(2026, 10, 31)

        # Helper para crear paquete con precios
        def crear_paquete(
            nombre: str,
            tipo: str,
            modo: str,
            cant_disc: int,
            minimo: int,
            preventa_price: Decimal,
            regular_price: Decimal,
            descripcion: str = "",
        ) -> Paquete:
            paquete, created = Paquete.objects.update_or_create(
                evento=evento,
                nombre=nombre,
                defaults={
                    "descripcion": descripcion,
                    "tipo": tipo,
                    "modo_disciplinas": modo,
                    "cantidad_disciplinas": cant_disc,
                    "minimo_compra_inicial": minimo,
                    "activo": True,
                },
            )
            # Each run reconciles catalog prices with the official price per person.
            PaquetePrecio.objects.update_or_create(
                paquete=paquete,
                etapa=EtapaChoices.PREVENTA,
                defaults={
                    "precio_unitario": preventa_price,
                    "vigente_desde": hoy,
                    "vigente_hasta": fecha_limite_preventa,
                    "activo": True,
                },
            )
            PaquetePrecio.objects.update_or_create(
                paquete=paquete,
                etapa=EtapaChoices.REGULAR,
                defaults={
                    "precio_unitario": regular_price,
                    "vigente_desde": fecha_limite_preventa,
                    "vigente_hasta": None,
                    "activo": True,
                },
            )
            return paquete, created

        # Helper para crear beneficio
        def crear_beneficio(paquete: Paquete, tipo: str, cantidad: int, alcance: str, modo_calc: str):
            _, created = PaqueteBeneficio.objects.update_or_create(
                paquete=paquete,
                tipo=tipo,
                defaults={
                    "cantidad": cantidad,
                    "alcance": alcance,
                    "modo_calculo": modo_calc,
                },
            )
            return created

        def reconciliar_disciplinas(paquete: Paquete, siglas: list[str]) -> None:
            """Keep each offer linked only to its official eligible disciplines."""
            disciplinas = [disciplina_map[sigla] for sigla in siglas]
            disciplina_ids = [disciplina.id for disciplina in disciplinas]
            PaqueteDisciplina.objects.filter(paquete=paquete).exclude(
                disciplina_id__in=disciplina_ids,
            ).delete()
            for disciplina in disciplinas:
                PaqueteDisciplina.objects.get_or_create(
                    paquete=paquete,
                    disciplina=disciplina,
                )

        # Reencuentro + Fiesta
        pkg, created = crear_paquete(
            nombre="Reencuentro + Fiesta",
            tipo=TipoPaqueteChoices.PACK,
            modo=ModoDisciplinasChoices.ELEGIBLE,
            cant_disc=1,
            minimo=10,
            preventa_price=Decimal("40.00"),
            regular_price=Decimal("50.00"),
            descripcion="Reencuentro con acceso a fiesta de cierre.",
        )
        self.stdout.write(f"    {'Created' if created else 'Exists'}: {pkg.nombre}")
        crear_beneficio(pkg, TipoBeneficioChoices.FIESTA, 1, AlcanceBeneficioChoices.INDIVIDUAL, ModoCalculoBeneficioChoices.FIJO_INICIAL)
        reconciliar_disciplinas(pkg, ["F7F", "VOL", "BAS"])

        # Pichanga + Fiesta
        pkg, created = crear_paquete(
            nombre="Pichanga + Fiesta",
            tipo=TipoPaqueteChoices.PACK,
            modo=ModoDisciplinasChoices.FIJO,
            cant_disc=1,
            minimo=10,
            preventa_price=Decimal("45.00"),
            regular_price=Decimal("55.00"),
            descripcion="Pichanga competitiva con acceso a fiesta de cierre.",
        )
        self.stdout.write(f"    {'Created' if created else 'Exists'}: {pkg.nombre}")
        crear_beneficio(pkg, TipoBeneficioChoices.FIESTA, 1, AlcanceBeneficioChoices.INDIVIDUAL, ModoCalculoBeneficioChoices.FIJO_INICIAL)
        reconciliar_disciplinas(pkg, ["F7M"])

        # Dúo + Fiesta Box (sin disciplinas — elegible)
        pkg, created = crear_paquete(
            nombre="Dúo + Fiesta Box",
            tipo=TipoPaqueteChoices.PACK,
            modo=ModoDisciplinasChoices.ELEGIBLE,
            cant_disc=2,
            minimo=15,
            preventa_price=Decimal("60.00"),
            regular_price=Decimal("70.00"),
            descripcion="Pack para dos personas con fiesta y box de bebidas.",
        )
        self.stdout.write(f"    {'Created' if created else 'Exists'}: {pkg.nombre}")
        # FIESTA: INDIVIDUAL + POR_CUPO — each paid spot grants individual fiesta pass
        crear_beneficio(pkg, TipoBeneficioChoices.FIESTA, 1, AlcanceBeneficioChoices.INDIVIDUAL, ModoCalculoBeneficioChoices.POR_CUPO)
        # BOX/CERVEZA: GRUPAL + FIJO_INICIAL — one promotional benefit per inscription
        crear_beneficio(pkg, TipoBeneficioChoices.BOX, 1, AlcanceBeneficioChoices.GRUPAL, ModoCalculoBeneficioChoices.FIJO_INICIAL)
        crear_beneficio(pkg, TipoBeneficioChoices.CERVEZA, 6, AlcanceBeneficioChoices.GRUPAL, ModoCalculoBeneficioChoices.FIJO_INICIAL)
        reconciliar_disciplinas(pkg, ["VOL", "BAS"])

        # Trío + Fiesta Box (sin disciplinas — elegible)
        pkg, created = crear_paquete(
            nombre="Trío + Fiesta Box",
            tipo=TipoPaqueteChoices.PACK,
            modo=ModoDisciplinasChoices.ELEGIBLE,
            cant_disc=3,
            minimo=20,
            preventa_price=Decimal("60.00"),
            regular_price=Decimal("70.00"),
            descripcion="Pack para tres personas con fiesta y box de bebidas.",
        )
        self.stdout.write(f"    {'Created' if created else 'Exists'}: {pkg.nombre}")
        # FIESTA: INDIVIDUAL + POR_CUPO — each paid spot grants individual fiesta pass
        crear_beneficio(pkg, TipoBeneficioChoices.FIESTA, 1, AlcanceBeneficioChoices.INDIVIDUAL, ModoCalculoBeneficioChoices.POR_CUPO)
        # BOX/CERVEZA: GRUPAL + FIJO_INICIAL — one promotional benefit per inscription
        crear_beneficio(pkg, TipoBeneficioChoices.BOX, 1, AlcanceBeneficioChoices.GRUPAL, ModoCalculoBeneficioChoices.FIJO_INICIAL)
        crear_beneficio(pkg, TipoBeneficioChoices.CERVEZA, 6, AlcanceBeneficioChoices.GRUPAL, ModoCalculoBeneficioChoices.FIJO_INICIAL)
        reconciliar_disciplinas(pkg, ["F7M", "VOL", "BAS"])

        # Disciplinas individuales con precio
        # Fútbol 7 masculino
        f7m = disciplina_map["F7M"]
        pkg, created = crear_paquete(
            nombre="Fútbol 7 Masculino",
            tipo=TipoPaqueteChoices.DISCIPLINA,
            modo=ModoDisciplinasChoices.FIJO,
            cant_disc=1,
            minimo=7,
            preventa_price=Decimal("40.00"),
            regular_price=Decimal("50.00"),
            descripcion="Torneo de fútbol 7 masculino.",
        )
        self.stdout.write(f"    {'Created' if created else 'Exists'}: {pkg.nombre}")
        reconciliar_disciplinas(pkg, ["F7M"])

        # Fútbol 7 femenino
        f7f = disciplina_map["F7F"]
        pkg, created = crear_paquete(
            nombre="Fútbol 7 Femenino",
            tipo=TipoPaqueteChoices.DISCIPLINA,
            modo=ModoDisciplinasChoices.FIJO,
            cant_disc=1,
            minimo=7,
            preventa_price=Decimal("40.00"),
            regular_price=Decimal("50.00"),
            descripcion="Torneo de fútbol 7 femenino.",
        )
        self.stdout.write(f"    {'Created' if created else 'Exists'}: {pkg.nombre}")
        reconciliar_disciplinas(pkg, ["F7F"])

        # Vóley mixto
        vol = disciplina_map["VOL"]
        pkg, created = crear_paquete(
            nombre="Vóley Mixto",
            tipo=TipoPaqueteChoices.DISCIPLINA,
            modo=ModoDisciplinasChoices.FIJO,
            cant_disc=1,
            minimo=6,
            preventa_price=Decimal("40.00"),
            regular_price=Decimal("50.00"),
            descripcion="Torneo de vóley mixto.",
        )
        self.stdout.write(f"    {'Created' if created else 'Exists'}: {pkg.nombre}")
        reconciliar_disciplinas(pkg, ["VOL"])

        # Básquet masculino
        bas = disciplina_map["BAS"]
        pkg, created = crear_paquete(
            nombre="Básquet Masculino",
            tipo=TipoPaqueteChoices.DISCIPLINA,
            modo=ModoDisciplinasChoices.FIJO,
            cant_disc=1,
            minimo=5,
            preventa_price=Decimal("40.00"),
            regular_price=Decimal("50.00"),
            descripcion="Torneo de básquet masculino.",
        )
        self.stdout.write(f"    {'Created' if created else 'Exists'}: {pkg.nombre}")
        reconciliar_disciplinas(pkg, ["BAS"])

        self.stdout.write("  Seeding Pases de fiesta (catálogo independiente)...")
        # El pase es un catálogo PARALELO al de paquetes: no se modela como
        # `Paquete.tipo=PASE`.
        #
        # El seed SÓLO crea lo que falta. Un pase que el operador ya activó (o
        # cuyos precios ajustó) NO se vuelve a inactivar ni a sobreescribir:
        # el rollout es explícito (PASES_FIESTA_ENABLED=True + activación
        # manual) y el rollback es volver a desactivar, nunca borrar datos.
        pase, created = Pase.objects.get_or_create(
            evento=evento,
            nombre=PASE_FIESTA_NOMBRE,
            defaults={
                "descripcion": PASE_FIESTA_DESCRIPCION,
                "cantidad_maxima": CANTIDAD_MAXIMA_SIN_LIMITE,
                "activo": False,
            },
        )
        self.stdout.write(
            f"    {'Created' if created else 'Exists'}: {pase.nombre} "
            f"({'activo' if pase.activo else 'inactivo'})"
        )

        if created:
            # Mismo calendario de etapas que los paquetes: preventa hasta el
            # cierre de preventa y regular desde ese mismo día.
            PasePrecio.objects.get_or_create(
                pase=pase,
                etapa=EtapaChoices.PREVENTA,
                defaults={
                    "precio_unitario": PASE_FIESTA_PREVENTA,
                    "vigente_desde": hoy,
                    "vigente_hasta": fecha_limite_preventa,
                    "activo": False,
                },
            )
            PasePrecio.objects.get_or_create(
                pase=pase,
                etapa=EtapaChoices.REGULAR,
                defaults={
                    "precio_unitario": PASE_FIESTA_REGULAR,
                    "vigente_desde": fecha_limite_preventa,
                    "vigente_hasta": None,
                    "activo": False,
                },
            )
            self.stdout.write("    Precios PREVENTA/REGULAR creados (inactivos)")
        else:
            self.stdout.write("    Precios existentes preservados")

        self.stdout.write(self.style.SUCCESS("\n  Seed completed successfully!"))
        self.stdout.write(f"  Evento: {evento.nombre}")
        self.stdout.write(f"  Disciplinas: {Disciplina.objects.count()}")
        self.stdout.write(f"  Promociones: {Promocion.objects.count()}")
        self.stdout.write(f"  Categorías: {Categoria.objects.count()}")
        self.stdout.write(f"  Paquetes: {Paquete.objects.count()}")
        self.stdout.write(f"  Pases: {Pase.objects.count()}")
