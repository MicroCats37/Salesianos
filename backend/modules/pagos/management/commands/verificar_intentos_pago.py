"""
verificar_intentos_pago — READ-ONLY preflight of the one-live-attempt guard.

The command answers ONE question: is the data clean enough to install the
database guard that refuses a SECOND live attempt of the same order? It NEVER
mutates anything: it reports the orders that already carry more than one live
attempt (PENDIENTE) and it does NOT delete, cancel or retire any payment
attempt — a payment attempt is an audit record and it may be money in flight.

Anomalies detected:

- `ORDEN_CON_MULTIPLES_INTENTOS_VIVOS` — the order carries more than one live
  attempt. The unique partial index of the live attempt cannot be installed
  on this data: the rows have to be resolved EXPLICITLY by the team.

Exit code:
    0 → no unsafe order: the guard can be installed.
    1 → at least one unsafe order: the guard must NOT be installed yet.

Usage:
    python manage.py verificar_intentos_pago [--json]
"""
import json

from django.core.management.base import BaseCommand

from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService

TIPO_ORDEN_INSEGURA = "ORDEN_CON_MULTIPLES_INTENTOS_VIVOS"

RUTA_DOCUMENTO = "backend/modules/pagos/docs/despliegue_intento_unico.md"


class Command(BaseCommand):
    """Report the orders that are unsafe for the one-live-attempt guard."""

    help = (
        "Preflight de solo lectura: informa las órdenes de pago con más de un "
        "intento vivo (PENDIENTE) antes de instalar la restricción de intento "
        "único."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            action="store_true",
            help="Emite el informe en JSON.",
        )

    def handle(self, *args, **options):
        # The core service is instantiated directly: the pagos DI module is
        # not registered in the injector (it is disabled project-wide), and
        # the service has no dependency to resolve.
        core = IzipayCoreService()
        inseguras = core.ordenes_con_multiples_intentos_vivos()
        resumen = core.resumen_intentos_vivos()

        if options.get("json"):
            self.stdout.write(
                json.dumps(
                    {
                        "resumen": resumen,
                        "inseguras": [self._insegura(orden) for orden in inseguras],
                        "total": len(inseguras),
                        "guard_instalable": not inseguras,
                    },
                    indent=2,
                    default=str,
                )
            )
            self._terminar(1 if inseguras else 0)
            return

        if not inseguras:
            self.stdout.write(
                self.style.SUCCESS(
                    "Intentos de pago verificados: ninguna orden tiene más de un "
                    "intento vivo — la restricción de intento único puede "
                    "instalarse."
                )
            )
            self.stdout.write(
                f"  Órdenes con intento vivo: "
                f"{resumen['ordenes_con_intento_vivo']}; "
                f"intentos vivos: {resumen['intentos_vivos']}."
            )
            self._terminar(0)
            return

        self.stdout.write(
            self.style.WARNING(
                f"Intentos de pago verificados: {len(inseguras)} orden(es) con más "
                "de un intento vivo."
            )
        )
        for orden in inseguras:
            self.stdout.write(
                f"  [{TIPO_ORDEN_INSEGURA}] "
                f"{orden.numero_orden or orden.orden_pago_id} — "
                f"{orden.intentos_vivos} intento(s) vivo(s): "
                f"{', '.join(orden.transaction_ids)}"
            )
        self.stdout.write(
            self.style.WARNING(
                "El informe es de solo lectura: no se modificó ningún registro."
            )
        )
        self.stdout.write(
            "La restricción de intento único NO debe instalarse todavía: "
            f"resuelve estas órdenes explícitamente (ver {RUTA_DOCUMENTO})."
        )
        self._terminar(1)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _insegura(self, orden) -> dict:
        """Return the report of one unsafe order."""
        return {
            "tipo": TIPO_ORDEN_INSEGURA,
            "orden_pago_id": orden.orden_pago_id,
            "numero_orden": orden.numero_orden,
            "intentos_vivos": orden.intentos_vivos,
            "transaction_ids": orden.transaction_ids,
        }

    def _terminar(self, codigo: int) -> None:
        """
        Finish the command with the given exit code.

        `SystemExit` is raised instead of returning a value: Django writes the
        return value of `handle` to the standard output, and the exit code of
        the command must stay out of the report.
        """
        if codigo:
            raise SystemExit(codigo)
