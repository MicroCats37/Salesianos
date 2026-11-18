"""
Constants — Choices and module-level constants for pagos.
"""
from django.db import models


class IzipayStatus(models.TextChoices):
    """Status choices for Izipay transaction attempts."""
    PENDIENTE = "PENDIENTE", "Pendiente"
    EXITO = "EXITO", "Exito"
    FALLIDO = "FALLIDO", "Fallido"
    CANCELADO = "CANCELADO", "Cancelado"


class OrdenPagoStatus(models.TextChoices):
    """Status choices for a generic payment order (OrdenPago)."""
    PENDIENTE = "PENDIENTE", "Pendiente"
    PAGADA = "PAGADA", "Pagada"
    CANCELADA = "CANCELADA", "Cancelada"
    VENCIDA = "VENCIDA", "Vencida"


class EstadoOperativoPago(models.TextChoices):
    """
    Operator verdict of a payment order — the ONE answer to "is this payment
    done?".

    The verdict is DERIVED, never typed by anybody: `pagos` owns it, and every
    surface that publishes a payment state publishes THIS one instead of
    making the reader compare three sibling facts.

    SIN_ORDEN            — the purchase has no payment order yet.
    PAGADA               — paid, settled, evidenced and dated.
    PAGADA_SIN_LIQUIDAR  — the money is in but the rights are not activated.
    PAGADA_SIN_EVIDENCIA — paid but NOT verifiable (no correlated evidence).
    PAGADA_SIN_FECHA     — paid and evidenced, but without a payment date.
    PENDIENTE            — the payment has not happened yet.
    CANCELADA            — the order or the purchase was cancelled.
    VENCIDA              — the order expired.
    """

    SIN_ORDEN = "SIN_ORDEN", "Sin orden"
    PAGADA = "PAGADA", "Pagada"
    PAGADA_SIN_LIQUIDAR = "PAGADA_SIN_LIQUIDAR", "Pagada sin liquidar"
    PAGADA_SIN_EVIDENCIA = "PAGADA_SIN_EVIDENCIA", "Pagada sin evidencia"
    PAGADA_SIN_FECHA = "PAGADA_SIN_FECHA", "Pagada sin fecha"
    PENDIENTE = "PENDIENTE", "Pendiente"
    CANCELADA = "CANCELADA", "Cancelada"
    VENCIDA = "VENCIDA", "Vencida"


class SettlementStatus(models.TextChoices):
    """
    Public state of the commercial settlement driven by a verified payment.

    SETTLED        — the purchase is paid and its rights are allocated.
    PENDING        — the payment is recorded but the settlement is not
                     complete; a later confirmation converges it.
    NOT_APPLICABLE — there is no settlement to perform (e.g. the payment
                     itself did not succeed).
    """
    SETTLED = "SETTLED", "Activación completada"
    PENDING = "PENDING", "Activación pendiente"
    NOT_APPLICABLE = "NOT_APPLICABLE", "Sin activación comercial"


class CanalConfirmacionPago(models.TextChoices):
    """
    Channel that delivered a provider confirmation.

    BROWSER      — the frontend SDK relayed the provider payload. It is
                   authenticated and bound to the owner of the order, but it
                   travels through an untrusted client.
    NOTIFICACION — the provider called us server to server. Its authority
                   comes from the merchant signature, never from a session.
    """
    BROWSER = "BROWSER", "Relato del navegador"
    NOTIFICACION = "NOTIFICACION", "Notificación del proveedor"


class CanalPagoManual(models.TextChoices):
    """
    Closed set of the channels through which a manual payment can arrive.

    The channel is part of the EVIDENCE: it tells the audit trail how the
    money reached the institution. The set is closed on purpose — an unknown
    channel is a validation error, never a free text field.
    """

    TRANSFERENCIA_BANCARIA = "TRANSFERENCIA_BANCARIA", "Transferencia bancaria"
    EFECTIVO = "EFECTIVO", "Efectivo"
    YAPE = "YAPE", "Yape"
    PLIN = "PLIN", "Plin"
    OTRO = "OTRO", "Otro"


class EstadoAprobacionPagoManual(models.TextChoices):
    """
    State of a manual payment approval.

    APROBADA — the evidence is active: it proves the payment of its order.
    ANULADA  — the evidence was revoked by an administrator; it is kept
               forever as the audit trail of the decision.
    """

    APROBADA = "APROBADA", "Aprobada"
    ANULADA = "ANULADA", "Anulada"


class OrigenPago(models.TextChoices):
    """
    Origin of the payment evidence of an order.

    IZIPAY   — a correlated successful provider transaction.
    MANUAL   — an active manual approval recorded by an administrator.
    SIN_PAGO — no verifiable evidence at all.
    """

    IZIPAY = "IZIPAY", "Izipay"
    MANUAL = "MANUAL", "Manual"
    SIN_PAGO = "SIN_PAGO", "Sin pago"


class EstadoVerificacionPago(models.TextChoices):
    """
    Result of verifying the provider signature of a confirmation.

    FIRMADA       — the signature verifies against the merchant key.
    NO_FIRMADA    — a signature was delivered and it does NOT verify.
    NO_VERIFICABLE — no signature was delivered, or the merchant key is not
                     configured, so the provider cannot be authenticated.
    """
    FIRMADA = "FIRMADA", "Firma verificada"
    NO_FIRMADA = "NO_FIRMADA", "Firma inválida"
    NO_VERIFICABLE = "NO_VERIFICABLE", "Verificación no disponible"


# ── Payment attempt lifecycle ─────────────────────────────────────────────────

# A PENDIENTE TransaccionPago is an ATTEMPT, not a charge: it only records
# that a provider session was opened for an order. Re-opening the checkout
# NEVER replays a provider session: the live attempt is retired and a fresh
# one — with its own provider session and its own transaction identity — is
# created for the new checkout.

# Metadata key that holds the provider session token of an attempt. The
# session belongs to the attempt that opened it: it is handed to the browser
# exactly once and it is never replayed for another checkout. It is dropped
# as soon as the attempt is confirmed.
CLAVE_TOKEN_SESION = "token_sesion"


# Allowed keys for OrdenPago.metadata — audit/display context only.
# These are NON-AUTHORITATIVE snapshots. They must NEVER replace real FKs
# or drive authorization/business validation.
METADATA_ALLOWED_KEYS = frozenset([
    "source",               # Origin system or trigger (e.g. "fest", "store")
    "purchase_reference",   # Human-readable purchase reference
    "display_context",      # UI display hints (e.g. {"label": "..."})
    "inscripcion_id",       # UUID of the origin inscripcion (snapshot)
    "paquete_id",           # UUID of the package (snapshot)
    "paquete_nombre",       # Package name (display snapshot)
    "evento_id",            # UUID of the event (snapshot)
    "buyer_documento",      # Buyer DNI (audit snapshot)
    "buyer_nombres",        # Buyer first names (audit snapshot)
    "buyer_apellidos",      # Buyer last names (audit snapshot)
])

# Forbidden keys — never allowed in metadata
METADATA_FORBIDDEN_KEYS = frozenset([
    "auth_token",
    "session_token",
    "password",
    "secret",
    "api_key",
    "token",
])
