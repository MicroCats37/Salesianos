"""
Seed command for commerce module — generic purchase fixtures.

Creates personas, commerce.Compras (PENDIENTE/PAGADA/CANCELADA), OrdenPagos,
and CompraInscripcions for local development and test scenarios.

IMPORTANT: Requires seed_catalogo_fest to run first (evento + paquetes).

Invocation order:
    python manage.py seed_catalogo_fest
    python manage.py seed_commerce
    python manage.py seed_commerce --clear   # Reset and re-seed

This command is idempotent: subsequent runs reuse existing records;
use --clear to reset and re-seed from scratch.

DEVELOPMENT-ONLY: This command refuses to run outside DEBUG=True environments.
It is designed exclusively for local development and test data seeding.
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.constants import OrdenPagoStatus, METADATA_ALLOWED_KEYS
from modules.usuarios.domain.models.persona import Persona
from modules.usuarios.domain.constants import TipoDocumentoChoices, GeneroChoices
from modules.salesianos_fest.domain.models import (
    Inscripcion,
    Equipo,
    InscripcionPersona,
    CompraInscripcion,
    AsignacionCupo,
    Promocion,
    Participacion,
)
from modules.salesianos_fest.domain.constants import (
    TipoCompraChoices,
    EstadoInscripcionChoices,
    EstadoEquipoChoices,
    EstadoInscripcionPersonaChoices,
    EstadoAsignacionCupoChoices,
)

# Personas with these DNI prefixes are considered commerce/FEST test data.
COMMERCE_TEST_DNI_PREFIX = "0000000"


class Command(BaseCommand):
    help = "Seed commerce module with personas and test purchase fixtures."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing commerce/FEST test data before seeding (full reset).",
        )

    def _check_development_environment(self):
        """Refuse to run outside DEBUG=True development/test environments."""
        if not getattr(settings, "DEBUG", False):
            raise SystemExit(
                self.style.ERROR(
                    "\n  ERROR: seed_commerce is a DEVELOPMENT-ONLY command.\n"
                    "  It requires DEBUG=True in settings.\n"
                    "  For production or non-development environments, use "
                    "  migration scripts or deployment tooling instead.\n"
                )
            )

    @transaction.atomic
    def handle(self, *args, **options):
        # Guard: refuse non-development environments
        self._check_development_environment()

        clear = options.get("clear", False)

        if clear:
            self._clear_commerce_data()

        # ── Personas ──────────────────────────────────────────────────
        personas = self._seed_personas()

        # ── Catalogo check ───────────────────────────────────────────
        from modules.eventos.domain.models import Evento
        from modules.salesianos_fest.domain.models import Paquete, PaqueteDisciplina

        evento = Evento.objects.filter(esta_activo=True).first()
        if not evento:
            self.stdout.write(self.style.ERROR(
                "No active Evento found. Run 'seed_catalogo_fest' first."
            ))
            return

        paquete = Paquete.objects.filter(evento=evento, activo=True).first()
        if not paquete:
            self.stdout.write(self.style.ERROR(
                "No active Paquete found. Run 'seed_catalogo_fest' first."
            ))
            return

        # Get a discipline via PaqueteDisciplina
        paquete_disc = PaqueteDisciplina.objects.filter(paquete=paquete).first()
        disciplina = paquete_disc.disciplina if paquete_disc else None

        # Get a promocion
        from datetime import date
        hoy = date.today()
        anio_promo = hoy.year
        promocion = (
            Promocion.objects
            .filter(activa=True)
            .order_by("-anio")
            .first()
        )
        if not promocion:
            # Create a fallback one
            promocion, _ = Promocion.objects.get_or_create(
                anio=anio_promo,
                defaults={"nombre": "Senior", "activa": True},
            )

        # Get a price
        from modules.salesianos_fest.domain.models import PaquetePrecio
        precio = (
            PaquetePrecio.objects
            .filter(paquete=paquete, activo=True)
            .order_by("vigente_desde")
            .first()
        )
        precio_unitario = precio.precio_unitario if precio else Decimal("40.00")

        # ── Personas con Inscripciones ───────────────────────────────
        for persona in personas:
            self._seed_inscripcion_con_compras(
                persona=persona,
                evento=evento,
                paquete=paquete,
                promocion=promocion,
                disciplina=disciplina,
                precio_unitario=precio_unitario,
            )

        self.stdout.write(self.style.SUCCESS("\n  Commerce seed completed!"))
        self.stdout.write(f"  Personas seeded: {len(personas)}")
        self.stdout.write(f"  commerce.Compras: {Compra.objects.count()}")
        self.stdout.write(f"  OrdenPagos: {OrdenPago.objects.count()}")
        self.stdout.write(f"  CompraInscripcions: {CompraInscripcion.objects.count()}")

    # ── Helpers ────────────────────────────────────────────────────────

    def _clear_commerce_data(self):
        """
        Delete all commerce/FEST test data in dependency order (safe cascade).

        Deletes: Participacion → AsignacionCupo → CompraInscripcion →
        TransaccionPago → Compra → OrdenPago → InscripcionPersona → Equipo → Inscripcion.

        Note: OrdenPago is deleted AFTER Compra because Compra.orden_pago has
        PROTECT (prevents deleting OrdenPago while Compra references it).

        Does NOT delete Persona or Usuario records (system-level, protected by FK).
        """
        self.stdout.write("  Clearing existing commerce/FEST test data...")
        # Delete in reverse dependency order (children → parents)
        Participacion.objects.all().delete()
        AsignacionCupo.objects.all().delete()
        CompraInscripcion.objects.all().delete()
        TransaccionPago.objects.all().delete()
        # Compra must be deleted BEFORE OrdenPago (Compra.orden_pago uses PROTECT)
        Compra.objects.all().delete()
        OrdenPago.objects.all().delete()
        InscripcionPersona.objects.all().delete()
        Equipo.objects.all().delete()
        Inscripcion.objects.all().delete()
        self.stdout.write(self.style.WARNING("  Commerce/FEST test data cleared."))

    def _seed_personas(self) -> list[Persona]:
        """Create 3 test responsables (idempotent)."""
        self.stdout.write("  Seeding personas...")
        personas = []
        test_personas = [
            ("00000001", "Juan", "Perez"),
            ("00000002", "Maria", "Garcia"),
            ("00000003", "Carlos", "Rodriguez"),
        ]
        for dni, nombres, apellidos in test_personas:
            p, created = Persona.objects.get_or_create(
                numero_documento=dni,
                defaults={
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "tipo_documento": TipoDocumentoChoices.DNI,
                    "genero": GeneroChoices.MASCULINO,
                    "telefono": "999000001",
                },
            )
            personas.append(p)
            self.stdout.write(f"    {'Created' if created else 'Exists'}: {nombres} {apellidos} (DNI {dni})")
        return personas

    def _seed_inscripcion_con_compras(
        self,
        persona,
        evento,
        paquete,
        promocion,
        disciplina,
        precio_unitario: Decimal,
    ):
        """
        Create one Inscripcion + Equipo + InscripcionPersonas + multiple
        commerce.Compras (PENDIENTE, PAGADA, CANCELADA) for this persona.

        Creates a realistic purchase lifecycle:
        1. Initial purchase (PENDIENTE) — unpaid
        2. Ampliacion purchase (PAGADA) — paid with TransaccionPago
        3. Second ampliacion (CANCELLED) — cancelled
        """
        dni = persona.numero_documento
        self.stdout.write(f"\n  Seeding inscripcion for {persona.nombres} {persona.apellidos}...")

        # ── Inscripcion ──────────────────────────────────────────────
        inscripcion, insc_created = Inscripcion.objects.get_or_create(
            responsable=persona,
            evento=evento,
            paquete=paquete,
            promocion=promocion,
            defaults={
                "estado": EstadoInscripcionChoices.RECIBIDA,
            },
        )
        self.stdout.write(f"    {'Created' if insc_created else 'Exists'}: Inscripcion {inscripcion.id}")

        # ── Equipo ───────────────────────────────────────────────────
        if disciplina:
            equipo, eq_created = Equipo.objects.get_or_create(
                inscripcion=inscripcion,
                disciplina=disciplina,
            defaults={
                "nombre": f"Equipo {persona.nombres}",
                "estado": EstadoEquipoChoices.EQUIPO_ACTIVO,
                "promocion": promocion,
            },
            )
            self.stdout.write(f"    {'Created' if eq_created else 'Exists'}: Equipo {equipo.nombre}")

        # ── InscripcionPersonas ──────────────────────────────────────
        cantidad = 3
        insc_personas = []
        for i in range(cantidad):
            ip, ip_created = InscripcionPersona.objects.get_or_create(
                inscripcion=inscripcion,
                persona=persona,
                defaults={
                    "estado": EstadoInscripcionPersonaChoices.ACTIVO,
                },
            )
            insc_personas.append(ip)
            if ip_created:
                self.stdout.write(f"    Created: InscripcionPersona {i+1}")

        # ── Scenario 1: PENDIENTE initial purchase ──────────────────
        self._crear_compra_contexto(
            inscripcion=inscripcion,
            persona=persona,
            tipo=TipoCompraChoices.INICIAL,
            cantidad=paquete.minimo_compra_inicial,
            precio_unitario=precio_unitario,
            estado=EstadoCompraChoices.PENDIENTE,
            descripcion=f"Inscripcion Inicial - {paquete.nombre}",
            referencia_externa=f"INIT-{dni}-001",
        )

        # ── Scenario 2: PAGADA ampliaciÃ³n purchase ─────────────────
        compra_pagada = self._crear_compra_contexto(
            inscripcion=inscripcion,
            persona=persona,
            tipo=TipoCompraChoices.AMPLIACION,
            cantidad=5,
            precio_unitario=precio_unitario,
            estado=EstadoCompraChoices.PAGADA,
            descripcion=f"Ampliacion Cupos - {paquete.nombre}",
            referencia_externa=f"AMP-{dni}-001",
        )

        # Create a TransaccionPago to simulate payment
        orden_pago = compra_pagada.orden_pago
        if orden_pago:
            _, tx_created = TransaccionPago.objects.get_or_create(
                orden_pago=orden_pago,
                defaults={
                    "amount": compra_pagada.total,
                    "currency": "PEN",
                    "status": "CAPTURED",
                    "transaction_id": f"TXN-{dni}-001",
                    "order_number": orden_pago.numero,
                },
            )
            if tx_created:
                self.stdout.write(f"    Created: TransaccionPago for PAGADA compra")

        # ── Scenario 3: CANCELADA ampliaciÃ³n ────────────────────────
        self._crear_compra_contexto(
            inscripcion=inscripcion,
            persona=persona,
            tipo=TipoCompraChoices.AMPLIACION,
            cantidad=3,
            precio_unitario=precio_unitario,
            estado=EstadoCompraChoices.CANCELADA,
            descripcion=f"Ampliacion Cancelada - {paquete.nombre}",
            referencia_externa=f"AMP-{dni}-002",
        )

    def _crear_compra_contexto(
        self,
        inscripcion,
        persona,
        tipo: str,
        cantidad: int,
        precio_unitario: Decimal,
        estado: str,
        descripcion: str,
        referencia_externa: str,
    ) -> Compra:
        """Create a commerce.Compra + OrdenPago + CompraInscripcion in one transaction."""
        total = cantidad * precio_unitario

        # Build unique defaults key for idempotency
        # (compra is identified by estado+total+referencia to allow multiple scenarios)
        compra, compra_created = Compra.objects.get_or_create(
            estado=estado,
            total=total,
            referencia_externa=referencia_externa,
            defaults={
                "responsable": persona,
                "descripcion": descripcion,
            },
        )
        action = "Created" if compra_created else "Exists"

        # Map estado -> OrdenPagoStatus
        estado_map = {
            EstadoCompraChoices.PENDIENTE: OrdenPagoStatus.PENDIENTE,
            EstadoCompraChoices.PAGADA: OrdenPagoStatus.PAGADA,
            EstadoCompraChoices.CANCELADA: OrdenPagoStatus.CANCELADA,
        }
        orden_pago_estado = estado_map.get(estado, OrdenPagoStatus.PENDIENTE)

        # Build metadata snapshot using only METADATA_ALLOWED_KEYS
        metadata = {
            "source": "fest",
            "inscripcion_id": str(inscripcion.id),
            "paquete_id": str(inscripcion.paquete_id) if inscripcion.paquete_id else None,
            "paquete_nombre": inscripcion.paquete.nombre if inscripcion.paquete else None,
            "evento_id": str(inscripcion.evento_id) if inscripcion.evento_id else None,
            "buyer_documento": persona.numero_documento,
            "buyer_nombres": persona.nombres,
            "buyer_apellidos": persona.apellidos,
        }
        # Strip any keys not in METADATA_ALLOWED_KEYS (defensive)
        metadata = {k: v for k, v in metadata.items() if k in METADATA_ALLOWED_KEYS and v is not None}

        # Idempotency: if Compra already exists and has an orden_pago, reuse it
        if not compra_created and compra.orden_pago is not None:
            orden_pago = compra.orden_pago
            op_created = False
            # Update metadata on reuse
            orden_pago.metadata = metadata
            orden_pago.save(update_fields=["metadata", "updated_at"])
        else:
            # Create OrdenPago (no 'compra' field on OrdenPago — OneToOne is owned by Compra)
            orden_pago, op_created = OrdenPago.objects.get_or_create(
                numero=f"ORD-{uuid.uuid4().hex[:10].upper()}",
                defaults={
                    "descripcion": descripcion,
                    "referencia_externa": referencia_externa,
                    "monto_total": total,
                    "moneda": "PEN",
                    "estado": orden_pago_estado,
                    "metadata": metadata,
                },
            )
            # Link back to compra if not yet linked
            if compra.orden_pago is None:
                compra.orden_pago = orden_pago
                compra.save(update_fields=["orden_pago"])

        # Create CompraInscripcion
        ci, ci_created = CompraInscripcion.objects.get_or_create(
            compra=compra,
            inscripcion=inscripcion,
            tipo=tipo,
            defaults={
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "total": total,
            },
        )

        self.stdout.write(
            f"    {action}: Compra {estado} (cantidad={cantidad}, "
            f"total={total}, orden_pago={orden_pago.numero if orden_pago else 'N/A'})"
        )
        return compra
