"""
verificar_pases — READ-ONLY diagnosis of the party passes.

The command answers ONE question: is the commercial data of the party passes
consistent with the rights it delivered? It NEVER mutates anything: it reports
the anomalies it finds so the team can decide. The anomalies that already
existed are documented, never "repaired" behind the administrator's back.

Anomalies detected (stable codes):

- `V-P1` — the purchase and its payment order disagree about the commercial
  state (one is paid and the other is not).
- `V-P2` — the rights delivered exceed the quantity purchased (the slots are
  immutable: a revoked slot is consumed forever).
- `V-P3` — an ACTIVE right exists over a purchase that is NOT paid.
- `V-P4` — an ACTIVE right has no effective accreditation, and no `BLOQUEADA`
  override explains the denial.
- `V-P5` — a PAID pass purchase does not appear in the administration union
  (the payments table would hide it).
- `V-P6` — the frozen amounts disagree: `total != cantidad * precio_unitario`
  or the amount of the purchase/order is not the frozen one.
- `V-P7` — the inventory cap of the pass is exceeded.

Usage:
    python manage.py verificar_pases [--dry-run] [--json]

Exit status:
    0 — no anomalies.
    1 — anomalies found (the report is the result).
"""
import json
from decimal import Decimal

from django.core.management.base import BaseCommand

from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)
from modules.administracion.domain.selectors.admin_pago_selector import (
    AdminPagoSelector,
)
from modules.administracion.domain.services.core.admin_operacion_service import (
    DEFAULT_ORDERING_PAGOS,
)
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.eventos.domain.models import Evento
from modules.pagos.domain.constants import OrdenPagoStatus
from modules.salesianos_fest.domain.constants import (
    AutorizacionFiestaChoices,
    EstadoAcreditacionChoices,
    EstadoPaseBeneficiarioChoices,
)
from modules.salesianos_fest.domain.models import AcreditacionEvento

# ── Códigos estables ──────────────────────────────────────────────────────────

V_P1_COMPRA_ORDEN = "V-P1"
V_P2_DERECHOS_EXCEDIDOS = "V-P2"
V_P3_DERECHO_SIN_PAGO = "V-P3"
V_P4_DERECHO_SIN_ACREDITACION = "V-P4"
V_P5_FUERA_DEL_PANEL = "V-P5"
V_P6_MONTOS_INCONSISTENTES = "V-P6"
V_P7_INVENTARIO_EXCEDIDO = "V-P7"


def _anomalias_fuera_del_panel(
    lineas_pagadas: list,
    ids_visibles: set[str],
) -> list[dict]:
    """
    The PAID pass purchases that the administration union does NOT list.

    The visible ids are a PARAMETER on purpose: the command derives them from
    the REAL `AdminPagoSelector`, and a test can supply them directly instead
    of patching the selector at runtime
    (`contract/TEST_ARCHITECTURE_CONTRACT.md` §6: the doubles travel through
    the fixture graph, never through `unittest.mock`).

    Args:
        lineas_pagadas: the paid commercial lines of passes.
        ids_visibles: the purchase ids the administration payments table lists.

    Returns:
        One anomaly per paid purchase that the table would hide.
    """
    anomalias: list[dict] = []

    for linea in lineas_pagadas:
        if str(linea.compra_id) in ids_visibles:
            continue

        compra = linea.compra
        anomalias.append(
            {
                "tipo": V_P5_FUERA_DEL_PANEL,
                "compra_id": str(linea.compra_id),
                "orden_pago_id": str(compra.orden_pago_id or ""),
                "numero_orden": compra.orden_pago.numero
                if compra.orden_pago
                else None,
                "pase_id": str(linea.pase_id),
                "descripcion": (
                    "La compra de pases está pagada pero no aparece en la "
                    "unión de pagos de la administración."
                ),
            }
        )

    return anomalias


class Command(BaseCommand):
    """Report the inconsistencies of the party passes. It never repairs them."""

    help = (
        "Diagnóstico de solo lectura: busca inconsistencias en las compras de "
        "pases, sus derechos nominativos y su acreditación."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Informa sin modificar nada. Es el comportamiento por defecto: "
                "el comando nunca repara."
            ),
        )
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
            raise SystemExit(1 if anomalias else 0)

        if not anomalias:
            self.stdout.write(
                self.style.SUCCESS(
                    "Pases verificados: no se encontraron inconsistencias."
                )
            )
            raise SystemExit(0)

        self.stdout.write(
            self.style.WARNING(
                f"Pases verificados: {len(anomalias)} inconsistencia(s) encontrada(s)."
            )
        )
        for anomalia in anomalias:
            referencia = (
                anomalia.get("numero_orden")
                or anomalia.get("compra_id")
                or anomalia.get("pase_id")
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
        raise SystemExit(1)

    # ── Detección ────────────────────────────────────────────────────────────

    def _detectar(self) -> list[dict]:
        """Return every inconsistency of the party passes, in a stable order."""
        anomalias: list[dict] = []
        anomalias.extend(self._desacuerdos_compra_orden())
        anomalias.extend(self._derechos_sobre_cantidad())
        anomalias.extend(self._derechos_activos_sin_pago())
        anomalias.extend(self._derechos_sin_acreditacion())
        anomalias.extend(self._compras_fuera_del_panel())
        anomalias.extend(self._montos_inconsistentes())
        anomalias.extend(self._inventario_excedido())
        return sorted(
            anomalias,
            key=lambda anomalia: (
                anomalia["tipo"],
                str(anomalia.get("compra_id") or ""),
                str(anomalia.get("persona_id") or ""),
                str(anomalia.get("pase_id") or ""),
            ),
        )

    def _lineas(self):
        """Every commercial line of passes with its purchase and its order."""
        from modules.salesianos_fest.domain.models import CompraPase

        return (
            CompraPase.objects.select_related(
                "compra",
                "compra__orden_pago",
                "pase",
                "evento",
            )
            .order_by("created_at", "id")
        )

    def _desacuerdos_compra_orden(self) -> list[dict]:
        """V-P1 — the purchase and its order disagree about the state."""
        anomalias: list[dict] = []

        for linea in self._lineas():
            compra = linea.compra
            orden = compra.orden_pago
            if orden is None:
                continue

            pagada_compra = compra.estado == EstadoCompraChoices.PAGADA
            pagada_orden = orden.estado == OrdenPagoStatus.PAGADA

            if pagada_compra == pagada_orden:
                continue

            anomalias.append(
                {
                    "tipo": V_P1_COMPRA_ORDEN,
                    "compra_id": str(compra.id),
                    "orden_pago_id": str(orden.id),
                    "numero_orden": orden.numero,
                    "pase_id": str(linea.pase_id),
                    "estado_compra": compra.estado,
                    "estado_orden": orden.estado,
                    "descripcion": (
                        "La compra y su orden de pago no coinciden en el "
                        "estado comercial."
                    ),
                }
            )

        return anomalias

    def _derechos_sobre_cantidad(self) -> list[dict]:
        """V-P2 — the delivered rights exceed the purchased quantity."""
        from modules.salesianos_fest.domain.models import PaseBeneficiario

        anomalias: list[dict] = []

        for linea in self._lineas():
            derechos = list(
                PaseBeneficiario.objects.filter(compra_pase_id=linea.id)
            )
            activos = [
                derecho
                for derecho in derechos
                if derecho.estado == EstadoPaseBeneficiarioChoices.ACTIVA
            ]

            if len(derechos) <= linea.cantidad and len(activos) <= linea.cantidad:
                continue

            anomalias.append(
                {
                    "tipo": V_P2_DERECHOS_EXCEDIDOS,
                    "compra_id": str(linea.compra_id),
                    "orden_pago_id": str(linea.compra.orden_pago_id or ""),
                    "numero_orden": linea.compra.orden_pago.numero
                    if linea.compra.orden_pago
                    else None,
                    "pase_id": str(linea.pase_id),
                    "cantidad_comprada": linea.cantidad,
                    "derechos_registrados": len(derechos),
                    "derechos_activos": len(activos),
                    "descripcion": (
                        "La compra entregó más derechos que pases comprados: "
                        "los slots son inmutables."
                    ),
                }
            )

        return anomalias

    def _derechos_activos_sin_pago(self) -> list[dict]:
        """V-P3 — an active right over a purchase that is not paid."""
        from modules.salesianos_fest.domain.models import PaseBeneficiario

        anomalias: list[dict] = []

        derechos = (
            PaseBeneficiario.objects.filter(
                estado=EstadoPaseBeneficiarioChoices.ACTIVA,
                compra_pase__compra__estado__in=[
                    EstadoCompraChoices.PENDIENTE,
                    EstadoCompraChoices.CANCELADA,
                ],
            )
            .select_related("compra_pase", "compra_pase__compra")
            .order_by("compra_pase_id", "slot")
        )

        for derecho in derechos:
            compra = derecho.compra_pase.compra
            anomalias.append(
                {
                    "tipo": V_P3_DERECHO_SIN_PAGO,
                    "compra_id": str(compra.id),
                    "orden_pago_id": str(compra.orden_pago_id or ""),
                    "numero_orden": compra.orden_pago.numero
                    if compra.orden_pago
                    else None,
                    "pase_id": str(derecho.compra_pase.pase_id),
                    "persona_id": str(derecho.persona_id),
                    "slot": derecho.slot,
                    "estado_compra": compra.estado,
                    "descripcion": (
                        "Hay un pase activo sobre una compra que no está pagada."
                    ),
                }
            )

        return anomalias

    def _derechos_sin_acreditacion(self) -> list[dict]:
        """V-P4 — an active right without effective accreditation."""
        from modules.salesianos_fest.domain.models import PaseBeneficiario

        anomalias: list[dict] = []

        derechos = (
            PaseBeneficiario.objects.filter(
                estado=EstadoPaseBeneficiarioChoices.ACTIVA,
                compra_pase__compra__estado=EstadoCompraChoices.PAGADA,
            )
            .select_related("compra_pase", "compra_pase__compra")
            .order_by("compra_pase_id", "slot")
        )

        for derecho in derechos:
            acreditacion = AcreditacionEvento.objects.filter(
                evento_id=derecho.evento_id,
                persona_id=derecho.persona_id,
            ).first()

            if acreditacion is not None:
                bloqueada = (
                    acreditacion.autorizacion_fiesta
                    == AutorizacionFiestaChoices.BLOQUEADA
                )
                efectiva = (
                    acreditacion.estado == EstadoAcreditacionChoices.ACTIVA
                    and acreditacion.acceso_fiesta
                )
                if efectiva or bloqueada:
                    continue

            anomalias.append(
                {
                    "tipo": V_P4_DERECHO_SIN_ACREDITACION,
                    "compra_id": str(derecho.compra_pase.compra_id),
                    "orden_pago_id": str(derecho.compra_pase.compra.orden_pago_id or ""),
                    "numero_orden": derecho.compra_pase.compra.orden_pago.numero
                    if derecho.compra_pase.compra.orden_pago
                    else None,
                    "pase_id": str(derecho.compra_pase.pase_id),
                    "persona_id": str(derecho.persona_id),
                    "slot": derecho.slot,
                    "acreditacion_id": str(acreditacion.id) if acreditacion else None,
                    "descripcion": (
                        "Hay un pase activo sin acreditación efectiva y sin un "
                        "bloqueo que explique la denegación."
                    ),
                }
            )

        return anomalias

    def _compras_fuera_del_panel(self) -> list[dict]:
        """V-P5 — a paid pass purchase that the administration would not list."""
        from modules.salesianos_fest.domain.models import CompraPase

        evento = Evento.objects.filter(esta_activo=True).first()
        if evento is None:
            return []

        lineas = list(
            CompraPase.objects.filter(
                evento_id=evento.id,
                compra__estado=EstadoCompraChoices.PAGADA,
            )
            .select_related("compra", "compra__orden_pago")
            .order_by("id")
        )

        return _anomalias_fuera_del_panel(
            lineas,
            self._ids_en_panel(str(evento.id)),
        )

    def _ids_en_panel(self, evento_id: str) -> set[str] | None:
        """The ids of the purchases the administration payments table lists."""
        selector = AdminPagoSelector()
        page_size = 100
        ids: set[str] = set()
        page = 1

        while True:
            params = AdminPaginacionParams(
                page=page,
                page_size=page_size,
                offset=(page - 1) * page_size,
                q=None,
                ordering=DEFAULT_ORDERING_PAGOS,
            )
            items, _total = selector.listar(evento_id, params=params)
            ids.update(str(item.compra_id) for item in items)
            if len(items) < page_size:
                break
            page += 1

        return ids

    def _montos_inconsistentes(self) -> list[dict]:
        """V-P6 — the frozen amounts disagree."""
        anomalias: list[dict] = []

        for linea in self._lineas():
            compra = linea.compra
            orden = compra.orden_pago
            esperado = linea.precio_unitario * linea.cantidad

            if linea.total != esperado:
                anomalias.append(
                    {
                        "tipo": V_P6_MONTOS_INCONSISTENTES,
                        "compra_id": str(compra.id),
                        "orden_pago_id": str(orden.id) if orden else "",
                        "numero_orden": orden.numero if orden else None,
                        "pase_id": str(linea.pase_id),
                        "total": str(linea.total),
                        "total_esperado": str(esperado),
                        "descripcion": (
                            "El total congelado no es cantidad * precio_unitario."
                        ),
                    }
                )

            if orden is not None and linea.total != orden.monto_total:
                anomalias.append(
                    {
                        "tipo": V_P6_MONTOS_INCONSISTENTES,
                        "compra_id": str(compra.id),
                        "orden_pago_id": str(orden.id),
                        "numero_orden": orden.numero,
                        "pase_id": str(linea.pase_id),
                        "total": str(linea.total),
                        "total_esperado": str(orden.monto_total),
                        "descripcion": (
                            "El total congelado no coincide con el monto de la "
                            "orden de pago."
                        ),
                    }
                )

            if linea.total != compra.total:
                anomalias.append(
                    {
                        "tipo": V_P6_MONTOS_INCONSISTENTES,
                        "compra_id": str(compra.id),
                        "orden_pago_id": str(orden.id) if orden else "",
                        "numero_orden": orden.numero if orden else None,
                        "pase_id": str(linea.pase_id),
                        "total": str(linea.total),
                        "total_esperado": str(compra.total),
                        "descripcion": (
                            "El total congelado no coincide con el total de la "
                            "compra."
                        ),
                    }
                )

        return anomalias

    def _inventario_excedido(self) -> list[dict]:
        """V-P7 — the inventory cap of the pass is exceeded."""
        from modules.salesianos_fest.domain.models import CompraPase, Pase

        anomalias: list[dict] = []

        pases = Pase.objects.filter(activo=True).order_by("id")

        for pase in pases:
            if pase.cantidad_maxima <= 0:
                continue

            lineas = CompraPase.objects.filter(
                pase_id=pase.id,
                compra__estado__in=[
                    EstadoCompraChoices.PENDIENTE,
                    EstadoCompraChoices.PAGADA,
                ],
            ).select_related("compra", "compra__orden_pago").order_by("id")

            vendido = sum(linea.cantidad for linea in lineas)
            if vendido <= pase.cantidad_maxima:
                continue

            anomalias.append(
                {
                    "tipo": V_P7_INVENTARIO_EXCEDIDO,
                    "pase_id": str(pase.id),
                    "pase_nombre": pase.nombre,
                    "cantidad_maxima": pase.cantidad_maxima,
                    "vendido": vendido,
                    "descripcion": (
                        "La suma de los pases vendidos supera el inventario "
                        "máximo del pase."
                    ),
                }
            )

        return anomalias


__all__ = ["Command"]
