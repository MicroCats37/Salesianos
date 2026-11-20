"""`VerificacionPagoService` — helpers puros para las confirmaciones.

Contract: `contract/django-app-architecture-contract.md` §4.3

Es **sync** y **sin ORM**: sólo razona sobre el payload que entregó el
proveedor y sobre los valores ya cargados por el flujo.

La correlación NO es un control antifalsificación: comprueba que el payload
describa la orden que ABIERMOS. Lo que prueba que el proveedor realmente lo
envió es la **firma**, verificada en servidor.

Regla de dinero (FR-04 §3): el monto y la moneda de la confirmación deben
coincidir **exactamente** con el snapshot congelado de la orden. Un importe
distinto no se "redondea" ni se "tolera": se rechaza con `MONTO_NO_COINCIDE` y
no se muta ninguna fila.
"""

import re
from decimal import Decimal, InvalidOperation

from modules.pagos.domain.exceptions import (
    MontoNoCoincideError,
    PagoDatosInconsistentesError,
)


class VerificacionPagoService:
    """Extrae y contrasta los valores del proveedor de una confirmación."""

    # ── Extracción ───────────────────────────────────────────────────────────

    def extraer_transaction_id(self, payload: dict) -> str | None:
        """Identificador del intento que entrega el proveedor."""
        for valor in self._candidatos(payload, "transactionId"):
            texto = self._a_texto(valor)
            if texto:
                return texto
        return None

    def extraer_order_number(self, payload: dict) -> str | None:
        """Referencia de orden que entrega el proveedor."""
        for valor in self._candidatos(payload, "orderNumber"):
            texto = self._a_texto(valor)
            if texto:
                return texto
        return None

    def extraer_amount(self, payload: dict) -> Decimal | None:
        """Monto que entrega el proveedor."""
        for valor in self._candidatos(payload, "amount"):
            monto = self._a_decimal(valor)
            if monto is not None:
                return monto
        return None

    def extraer_currency(self, payload: dict) -> str | None:
        """Moneda que entrega el proveedor."""
        for valor in self._candidatos(payload, "currency"):
            texto = self._a_texto(valor)
            if texto:
                return texto.upper()
        return None

    def extraer_codigo(self, payload: dict) -> str:
        """Código de respuesta del proveedor."""
        if not isinstance(payload, dict):
            return ""
        codigo = payload.get("code")
        if codigo is None:
            return ""
        return str(codigo)

    # ── Correlación ─────────────────────────────────────────────────────────

    def validar_monto(self, payload: dict, orden) -> None:
        """Comprueba el monto y la moneda contra la orden.

        Args:
            payload: el payload del proveedor.
            orden: la `OrdenPago` ya cargada.

        Raises:
            MontoNoCoincideError: si el monto o la moneda no coinciden
                exactamente con el snapshot congelado de la orden.
        """
        monto = self.extraer_amount(payload)
        if monto is not None and monto != orden.monto:
            raise MontoNoCoincideError()

        moneda = self.extraer_currency(payload)
        if moneda is not None and moneda != (orden.moneda or "").upper():
            raise MontoNoCoincideError()

    def validar_correlacion(self, payload: dict, orden, intento) -> None:
        """Comprueba que el payload describa la orden que se abrió.

        El proveedor puede devolver la orden con cualquiera de los dos
        identificadores que conoce: la referencia visible de la orden o la
        referencia técnica del intento. Cualquier otro valor es una
        contradicción.

        Args:
            payload: el payload del proveedor.
            orden: la `OrdenPago` ya cargada.
            intento: el `TransaccionPago` ya cargado.

        Raises:
            PagoDatosInconsistentesError: si la referencia no corresponde.
        """
        order_number = self.extraer_order_number(payload)
        if not order_number:
            return

        conocidas = {
            str(orden.referencia or ""),
            str(getattr(intento, "referencia_proveedor", "") or ""),
            str(getattr(intento, "referencia_proveedor", "") or "")[:10],
        }
        conocidas.discard("")
        if order_number not in conocidas:
            raise PagoDatosInconsistentesError()

    # ── Internos ─────────────────────────────────────────────────────────────

    def _candidatos(self, payload: dict, clave: str):
        """Todos los lugares donde el proveedor puede llevar un valor.

        El payload del proveedor expone la misma información en el nivel
        superior y dentro de `response` / `response.order[]`. Se inspeccionan
        todos.
        """
        if not isinstance(payload, dict):
            return

        valor = payload.get(clave)
        if valor is not None:
            yield valor

        respuesta = payload.get("response")
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

    def _a_texto(self, valor) -> str:
        """Normaliza un valor del proveedor a texto no vacío."""
        if valor is None or isinstance(valor, (dict, list, bool)):
            return ""
        texto = str(valor).strip()
        return texto

    def _a_decimal(self, valor) -> Decimal | None:
        """Convierte un monto del proveedor a `Decimal`, tolerando su formato."""
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
            # El último separador es el decimal.
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


__all__ = ["VerificacionPagoService"]
