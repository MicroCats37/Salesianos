"""
verificar_pagos — READ-ONLY diagnosis of the payment evidence.

The command answers ONE question: is there any purchase that says "paid"
without a verifiable proof? It NEVER mutates anything: it reports the
anomalies it finds so the team can decide, and the anomalies that already
existed are documented, never "repaired" behind the administrator's back.

Anomalies detected:

- `COMPRA_PAGADA_SIN_EVIDENCIA` — the purchase is PAGADA but its order has
  neither a correlated successful provider transaction nor an active manual
  approval. This is the defect the manual approval closes.
- `ORDEN_PAGADA_SIN_EVIDENCIA` — the order is PAGADA without any evidence.
- `APROBACION_SIN_COMPRA` — an approval exists for an order that funds no
  purchase.
- `APROBACION_NO_CORRELACIONADA` — the approved amount or currency differs
  from the order: the evidence cannot settle that order.
- `APROBACION_SOBRE_ORDEN_CANCELADA` — an active approval of a cancelled
  order or purchase.
- `APROBACION_Y_PAGO_PROVEEDOR` — an active approval of an order that was
  also paid through the provider: two contradictory evidences.

Usage:
    python manage.py verificar_pagos [--json]
"""
import json

from django.core.management.base import BaseCommand

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.constants import (
    EstadoAprobacionPagoManual,
    IzipayStatus,
    OrigenPago,
    OrdenPagoStatus,
)
from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago, TransaccionPago


class Command(BaseCommand):
    """Report the purchases and orders whose payment evidence is missing."""

    help = "Diagnóstico de solo lectura: busca pagos y compras sin evidencia verificable."

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            action="store_true",
            help="Emite el informe en JSON.",
        )

    def handle(self, *args, **options):
        anomalias = self._detectar()

        if options.get("json"):
            self.stdout.write(
                json.dumps(
                    {"anomalias": anomalias, "total": len(anomalias)},
                    indent=2,
                    default=str,
                )
            )
            return

        if not anomalias:
            self.stdout.write(
                self.style.SUCCESS(
                    "Pagos verificados: no se encontraron anomalías de evidencia."
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"Pagos verificados: {len(anomalias)} anomalía(s) encontrada(s)."
            )
        )
        for anomalia in anomalias:
            referencia = (
                anomalia.get("numero_orden")
                or anomalia.get("compra_id")
                or anomalia.get("orden_pago_id")
                or ""
            )
            self.stdout.write(
                f"  [{anomalia['tipo']}] {referencia} — {anomalia['descripcion']}"
            )
        self.stdout.write(
            self.style.WARNING(
                "El informe es de solo lectura: no se modificó ningún registro."
            )
        )

    # ── Detección ────────────────────────────────────────────────────────────

    def _detectar(self) -> list[dict]:
        """Return every anomaly of the payment evidence."""
        anomalias: list[dict] = []
        anomalias.extend(self._compras_sin_evidencia())
        anomalias.extend(self._ordenes_sin_evidencia())
        anomalias.extend(self._anomalias_de_aprobacion())
        return anomalias

    def _evidencia_izipay(self, orden) -> bool:
        """Return True when the order carries a correlated successful attempt."""
        return TransaccionPago.objects.filter(
            orden_pago_id=orden.id,
            status=IzipayStatus.EXITO,
            amount=orden.monto_total,
            currency=orden.moneda,
        ).exists()

    def _aprobacion_activa(self, orden) -> AprobacionPagoManual | None:
        """Return the active manual approval of the order, if there is one."""
        return (
            AprobacionPagoManual.objects
            .filter(
                orden_pago_id=orden.id,
                estado=EstadoAprobacionPagoManual.APROBADA,
            )
            .first()
        )

    def _compras_sin_evidencia(self) -> list[dict]:
        """Return the purchases marked as paid without a verifiable proof."""
        from modules.commerce.domain.models import Compra

        anomalias: list[dict] = []
        compras = Compra.objects.filter(
            estado=EstadoCompraChoices.PAGADA,
            orden_pago__isnull=False,
        ).select_related("orden_pago")

        for compra in compras:
            orden = compra.orden_pago
            if orden is None:
                continue
            if self._evidencia_izipay(orden):
                continue
            if self._aprobacion_activa(orden) is not None:
                continue
            anomalias.append(
                {
                    "tipo": "COMPRA_PAGADA_SIN_EVIDENCIA",
                    "compra_id": str(compra.id),
                    "orden_pago_id": str(orden.id),
                    "numero_orden": orden.numero,
                    "origen_detectado": OrigenPago.SIN_PAGO,
                    "descripcion": (
                        "La compra está pagada pero su orden no tiene una "
                        "transacción exitosa correlacionada ni una aprobación "
                        "manual activa."
                    ),
                }
            )

        return anomalias

    def _ordenes_sin_evidencia(self) -> list[dict]:
        """Return the paid orders without a verifiable proof."""
        anomalias: list[dict] = []
        ordenes = OrdenPago.objects.filter(
            estado=OrdenPagoStatus.PAGADA
        ).select_related()

        for orden in ordenes:
            if self._evidencia_izipay(orden):
                continue
            if self._aprobacion_activa(orden) is not None:
                continue
            anomalias.append(
                {
                    "tipo": "ORDEN_PAGADA_SIN_EVIDENCIA",
                    "orden_pago_id": str(orden.id),
                    "numero_orden": orden.numero,
                    "origen_detectado": OrigenPago.SIN_PAGO,
                    "descripcion": (
                        "La orden está pagada pero no tiene ninguna evidencia "
                        "verificable de pago."
                    ),
                }
            )

        return anomalias

    def _anomalias_de_aprobacion(self) -> list[dict]:
        """Return the inconsistent manual approvals."""
        from modules.commerce.domain.models import Compra

        anomalias: list[dict] = []
        aprobaciones = (
            AprobacionPagoManual.objects
            .filter(estado=EstadoAprobacionPagoManual.APROBADA)
            .select_related("orden_pago")
        )

        for aprobacion in aprobaciones:
            orden = aprobacion.orden_pago

            if aprobacion.monto != orden.monto_total or (
                aprobacion.moneda != orden.moneda
            ):
                anomalias.append(
                    {
                        "tipo": "APROBACION_NO_CORRELACIONADA",
                        "aprobacion_id": str(aprobacion.id),
                        "orden_pago_id": str(orden.id),
                        "numero_orden": orden.numero,
                        "descripcion": (
                            "El monto o la moneda de la aprobación no "
                            "coinciden con la orden de pago."
                        ),
                    }
                )

            compra = Compra.objects.filter(orden_pago_id=orden.id).first()
            if compra is None:
                anomalias.append(
                    {
                        "tipo": "APROBACION_SIN_COMPRA",
                        "aprobacion_id": str(aprobacion.id),
                        "orden_pago_id": str(orden.id),
                        "numero_orden": orden.numero,
                        "descripcion": (
                            "La aprobación no corresponde a ninguna compra: no "
                            "hay derechos comerciales que liquidar."
                        ),
                    }
                )
            elif compra.estado == EstadoCompraChoices.CANCELADA:
                anomalias.append(
                    {
                        "tipo": "APROBACION_SOBRE_ORDEN_CANCELADA",
                        "aprobacion_id": str(aprobacion.id),
                        "orden_pago_id": str(orden.id),
                        "numero_orden": orden.numero,
                        "descripcion": (
                            "La aprobación está activa sobre una compra "
                            "cancelada."
                        ),
                    }
                )

            if self._evidencia_izipay(orden):
                anomalias.append(
                    {
                        "tipo": "APROBACION_Y_PAGO_PROVEEDOR",
                        "aprobacion_id": str(aprobacion.id),
                        "orden_pago_id": str(orden.id),
                        "numero_orden": orden.numero,
                        "descripcion": (
                            "La orden tiene una aprobación manual activa y "
                            "también un pago exitoso del proveedor."
                        ),
                    }
                )

        return anomalias
