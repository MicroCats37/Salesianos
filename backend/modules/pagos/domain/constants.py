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
# must not pile up attempts, so the active attempt is reused while it is
# still usable and the superseded ones are expired.
#
# Reuse window of an active attempt. It MUST stay below the validity of the
# provider session it holds: a session that is no longer usable must never
# be handed back to the browser.
INTENTO_REUTILIZABLE_MINUTOS = 5

# Metadata key that holds the provider session token of an attempt. It lets
# the backend reuse the SAME provider session — and therefore the same
# transaction id — instead of opening a second charge opportunity for the
# same order. It is dropped as soon as the attempt is confirmed.
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
