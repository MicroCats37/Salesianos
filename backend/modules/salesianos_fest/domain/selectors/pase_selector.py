"""
PaseSelector — read-only queries for the independent party-pass catalogue.

The selector is the ONLY place that reads the pass tables. It never writes
and it never knows about the HTTP layer: it returns domain result objects.

Read-only by construction (same rule as the rest of the module's selectors).
"""
from datetime import date
from typing import Optional

from django.db import models
from django.db.models import Prefetch
from django.utils import timezone

from modules.commerce.domain.constants import EstadoCompraChoices

from ..constants import EtapaChoices
from ..models import CompraPase, Pase, PasePrecio
from ..results.pase_results import (
    PaseCatalogoResult,
    PasePrecioCatalogoResult,
)


def _es_vigente(precio: PasePrecio, hoy: date) -> bool:
    """True when the price row is inside its own validity window."""
    if precio.vigente_desde > hoy:
        return False
    if precio.vigente_hasta is not None and precio.vigente_hasta < hoy:
        return False
    return True


def _hoy() -> date:
    """Current date used by the price calendar.

    `timezone.now().date()` is the same source the sports catalogue uses
    (`CrearCompraFlujo._obtener_precio_vigente`): the pass catalogue and the
    pass purchase MUST agree on which price is vigente.
    """
    return timezone.now().date()


class PaseSelector:
    """Queries for Pase entities (read-only)."""

    @staticmethod
    def get_activos_del_evento(evento_id: str) -> list[PaseCatalogoResult]:
        """
        Return the ACTIVE passes of an event with their price calendar.

        Only ACTIVE passes are published. `precios[]` contains every ACTIVE
        price row (the stage calendar); `precio_preventa` / `precio_regular`
        expose only the price of that stage that is CURRENTLY inside its
        validity window, and `precio_vigente` is the effective unit price
        (preventa first, then regular, then None when no price is vigente).
        """
        hoy = _hoy()
        pases = (
            Pase.objects.filter(evento_id=evento_id, activo=True)
            .select_related("evento")
            .prefetch_related(
                Prefetch(
                    "precios",
                    queryset=PasePrecio.objects.filter(activo=True).order_by("etapa"),
                )
            )
            .order_by("nombre")
        )

        results: list[PaseCatalogoResult] = []
        for pase in pases:
            precios = [
                PasePrecioCatalogoResult(
                    etapa=precio.etapa,
                    precio_unitario=precio.precio_unitario,
                    vigente_desde=precio.vigente_desde,
                    vigente_hasta=precio.vigente_hasta,
                )
                for precio in pase.precios.all()
            ]

            precio_preventa = None
            precio_regular = None
            for precio in pase.precios.all():
                if not _es_vigente(precio, hoy):
                    continue
                if precio.etapa == EtapaChoices.PREVENTA:
                    precio_preventa = precio.precio_unitario
                elif precio.etapa == EtapaChoices.REGULAR:
                    precio_regular = precio.precio_unitario

            precio_vigente = (
                precio_preventa if precio_preventa is not None else precio_regular
            )

            results.append(
                PaseCatalogoResult(
                    id=str(pase.id),
                    evento_id=str(pase.evento_id),
                    nombre=pase.nombre,
                    descripcion=pase.descripcion,
                    cantidad_maxima=pase.cantidad_maxima,
                    activo=pase.activo,
                    precio_preventa=precio_preventa,
                    precio_regular=precio_regular,
                    precio_vigente=precio_vigente,
                    precios=precios,
                )
            )
        return results

    @staticmethod
    def obtener_precio_vigente(pase_id: str) -> Optional[PasePrecioCatalogoResult]:
        """
        Return the effective price of a pass right now, or None.

        The rows are ordered by stage, so PREVENTA wins over REGULAR when both
        windows overlap — the same precedence the catalogue applies.
        """
        hoy = _hoy()
        precios = PasePrecio.objects.filter(pase_id=pase_id, activo=True).order_by("etapa")
        for precio in precios:
            if _es_vigente(precio, hoy):
                return PasePrecioCatalogoResult(
                    etapa=precio.etapa,
                    precio_unitario=precio.precio_unitario,
                    vigente_desde=precio.vigente_desde,
                    vigente_hasta=precio.vigente_hasta,
                )
        return None

    @staticmethod
    def contar_cantidad_vendida(pase_id: str) -> int:
        """
        Return how many passes of this pass are already sold.

        Only the NOT cancelled purchases count: a cancelled purchase returns
        its passes to the inventory. The sum is the base of the inventory
        check performed inside the purchase transaction.
        """
        total = (
            CompraPase.objects
            .filter(pase_id=pase_id)
            .exclude(compra__estado=EstadoCompraChoices.CANCELADA)
            .aggregate(total=models.Sum("cantidad"))["total"]
        )
        return int(total or 0)
