"""
reconciliar_pagos — repairs paid orders whose commercial settlement is pending.

A verified payment marks its order as PAGADA; the commercial settlement of the
linked purchase runs in its own transaction. When that settlement never
happened, the order stays PAGADA while its purchase stays PENDIENTE: the money
is recorded but the purchase is not settled and no cup rights were allocated.

This command is the reviewed, explicit way of closing that gap. It is
idempotent: running it again produces no change and never duplicates rights.

Usage:
    python manage.py reconciliar_pagos --dry-run
    python manage.py reconciliar_pagos
    python manage.py reconciliar_pagos --orden-pago-id <uuid>

WARNING: against real data it settles real purchases and allocates real cup
rights. Always review `--dry-run` output first.
"""
from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand

from ninja_extra import get_injector

from modules.salesianos_fest.domain.services.flujos.reconciliar_pagos_flujo import (
    ReconciliarPagosFlujo,
)


class Command(BaseCommand):
    help = (
        "Liquida las compras pendientes de órdenes de pago ya pagadas. "
        "Es idempotente: puede ejecutarse varias veces sin duplicar derechos."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be reconciled without changing anything.",
        )
        parser.add_argument(
            "--orden-pago-id",
            dest="orden_pago_id",
            default=None,
            help="Reconcile only this payment order (UUID).",
        )

    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run", False))
        orden_pago_id = options.get("orden_pago_id")

        flujo = get_injector().get(ReconciliarPagosFlujo)
        resultado = async_to_sync(flujo._reconciliar)(
            orden_pago_id=orden_pago_id,
            dry_run=dry_run,
        )

        if not resultado.detalle:
            self.stdout.write("No hay órdenes pagadas con compra pendiente.")

        for item in resultado.detalle:
            detalle = f" — {item.motivo}" if item.motivo else ""
            if item.intentos_expirados:
                detalle += f" — intentos expirados: {item.intentos_expirados}"
            self.stdout.write(
                f"  {item.numero_orden} ({item.orden_pago_id}): "
                f"{item.estado}{detalle}"
            )

        prefijo = "SIMULACIÓN — " if resultado.dry_run else ""
        self.stdout.write(
            f"{prefijo}Revisadas: {resultado.revisadas} | "
            f"Reconciliadas: {resultado.reconciliadas} | "
            f"Ya liquidadas: {resultado.ya_liquidadas} | "
            f"Omitidas: {resultado.omitidas} | "
            f"Errores: {resultado.errores}"
        )
