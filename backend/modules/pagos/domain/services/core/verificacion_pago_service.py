"""
VerificacionPagoService — pure validation helpers for provider confirmations.

Sync and ORM-free: it only reasons about the payload the provider delivered
and about the values already loaded by the flow.

The correlation is a consistency check, NOT an anti-forgery control: it makes
sure the payload the provider sent describes the order we opened. Only the
provider signature proves that the provider actually sent it.
"""
import re
from decimal import Decimal, InvalidOperation

from modules.pagos.domain.exceptions import PagoDatosInconsistentesError


class VerificacionPagoService:
    """Extracts and cross-checks the provider values of a confirmation."""

    # ── Extraction ─────────────────────────────────────────────────────────────

    def extraer_amount(self, kr_answer: dict) -> Decimal | None:
        """Return the amount carried by the payload, if it carries one."""
        for valor in self._candidatos(kr_answer, "amount"):
            monto = self._a_decimal(valor)
            if monto is not None:
                return monto
        return None

    def extraer_order_number(self, kr_answer: dict) -> str | None:
        """Return the provider order number carried by the payload, if any."""
        for valor in self._candidatos(kr_answer, "orderNumber"):
            if isinstance(valor, (dict, list)) or valor is None:
                continue
            texto = str(valor).strip()
            if texto:
                return texto
        return None

    def extraer_transaction_id(self, kr_answer: dict) -> str | None:
        """Return the provider transaction id carried by the payload, if any."""
        for valor in self._candidatos(kr_answer, "transactionId"):
            if isinstance(valor, (dict, list)) or valor is None:
                continue
            texto = str(valor).strip()
            if texto:
                return texto
        return None

    # ── Correlation ────────────────────────────────────────────────────────────

    def validar_correlacion(self, kr_answer: dict, transaccion) -> None:
        """
        Cross-check the provider payload against the persisted transaction.

        Every value the provider DID deliver must match what was recorded
        when the checkout was opened. A payload that contradicts the stored
        order is rejected before any state changes.

        Args:
            kr_answer: The provider payload.
            transaccion: The persisted TransaccionPago.

        Raises:
            PagoDatosInconsistentesError: on any contradiction.
        """
        amount = self.extraer_amount(kr_answer)
        if amount is not None and amount != transaccion.amount:
            raise PagoDatosInconsistentesError()

        order_number = self.extraer_order_number(kr_answer)
        if order_number and order_number != transaccion.order_number:
            raise PagoDatosInconsistentesError()

    # ── Internals ──────────────────────────────────────────────────────────────

    def _candidatos(self, kr_answer: dict, clave: str):
        """
        Yield the places where the provider may carry a value.

        The Izipay Perú payload exposes the same information at the top level
        and inside `response` / `response.order[]`. All of them are inspected.
        """
        if not isinstance(kr_answer, dict):
            return

        valor = kr_answer.get(clave)
        if valor is not None:
            yield valor

        respuesta = kr_answer.get("response")
        if not isinstance(respuesta, dict):
            return

        valor = respuesta.get(clave)
        if valor is not None:
            yield valor

        ordenes = respuesta.get("order")
        if isinstance(ordenes, list):
            for orden in ordenes:
                if isinstance(orden, dict):
                    valor = orden.get(clave)
                    if valor is not None:
                        yield valor

    def _a_decimal(self, valor) -> Decimal | None:
        """Convert a provider amount into a Decimal, tolerating its format."""
        if valor is None or isinstance(valor, bool):
            return None

        if isinstance(valor, (int, float, Decimal)):
            try:
                return Decimal(str(valor))
            except InvalidOperation:
                return None

        texto = re.sub(r"[^0-9,.\-]", "", str(valor).strip())
        if not texto:
            return None

        if "," in texto and "." in texto:
            # The last separator is the decimal one.
            if texto.rfind(",") > texto.rfind("."):
                texto = texto.replace(".", "").replace(",", ".")
            else:
                texto = texto.replace(",", "")
        elif "," in texto:
            texto = texto.replace(",", ".")

        try:
            return Decimal(texto)
        except InvalidOperation:
            return None
