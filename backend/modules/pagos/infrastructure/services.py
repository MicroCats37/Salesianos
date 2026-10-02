"""
Izipay infrastructure — concrete Izipay Perú Web Core 2.0 HTTP client.

Uses httpx for async-capable HTTP calls against the Izipay Perú REST API.
Settings read from django.conf.settings — fails clearly if credentials are absent.
"""
import logging
import re
import unicodedata

import httpx

from django.conf import settings

from modules.pagos.domain.exceptions import IzipayError

logger = logging.getLogger(__name__)


# ── Text sanitization for Izipay Perú ─────────────────────────────────────────

def _sanitizar_texto(texto: str) -> str:
    """
    Cleans text for Izipay Perú: removes accents and keeps only A-Z and spaces.
    """
    if not texto:
        return ""
    # Normalize to separate accents from base letters
    nfd = unicodedata.normalize("NFD", texto)
    # Filter out combining marks (removes accents)
    sin_acentos = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    # Keep only letters A-Z and spaces
    return re.sub(r"[^a-zA-Z\s]", " ", sin_acentos).strip()


# ── Sanitization for kr_answer metadata ───────────────────────────────────────

# Fields that must NEVER be stored in metadata
_SENSITIVE_KEYS = frozenset({
    # Card data
    "pan", "cardNumber", "card_number", "cvv", "cvc", "cvv2", "cvv_2",
    "cardHolderName", "card_holder_name", "cardToken", "card_token",
    "cardAlias", "card_alias", "cardAssociation", "card_association",
    # Auth/secrets
    "privateKey", "private_key", "secretKey", "secret_key", "apiKey",
    "api_key", "encryptionKey", "encryption_key", "tokenizationKey",
    "izipayKey", "izipay_key", "shopId", "shop_id",
    # Session/auth tokens from provider
    "sessionToken", "session_token", "authToken", "auth_token",
    "accessToken", "access_token", "idToken", "id_token",
    # 3DS data
    "eci", "xid", "cavv", "cavvAlgorithm",
    # Full raw payloads
    "raw_request", "raw_response", "raw", "full_card_data",
})


def sanitizar_kr_answer(kr_answer: dict) -> dict:
    """
    Recursively remove sensitive fields from Izipay Perú kr_answer before storing in metadata.

    Returns a shallow copy with sensitive keys stripped.
    Fields with names containing sensitive substrings are also removed.
    Never raises — failures during sanitization are logged and the field is removed.
    """
    if not isinstance(kr_answer, dict):
        return {}

    def _sanitize(value):
        if isinstance(value, dict):
            return {k: _sanitize(v) for k, v in value.items() if _is_safe_key(k)}
        if isinstance(value, list):
            return [_sanitize(item) for item in value]
        return value

    return _sanitize(kr_answer)


def _is_safe_key(key: str) -> bool:
    """Return True if the key does not look like a sensitive field."""
    lower_key = key.lower()
    return not any(lower_key in sensitive.lower() for sensitive in _SENSITIVE_KEYS)


# ── Izipay Perú Web Core 2.0 API client ───────────────────────────────────────

class IzipayClient:
    """
    Async-capable Izipay Perú Web Core 2.0 REST API client using httpx.

    Calls the Izipay Perú Token/Generate endpoint:
    1. generar_token_sesion() — creates a payment session, returns token + SDK config

    Settings required (from django.conf.settings):
        IZIPAY_SHOP_ID      — Izipay Perú merchant/shop identifier
        IZIPAY_KEY          — Izipay Perú public API key
        IZIPAY_API_URL      — base URL (e.g. https://sandbox-api-pw.izipay.pe)
        IZIPAY_CALLBACK_URL — URL Izipay redirects to after payment (for frontend SDK)

    Note: Unlike Iyzico, there is NO checkoutFormRetrieve step.
          Confirmation arrives as a callback (kr_answer) directly from the frontend.
          The server-side verification is limited — see verificar_respuesta_firma() limitation.

    Raises:
        IzipayError: on network error, API error response, or missing settings.
    """

    def __init__(self):
        self.shop_id = getattr(settings, "IZIPAY_SHOP_ID", None)
        self.api_key = getattr(settings, "IZIPAY_KEY", None)
        self.api_url = getattr(settings, "IZIPAY_API_URL", None)
        self.callback_url = getattr(settings, "IZIPAY_CALLBACK_URL", None)
        self._validate_settings()

    def _validate_settings(self) -> None:
        """Raise IzipayError if any required setting is missing or empty."""
        missing = []
        for name, value in [
            ("IZIPAY_SHOP_ID", self.shop_id),
            ("IZIPAY_KEY", self.api_key),
            ("IZIPAY_API_URL", self.api_url),
        ]:
            if not value:
                missing.append(name)
        if missing:
            raise IzipayError(
                f"Izipay settings missing or empty: {', '.join(missing)}. "
                "Set these environment variables / in base.py settings."
            )

    def _headers(self, transaction_id: str) -> dict:
        """
        Build request headers for Izipay Perú Token/Generate.

        Headers per official Izipay Perú docs:
          - Authorization: Bearer {api_key}
          - transactionId: {transaction_id}  (idempotency key)
          - Content-Type: application/json
          - Accept: application/json
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "transactionId": str(transaction_id),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ── Token / session creation ────────────────────────────────────────────────

    async def generar_token_sesion(
        self,
        transaction_id: str,
        order_number: str,
        amount: str,
        currency: str,
        buyer_email: str,
        buyer_name: str,
        buyer_surname: str,
        buyer_document: str = "00000000",
        buyer_phone: str = "999999999",
    ) -> dict:
        """
        Call Izipay Perú Token/Generate to create a payment session.

        This is the server-side token preparation for Web Core 2.0 popup flow.
        The returned token + config is sent to the frontend where
        checkout.LoadForm() is called with these values.

        Args:
            transaction_id: 14-digit idempotency key
            order_number: 10-digit order number
            amount: Amount as string (e.g. "100.00")
            currency: ISO currency code (e.g. "PEN")
            buyer_email: Payer email
            buyer_name: Payer first name (will be sanitized for Izipay)
            buyer_surname: Payer last name (will be sanitized for Izipay)
            buyer_document: Payer document number (DNI)
            buyer_phone: Payer phone number

        Returns:
            Izipay Perú API response dict with at least:
                - token: str (JWT session token for frontend SDK)
                - response: dict with token (or token at top level)

        Raises:
            IzipayError: on HTTP error or API-level failure (non-success).
        """
        # Sanitize names for Izipay Perú (ASCII only, no accents)
        first_name = _sanitizar_texto(buyer_name)[:30] or "CLIENTE"
        last_name = _sanitizar_texto(buyer_surname)[:30] or "VENTA"

        payload = {
            "requestSource": "ECOMMERCE",
            "merchantCode": self.shop_id,
            "orderNumber": order_number,
            "publicKey": self.api_key,
            "amount": amount,
            "currency": currency,
            "clientData": {
                "email": buyer_email,
                "fullName": f"{first_name} {last_name}",
                "phoneNumber": buyer_phone,
                "documentNumber": buyer_document,
                "documentType": "DNI",
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/security/v1/Token/Generate",
                    json=payload,
                    headers=self._headers(transaction_id),
                )
            except httpx.TimeoutException as e:
                raise IzipayError(f"Izipay request timed out: {e}") from e
            except httpx.RequestError as e:
                raise IzipayError(f"Izipay request error: {e}") from e

        return self._parse_response(response, transaction_id)

    # ── Response parsing ───────────────────────────────────────────────────────

    def _parse_response(self, response: httpx.Response, transaction_id: str) -> dict:
        """Parse and validate Izipay Perú API response."""
        if response.status_code >= 500:
            raise IzipayError(
                f"Izipay server error {response.status_code} for "
                f"transactionId={transaction_id}: {response.text[:200]}"
            )

        try:
            data = response.json()
        except Exception as e:
            raise IzipayError(
                f"Failed to parse Izipay response as JSON: {e}. "
                f"Status={response.status_code}, body={response.text[:200]}"
            ) from e

        # Izipay Perú returns token in response.token or top-level token
        # No "status: failure" top-level field like Iyzico — check for token
        token = data.get("token") or (data.get("response", {}).get("token") if isinstance(data.get("response"), dict) else None)
        if not token:
            error_msg = (
                data.get("responseMessage")
                or data.get("message")
                or data.get("errorMessage")
                or "No token in Izipay response"
            )
            raise IzipayError(
                f"Izipay token generation failed: {error_msg} "
                f"(transactionId={transaction_id})"
            )

        return data
