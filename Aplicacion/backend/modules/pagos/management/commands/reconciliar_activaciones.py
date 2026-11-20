"""`reconciliar_activaciones` — el disparador del reintento de derechos.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3, §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

**Por qué un comando.** `D-FND-05-07` dejó abierto el disparador del reintento
de la activación: un comando de operación, una tarea programada o el propio
flujo de pago. Este paquete elige el **comando de operación** porque es
idempotente, auditable, no corre solo y no necesita un planificador en el
proceso del API.

**Qué hace.** Revisa las órdenes de pago confirmadas cuya activación no está
resuelta y, con `--aplicar`, pide al coordinador el reintento. El reintento
**converge**: si el derecho ya estaba habilitado, no se vuelve a invocar al
dominio (FR-04 I-2).

**Qué NO hace.** No revierte cobros, no toca el estado de la orden ni el de la
compra, y no envía ninguna notificación. Un pago confirmado y un derecho
pendiente son hechos separados (RN-C08): la incidencia es recuperable, no un
error.

**Uso:**

    python manage.py reconciliar_activaciones            # informe (no muta)
    python manage.py reconciliar_activaciones --aplicar   # reintenta
    python manage.py reconciliar_activaciones --aplicar --limite 500
"""

from django.core.management.base import BaseCommand
from injector import Injector

from modules.commerce.di import CommerceModule
from modules.pagos.di import PagosModule
from modules.pagos.domain.services.core.reconciliacion_pago_service import (
    LIMITE_POR_DEFECTO,
    ReconciliacionPagoService,
)


class Command(BaseCommand):
    """Concilia los pagos verificados cuya activación no está resuelta."""

    help = (
        "Revisa los pagos confirmados con la activación de derechos pendiente o "
        "fallida y, con --aplicar, reintenta la activación de forma segura."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--aplicar",
            action="store_true",
            help=(
                "Reintenta la activación. Sin esta opción el comando sólo "
                "informa: no muta nada."
            ),
        )
        parser.add_argument(
            "--limite",
            type=int,
            default=LIMITE_POR_DEFECTO,
            help=(
                f"Máximo de órdenes confirmadas revisadas "
                f"(por defecto {LIMITE_POR_DEFECTO})."
            ),
        )

    def handle(self, *args, **options) -> None:
        injector = Injector([CommerceModule, PagosModule])
        servicio = injector.get(ReconciliacionPagoService)

        aplicar = bool(options.get("aplicar"))
        limite = int(options.get("limite") or LIMITE_POR_DEFECTO)

        informe = servicio.conciliar(limite=limite, aplicar=aplicar)

        modo = "APLICADA" if aplicar else "INFORME (no muta)"
        self.stdout.write(f"Reconciliación de activaciones · {modo}")
        self.stdout.write(
            f"Órdenes confirmadas revisadas: {informe.revisadas} · "
            f"con incidencia: {informe.con_incidencia} · "
            f"recuperadas: {informe.recuperadas} · "
            f"pendientes: {informe.pendientes}"
        )
        for item in informe.items:
            self.stdout.write(
                f"  - {item.referencia} ({item.orden_pago_id}) · "
                f"orden={item.estado_orden} · "
                f"activacion={item.estado_activacion} · "
                f"codigo={item.codigo} · "
                f"accion={item.proxima_accion}"
            )
        if informe.pendientes:
            self.stdout.write(
                self.style.WARNING(
                    f"{informe.pendientes} activación(es) siguen sin resolverse. "
                    "El pago confirmado se conserva: es una incidencia "
                    "recuperable (RN-C08)."
                )
            )
