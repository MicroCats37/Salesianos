"""Vocabulario cerrado del módulo `pagos`.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Este archivo declara **vocabularios cerrados**, nunca reglas:

| Vocabulario | Valores | Dueño |
|---|---|---|
| `EstadoOrdenPago` | `PENDIENTE` · `EN_VERIFICACION` · `CONFIRMADA` · `FALLIDA` · `VENCIDA` | `pagos` |
| `EstadoTransaccionPago` | `PENDIENTE` · `EXITO` · `FALLIDO` · `CANCELADO` | `pagos` |
| `EstadoOperativoPago` | 8 valores **congelados sin renumerar** (FR-01 §5.2) | `pagos` |
| `OrigenPago` | `IZIPAY` · `MANUAL` · `SIN_PAGO` | `pagos` |
| `CanalConfirmacionPago` | `BROWSER` · `NOTIFICACION` | `pagos` |
| `EstadoVerificacionPago` | `FIRMADA` · `NO_FIRMADA` · `NO_VERIFICABLE` | `pagos` |

Sobre `EstadoOperativoPago` hay UNA regla congelada: **el vocabulario vivo no se
renumera** (FR-01 §5.2). Los ocho valores son los del veredicto ya publicado
por el backend auditado; este paquete los reproduce tal cual, sin añadir, quitar
ni renombrar ninguno. `EstadoOperativoPagoService` es su **único** dueño: ninguna
otra superficie recalcula el veredicto cruzando `Compra.estado`,
`OrdenPago.estado` y las banderas del proveedor (`RN-C07`, `contratos/01` §1.4).

El código `PAGADA_SIN_LIQUIDAR` conserva su nombre histórico por congelación,
pero su `descripcion` — que es lo que el operador lee — nunca usa la palabra
«liquidación» (DEC-20, `RN-C07`).
"""

from django.db import models


# ── Estados de la orden de pago (FR-04 §1.2) ────────────────────────────────


class EstadoOrdenPago(models.TextChoices):
    """Estado de la obligación de pago.

    `EN_VERIFICACION` es el estado de "estamos verificando tu pago": la
    notificación llegó pero todavía no se pudo confirmar (RN-C07).
    """

    PENDIENTE = "PENDIENTE", "Pendiente"
    EN_VERIFICACION = "EN_VERIFICACION", "En verificación"
    CONFIRMADA = "CONFIRMADA", "Confirmada"
    FALLIDA = "FALLIDA", "Fallida"
    VENCIDA = "VENCIDA", "Vencida"


# ── Estados del intento contra el proveedor (FR-04 §1.3) ────────────────────


class EstadoTransaccionPago(models.TextChoices):
    """Estado de un intento de pago.

    Un intento `PENDIENTE` es un **intento**, no un cobro: registra que se abrió
    una sesión de pago para la orden. Los intentos cerrados se conservan para
    siempre: son la traza de auditoría.
    """

    PENDIENTE = "PENDIENTE", "Pendiente"
    EXITO = "EXITO", "Éxito"
    FALLIDO = "FALLIDO", "Fallido"
    CANCELADO = "CANCELADO", "Cancelado"


# ── Veredicto operativo (FR-01 §5.2 — CONGELADO, sin renumerar) ────────────


class EstadoOperativoPago(models.TextChoices):
    """El veredicto del operador: la respuesta única a «¿está pagado esto?».

    Es DERIVADO, nunca escrito por nadie: `pagos` lo calcula y nadie más.

    - `SIN_ORDEN` — la compra todavía no tiene orden de pago.
    - `PAGADA` — pagada, evidenciada y fechada.
    - `PAGADA_SIN_LIQUIDAR` — el dinero entró pero la compra no figura pagada.
    - `PAGADA_SIN_EVIDENCIA` — pagada sin evidencia verificable asociada.
    - `PAGADA_SIN_FECHA` — pagada y evidenciada, pero sin fecha de pago.
    - `PENDIENTE` — el pago todavía no ocurrió.
    - `CANCELADA` — la orden o la compra fueron canceladas.
    - `VENCIDA` — la orden venció.
    """

    SIN_ORDEN = "SIN_ORDEN", "Sin orden"
    PAGADA = "PAGADA", "Pagada"
    PAGADA_SIN_LIQUIDAR = "PAGADA_SIN_LIQUIDAR", "Pagada sin liquidar"
    PAGADA_SIN_EVIDENCIA = "PAGADA_SIN_EVIDENCIA", "Pagada sin evidencia"
    PAGADA_SIN_FECHA = "PAGADA_SIN_FECHA", "Pagada sin fecha"
    PENDIENTE = "PENDIENTE", "Pendiente"
    CANCELADA = "CANCELADA", "Cancelada"
    VENCIDA = "VENCIDA", "Vencida"


#: Descripciones públicas del veredicto (FR-01 §5.1).
#:
#: Una línea con la causa y el siguiente paso seguro. Son prosa FIJA: nunca
#: interpolan ids, UUIDs, montos, referencias del proveedor ni texto técnico.
DESCRIPCIONES_ESTADO_OPERATIVO: dict[str, str] = {
    EstadoOperativoPago.SIN_ORDEN: (
        "La compra todavía no tiene una orden de pago."
    ),
    EstadoOperativoPago.PAGADA: (
        "El pago está confirmado y la compra consta como pagada."
    ),
    EstadoOperativoPago.PAGADA_SIN_LIQUIDAR: (
        "El pago está confirmado y la compra todavía no figura como pagada."
    ),
    EstadoOperativoPago.PAGADA_SIN_EVIDENCIA: (
        "El pago figura como pagado pero no hay evidencia verificable asociada."
    ),
    EstadoOperativoPago.PAGADA_SIN_FECHA: (
        "El pago está confirmado y evidenciado, pero no registra fecha de pago."
    ),
    EstadoOperativoPago.PENDIENTE: (
        "El pago todavía no se ha completado."
    ),
    EstadoOperativoPago.CANCELADA: (
        "La orden de pago o la compra fueron canceladas."
    ),
    EstadoOperativoPago.VENCIDA: (
        "La orden de pago venció sin completarse."
    ),
}


# ── Origen de la evidencia de pago ─────────────────────────────────────────


class OrigenPago(models.TextChoices):
    """Procedencia de la evidencia de pago de una orden.

    - `IZIPAY` — una transacción de proveedor verificada y correlacionada.
    - `MANUAL` — una aprobación manual activa (la decide un administrador).
    - `SIN_PAGO` — no hay evidencia verificable ninguna.
    """

    IZIPAY = "IZIPAY", "Izipay"
    MANUAL = "MANUAL", "Manual"
    SIN_PAGO = "SIN_PAGO", "Sin pago"


# ── Canal de la confirmación ────────────────────────────────────────────────


class CanalConfirmacionPago(models.TextChoices):
    """Canal por el que llegó la confirmación de pago.

    - `BROWSER` — el SDK del navegador reenvió el payload del proveedor. Viaja
      por un cliente no confiable: exige autenticación y titularidad, y la
      firma se verifica cuando la clave del comercio está configurada.
    - `NOTIFICACION` — el proveedor llamó al servidor. Su autoridad viene
      **sólo** de la firma del comercio, nunca de una sesión.
    """

    BROWSER = "BROWSER", "Relato del navegador"
    NOTIFICACION = "NOTIFICACION", "Notificación del proveedor"


# ── Resultado de verificar la firma del proveedor ───────────────────────────


class EstadoVerificacionPago(models.TextChoices):
    """Resultado de verificar la firma de una confirmación.

    - `FIRMADA` — la firma verifica contra la clave del comercio.
    - `NO_FIRMADA` — se entregó una firma y NO verifica.
    - `NO_VERIFICABLE` — no se entregó firma, o la clave del comercio no está
      configurada: el proveedor no puede ser autenticado.
    """

    FIRMADA = "FIRMADA", "Firma verificada"
    NO_FIRMADA = "NO_FIRMADA", "Firma inválida"
    NO_VERIFICABLE = "NO_VERIFICABLE", "Verificación no disponible"


# ── Códigos del proveedor ───────────────────────────────────────────────────

#: Código de respuesta del proveedor que significa «operación exitosa».
CODIGO_PROVEEDOR_EXITO = "00"

#: Código de respuesta del proveedor que significa «error de comunicación»: la
#: ausencia de firma en ese caso NO es una firma inválida.
CODIGO_PROVEEDOR_ERROR_COMUNICACION = "021"

#: Vigencia por defecto de una orden de pago, en horas.
ORDEN_VIGENCIA_HORAS = 2

#: Longitud máxima admitida de una clave de idempotencia (FR-04 §2.2).
MAX_LEN_CLAVE_IDEMPOTENCIA = 128


# ── Metadata de la orden ────────────────────────────────────────────────────

#: Claves admitidas en `OrdenPago.metadata` — contexto de auditoría/pantalla.
#:
#: Son snapshots **NO autoritativos**: nunca sustituyen a una FK real ni
#: dirigen una validación de negocio o una autorización.
METADATA_ALLOWED_KEYS = frozenset(
    {
        "source",
        "purchase_reference",
        "display_context",
        "concepto_tipo",
        "concepto_id",
        "concepto_nombre",
        "evento_id",
        "edicion_id",
    }
)

#: Claves PROHIBIDAS en `OrdenPago.metadata` — defensa en profundidad.
METADATA_FORBIDDEN_KEYS = frozenset(
    {
        "auth_token",
        "session_token",
        "password",
        "secret",
        "api_key",
        "token",
        "signature",
        "payload_http",
        "key_hash",
    }
)


__all__ = [
    "CODIGO_PROVEEDOR_ERROR_COMUNICACION",
    "CODIGO_PROVEEDOR_EXITO",
    "DESCRIPCIONES_ESTADO_OPERATIVO",
    "MAX_LEN_CLAVE_IDEMPOTENCIA",
    "METADATA_ALLOWED_KEYS",
    "METADATA_FORBIDDEN_KEYS",
    "ORDEN_VIGENCIA_HORAS",
    "CanalConfirmacionPago",
    "EstadoOperativoPago",
    "EstadoOrdenPago",
    "EstadoTransaccionPago",
    "EstadoVerificacionPago",
    "OrigenPago",
]
