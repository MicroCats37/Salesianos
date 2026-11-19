"""`ActivacionCompra` — el registro de la activación de derechos de una compra.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.1 I-2, §2.3, §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6

Este registro es el **hecho de activación**: distinto del pago confirmado y
distinto del estado comercial de la compra (FR-04 §1.3). No lo crea `pagos`:
lo crea el coordinador, que es su dueño.

Reglas congeladas que este modelo hace cumplir en la base de datos:

1. **Una activación efectiva por `(compra_id, origen)`** (I-2). La restricción
   `activacion_unica_por_compra_y_origen` es la guarda REAL: la comprobación en
   Python no sirve bajo concurrencia (aprendizaje #6 de FND-04).
2. **Una clave de activación por activación** (`clave`). La clave es
   **estable**: se deriva de `(compra_id, origen)`, de modo que un reintento
   entrega SIEMPRE la misma clave al dominio. El dominio la usa para no
   aplicar dos veces el mismo derecho.
3. **El pago no se revierte** (RN-C08, FR-04 §4). Este registro no tiene
   ninguna relación con el estado del pago: la activación puede fallar y el
   pago confirmado sigue confirmado.
4. **La incidencia es recuperable y segura** (RN-C08). `incidencia` guarda
   SÓLO datos seguros: un código de máquina, el origen, el número de intento
   y la fecha. Nunca el texto de una excepción, ni un payload de proveedor,
   ni un secreto.

Sobre `intentos`, `en_curso` y `ultimo_intento_en`: son el **lease** del
intento. `en_curso` dice "hay un intento reservado"; `ultimo_intento_en`
permite recuperar el intento si el proceso que lo reservó murió. Un intento
reservado NO es una activación en curso: el derecho puede haberse aplicado
en el dominio y el registro haber quedado sin cerrar. Por eso el reintento es
seguro: el dominio deduplica por `clave`.
"""

from django.db import models

from core.models import BaseModel
from modules.commerce.domain.constants import (
    MAX_LEN_CLAVE_ACTIVACION,
    EstadoActivacionCompra,
    OrigenCompra,
)


class ActivacionCompra(BaseModel):
    """La activación de derechos derivada de una compra pagada."""

    compra = models.ForeignKey(
        "commerce.Compra",
        on_delete=models.CASCADE,
        related_name="activaciones",
        verbose_name="Compra",
        help_text=(
            "La compra que financia el derecho. La activación se identifica "
            "por `(compra, origen)` (FR-04 I-2)."
        ),
    )
    origen = models.CharField(
        max_length=20,
        choices=OrigenCompra.choices,
        verbose_name="Origen",
        help_text=(
            "Dominio de origen de la compra. Determina QUÉ activador de "
            "dominio despacha el coordinador."
        ),
    )
    clave = models.CharField(
        max_length=MAX_LEN_CLAVE_ACTIVACION,
        unique=True,
        verbose_name="Clave de activación",
        help_text=(
            "Clave de idempotencia de la activación. Es ESTABLE: se deriva de "
            "`(compra_id, origen)` y no cambia entre reintentos, de modo que el "
            "dominio puede deduplicar por ella."
        ),
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoActivacionCompra.choices,
        default=EstadoActivacionCompra.PENDIENTE,
        verbose_name="Estado",
        help_text=(
            "PENDIENTE · ACTIVADA · FALLIDA. `ACTIVADA` es terminal: no se "
            "vuelve a invocar al dominio para la misma compra."
        ),
    )
    intentos = models.PositiveIntegerField(
        default=0,
        verbose_name="Intentos",
        help_text="Cuántas veces se ha intentado la activación (reintentables).",
    )
    en_curso = models.BooleanField(
        default=False,
        verbose_name="En curso",
        help_text=(
            "Hay un intento reservado. Un reintento concurrente NO vuelve a "
            "despachar; sólo puede reclamar el intento si el lease venció."
        ),
    )
    ultimo_intento_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Último intento",
        help_text=(
            "Instante en que se reservó el intento. Permite recuperar una "
            "activación abandonada por un proceso que murió."
        ),
    )
    activada_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Activada en",
        help_text="Instante en que el derecho quedó habilitado.",
    )
    incidencia = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Incidencia",
        help_text=(
            "Datos SEGUROS del último fallo: código, origen, intento y fecha. "
            "Nunca texto de excepción, ni payloads, ni secretos (RN-C08)."
        ),
    )
    detalle = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Detalle",
        help_text=(
            "Resumen del resultado del dominio, con claves de lista CERRADA. "
            "Es informativo: no es una fuente de verdad del derecho."
        ),
    )

    class Meta:
        db_table = "commerce_activacion_compra"
        verbose_name = "Activación de compra"
        verbose_name_plural = "Activaciones de compra"
        ordering = ["-created_at"]
        constraints = [
            # Una sola activación por `(compra, origen)`: es la guarda real de
            # "una activación de derechos por compra" (FR-04 I-2).
            models.UniqueConstraint(
                fields=["compra", "origen"],
                name="activacion_unica_por_compra_y_origen",
            ),
        ]
        indexes = [
            models.Index(fields=["estado"], name="ix_activacioncompra_estado"),
            models.Index(fields=["origen"], name="ix_activacioncompra_origen"),
        ]

    def __str__(self) -> str:
        return f"Activación {self.id} ({self.origen}) - {self.estado}"

    # ── Conveniencias triviales (sin lógica de negocio) ────────────────────

    @property
    def esta_activada(self) -> bool:
        """Si el derecho quedó habilitado."""
        return self.estado == EstadoActivacionCompra.ACTIVADA

    @property
    def es_reintentable(self) -> bool:
        """Si la activación se puede reintentar sin perder el pago."""
        return self.estado in (
            EstadoActivacionCompra.PENDIENTE,
            EstadoActivacionCompra.FALLIDA,
        )
