"""Cliente de sesión Izipay para el checkout público del marketplace."""

from decimal import Decimal
import logging

import httpx
from django.conf import settings
from ninja.errors import HttpError

logger = logging.getLogger(__name__)


class IzipaySessionService:
    """Abre una sesión del proveedor sin exponer credenciales al navegador."""

    @property
    def shop_id(self) -> str:
        return getattr(settings, "IZIPAY_SHOP_ID", "") or ""

    async def abrir(
        self,
        *,
        transaction_id: str,
        order_number: str,
        amount: Decimal,
        currency: str,
        buyer_email: str,
        buyer_name: str,
        buyer_surname: str,
    ) -> str:
        shop_id = self.shop_id
        key = getattr(settings, "IZIPAY_KEY", "")
        api_url = getattr(settings, "IZIPAY_API_URL", "").rstrip("/")

        if not shop_id or not key or not api_url:
            logger.error("Izipay session is missing required configuration.")
            raise HttpError(503, "Izipay session could not be started.")

        payload = {
            "requestSource": "ECOMMERCE",
            "merchantCode": shop_id,
            "orderNumber": order_number,
            "publicKey": key,
            "amount": f"{amount:.2f}",
            "currency": currency,
            "clientData": {
                "email": buyer_email,
                "fullName": f"{buyer_name or 'CLIENTE'} {buyer_surname or 'VENTA'}",
                "phoneNumber": "999999999",
                "documentNumber": "00000000",
                "documentType": "DNI",
            },
        }
        headers = {
            "Authorization": f"Bearer {key}",
            "transactionId": transaction_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{api_url}/security/v1/Token/Generate",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                body = response.json()
        except httpx.HTTPStatusError as exc:
            try:
                provider_error = exc.response.json()
            except ValueError:
                provider_error = {}
            logger.warning(
                "Izipay session request was rejected with status %s (code=%s, message=%s).",
                exc.response.status_code,
                provider_error.get("code") or provider_error.get("errorCode"),
                provider_error.get("message") or provider_error.get("errorMessage"),
            )
            raise HttpError(503, "Izipay session could not be started.") from None
        except (httpx.RequestError, ValueError):
            logger.warning("Izipay session request failed before a valid response.")
            raise HttpError(503, "Izipay session could not be started.") from None

        token = body.get("token")
        if not token and isinstance(body.get("response"), dict):
            token = body["response"].get("token")
        if not isinstance(token, str) or not token:
            logger.warning("Izipay session response did not include a token.")
            raise HttpError(503, "Izipay session could not be started.")
        return token


__all__ = ["IzipaySessionService"]
