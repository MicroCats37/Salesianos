"""
reparar_cupos — materializes the paid cups that were never assigned.

A paid cup is materialized from the paid capacity of its inscripcion at
payment settlement and at preregistration time. An inscription whose purchase
was marked PAGADA outside the settlement flow (seed, admin edit, legacy rows)
keeps its paid capacity without any right: the participants wait in the pool
while the saldo says the capacity is free.

This command is the reviewed, explicit way of closing that gap. It is
idempotent: running it again produces no change and never duplicates rights.

Usage:
    python manage.py reparar_cupos --dry-run
    python manage.py reparar_cupos
    python manage.py reparar_cupos --inscripcion-id <uuid>

WARNING: against real data it creates real cup rights and grants the access
they carry. Always review the `--dry-run` output first.
"""
from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand

from ninja_extra import get_injector

from modules.salesianos_fest.domain.services.flujos.reparar_cupos_flujo import (
    RepararCuposFlujo,
)


class Command(BaseCommand):
    help = (
        "Asigna los cupos pagados pendientes de las inscripciones con capacidad "
        "pagada. Es idempotente: puede ejecutarse varias veces sin duplicar derechos."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be repaired without changing anything.",
        )
        parser.add_argument(
            "--inscripcion-id",
            dest="inscripcion_id",
            default=None,
            help="Repair only this inscripcion (UUID).",
        )

    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run", False))
        inscripcion_id = options.get("inscripcion_id")

        flujo = get_injector().get(RepararCuposFlujo)
        resultado = async_to_sync(flujo._reparar)(
            inscripcion_id=inscripcion_id,
            dry_run=dry_run,
        )

        if not resultado.detalle:
            self.stdout.write("No hay inscripciones con capacidad pagada.")

        for item in resultado.detalle:
            detalle = f" — {item.motivo}" if item.motivo else ""
            self.stdout.write(
                f"  {item.inscripcion_id}: {item.estado} "
                f"(pagados={item.pagados}, asignados={item.asignados_pagados}, "
                f"disponibles={item.disponibles_pagados}, "
                f"pendientes={item.pendientes}, "
                f"creadas={item.asignaciones_creadas}){detalle}"
            )

        prefijo = "SIMULACIÓN — " if resultado.dry_run else ""
        self.stdout.write(
            f"{prefijo}Revisadas: {resultado.revisadas} | "
            f"Reparadas: {resultado.reparadas} | "
            f"Sin pendientes: {resultado.sin_pendientes} | "
            f"Errores: {resultado.errores} | "
            f"Cupos asignados: {resultado.asignaciones_creadas}"
        )
