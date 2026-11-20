"""Modelos del módulo `pagos`.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Tres agregados, agrupados aquí porque comparten la misma semántica — el
**cobro** — y porque el historial de pagos es indivisible:

| Modelo | Rol | Atributos congelados |
|---|---|---|
| `OrdenPago` | la obligación de pago | `estado` · `monto` · `moneda` · `referencia` |
| `TransaccionPago` | un **intento** contra el proveedor | `intento` · `referencia_proveedor` · `estado` · `verificada` · `evidencia` |
| `RegistroIdempotencia` | la clave de idempotencia del borde HTTP | `ambito` · `clave` · `huella` · `respuesta` |

Sobre la relación con el agregado comercial: `OrdenPago` **no** declara una FK
a `Compra`. La relación la posee `commerce.Compra.orden_pago` (OneToOne,
nullable) — así la dirección de dependencias queda `commerce -> pagos` y el
módulo de pago nunca importa el de comercio. `pagos` consulta el estado
comercial de la compra a través del **port** `IEstadoCompraOrdenPagoService`
(`domain/ports`).

Los modelos son planos y anémicos (`contract/django-app-architecture-contract.md`
§4.2): campos, `Meta` y `__str__`. La lógica vive en los servicios.
"""

from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from modules.pagos.domain.constants import (
    EstadoAprobacionPagoManual,
    EstadoOrdenPago,
    EstadoTransaccionPago,
)


class OrdenPago(BaseModel):
    """Obligación de pago de una compra.

    Es agnóstica del dominio: no conoce inscripciones, pases ni productos. Su
    contexto comercial viaja como snapshot en `metadata` (claves permitidas,
    nunca autoritativas) y en la compra que la financia.

    Invariantes congeladas (FR-04 §1.2):

    - `monto` y `moneda` coinciden **exactamente** con `Compra.total` y
      `Compra.moneda`: el monto es un snapshot congelado y nadie lo ajusta.
    - `referencia` es la referencia **visible** del proveedor. Prohibido
      exponer en ella secretos, tokens de sesión ni payloads firmados
      (`contratos/03` §8).
    - El estado es un hecho de la ORDEN. El hecho del proveedor vive en
      `TransaccionPago` y el veredicto del operador lo calcula
      `EstadoOperativoPagoService`. Son tres hechos distintos.
    """

    history = HistoricalRecords()

    referencia = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Referencia de la orden",
        help_text=(
            "Referencia visible del proveedor. Es la clave con la que el "
            "proveedor identifica la orden en sus avisos."
        ),
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoOrdenPago.choices,
        default=EstadoOrdenPago.PENDIENTE,
        verbose_name="Estado",
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto",
        help_text="Snapshot congelado del monto que se debe cobrar.",
    )
    moneda = models.CharField(
        max_length=3,
        default="PEN",
        verbose_name="Moneda",
        help_text="Código ISO-4217 del monto. Prohibido=float para dinero.",
    )
    pagada_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de pago",
        help_text="Instante en que se confirmó el pago. Nulo = aún no se pagó.",
    )
    vence_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Vencimiento",
        help_text="Instante en que la orden deja de admitir un pago.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Contexto de auditoría",
        help_text=(
            "Snapshot NO autoritativo de contexto (auditoría/pantalla). "
            "Nunca sustituye a una FK real ni dirige una autorización."
        ),
    )

    class Meta:
        db_table = "pagos_ordenpago"
        verbose_name = "Orden de pago"
        verbose_name_plural = "Órdenes de pago"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gte=0),
                name="ordenpago_monto_no_negativo",
            ),
        ]
        indexes = [
            models.Index(fields=["estado"], name="ix_ordenpago_estado"),
            models.Index(fields=["referencia"], name="ix_ordenpago_referencia"),
        ]

    def __str__(self) -> str:
        return f"OrdenPago {self.referencia} - {self.estado}"


class TransaccionPago(BaseModel):
    """Un **intento** de pago contra el proveedor, ligado a una orden.

    Una transacción `PENDIENTE` es un INTENTO, no un cobro: registra que se
    abrió una sesión de pago para la orden. Al reabrir el checkout se crea un
    intento NUEVO (con su propio ordinal y su propia identidad) y el anterior
    queda cerrado como historial — nunca se borra ni se reescribe
    (`RN-C04`: preservar trazabilidad de todo intento).

    Invariantes congeladas (FR-04 §1.3):

    - `intento` es creciente por orden y único dentro de ella.
    - `referencia_proveedor` identifica el intento. Es dato técnico: sólo se
      expone en detalle técnico autorizado.
    - `verificada` dice si la notificación fue **firmada y verificada** en
      servidor. Un pago no verificado nunca declara el orden pagado.
    - `evidencia` conserva la evidencia de la aprobación (aplica cuando el
      pago no vino del proveedor).
    """

    history = HistoricalRecords()

    orden_pago = models.ForeignKey(
        OrdenPago,
        on_delete=models.PROTECT,
        related_name="intentos",
        verbose_name="Orden de pago",
    )
    intento = models.PositiveIntegerField(
        verbose_name="Número de intento",
        help_text="Posición del intento dentro de su orden. Creciente.",
    )
    referencia_proveedor = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Referencia del proveedor",
        help_text=(
            "Identificador técnico del intento. Sólo se expone en detalle "
            "técnico autorizado."
        ),
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoTransaccionPago.choices,
        default=EstadoTransaccionPago.PENDIENTE,
        verbose_name="Estado",
    )
    verificada = models.BooleanField(
        default=False,
        verbose_name="Firma verificada",
        help_text=(
            "La confirmación del proveedor fue firmada y verificada en servidor."
        ),
    )
    evidencia = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Evidencia",
        help_text=(
            "Evidencia de la aprobación (canal, código de respuesta, fecha). "
            "Nunca contiene credenciales ni el payload firmado."
        ),
    )
    codigo_respuesta = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="Código de respuesta",
    )
    mensaje_respuesta = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Mensaje de respuesta",
    )
    metodo_pago = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="Método de pago",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Contexto del proveedor",
        help_text="Payload del proveedor saneado: sin credenciales ni secretos.",
    )

    class Meta:
        db_table = "pagos_transaccionpago"
        verbose_name = "Intento de pago"
        verbose_name_plural = "Intentos de pago"
        ordering = ["orden_pago_id", "intento"]
        constraints = [
            models.UniqueConstraint(
                fields=["orden_pago", "intento"],
                name="transaccion_intento_unico_por_orden",
            ),
            # Una orden tiene como máximo UN intento vivo. Los intentos
            # cerrados (EXITO, FALLIDO, CANCELADO) no se tocan: la traza de
            # auditoría de la orden nunca se reescribe.
            models.UniqueConstraint(
                fields=["orden_pago"],
                condition=models.Q(estado=EstadoTransaccionPago.PENDIENTE),
                name="transaccion_intento_vivo_unico_por_orden",
            ),
        ]
        indexes = [
            models.Index(
                fields=["orden_pago", "estado"],
                name="ix_transaccion_orden_estado",
            ),
        ]

    def __str__(self) -> str:
        return f"Intento {self.intento} - {self.estado}"


class AprobacionPagoManual(BaseModel):
    """Evidencia auditada de un pago confirmado fuera del proveedor."""

    orden_pago = models.ForeignKey(
        OrdenPago, on_delete=models.PROTECT, related_name="aprobaciones_manuales"
    )
    actor = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="aprobaciones_manuales_pago",
    )
    canal = models.CharField(max_length=32)
    referencia = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=3)
    motivo = models.TextField(max_length=1000)
    estado = models.CharField(
        max_length=20,
        choices=EstadoAprobacionPagoManual.choices,
        default=EstadoAprobacionPagoManual.APROBADA,
    )

    class Meta:
        db_table = "pagos_aprobacionpagomanual"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["orden_pago"],
                condition=models.Q(estado=EstadoAprobacionPagoManual.APROBADA),
                name="aprobacion_manual_activa_unica_por_orden",
            )
        ]
        indexes = [
            models.Index(fields=["orden_pago", "estado"], name="ix_aprobmanual_orden_estado"),
            models.Index(fields=["actor", "created_at"], name="ix_aprobmanual_actor_fecha"),
        ]

    def __str__(self) -> str:
        return f"Aprobacion manual {self.orden_pago_id} - {self.estado}"


class RegistroIdempotencia(BaseModel):
    """La clave de idempotencia del borde HTTP (FR-04 §2.2).

    Toda mutación que pueda repetirse acepta una clave explícita
    (header `Idempotency-Key`). El registro guarda:

    - `ambito` — endpoint + actor. Dos claves distintas ⇒ dos operaciones
      distintas; la misma clave en otro ámbito es otra operación.
    - `clave` — la clave opaca del cliente (≤ 128 caracteres).
    - `huella` — el resumen SHA-256 de la petición. **Nunca** se guarda el
      payload: sólo su huella, para poder detectar una reutilización con otro
      contenido.
    - `respuesta` — el resultado de la primera ejecución, para que la
      repetición devuelva exactamente lo mismo (mismo `data`, mismo `success`)
      con el status HTTP de la primera vez. Nunca 500.
    """

    ambito = models.CharField(
        max_length=200,
        verbose_name="Ámbito",
        help_text="Endpoint + actor. La clave sólo es única dentro del ámbito.",
    )
    clave = models.CharField(
        max_length=128,
        verbose_name="Clave",
        help_text="Clave opaca generada por el cliente para una intención.",
    )
    huella = models.CharField(
        max_length=64,
        verbose_name="Huella de la petición",
        help_text="SHA-256 de la petición normalizada. Nunca el payload.",
    )
    respuesta = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Respuesta registrada",
    )
    codigo_estado = models.PositiveSmallIntegerField(
        default=200,
        verbose_name="Código de estado",
    )

    class Meta:
        db_table = "pagos_registroidempotencia"
        verbose_name = "Registro de idempotencia"
        verbose_name_plural = "Registros de idempotencia"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["ambito", "clave"],
                name="idempotencia_clave_unica_por_ambito",
            ),
        ]

    def __str__(self) -> str:
        return f"Idempotencia {self.ambito}:{self.clave}"


__all__ = [
    "OrdenPago",
    "RegistroIdempotencia",
    "TransaccionPago",
]
