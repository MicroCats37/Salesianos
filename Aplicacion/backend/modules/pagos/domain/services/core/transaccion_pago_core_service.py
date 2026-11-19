"""`TransaccionPagoCoreService` — operaciones sync sobre los intentos de pago.

Contract: `contract/django-app-architecture-contract.md` §4.3

- Es **sync**.
- Opera directamente sobre el ORM.
- **NO** abre `transaction.atomic()`: la atomicidad la aporta el flujo.

Reglas que este servicio respeta:

- Un intento `PENDIENTE` es un **intento**, no un cobro. Al reabrir el
  checkout se crea un intento nuevo y el anterior se cierra: la traza de
  auditoría de la orden **nunca** se borra ni se reescribe (RN-C04).
- `crear_intento` calcula el ordinal a partir del historial existente, de modo
  que el ordinal es creciente por orden y único.
- La **identidad** del intento se construye con tres partes: el alcance (un
  resumen estable de la orden), la posición (el ordinal) y un nonce aleatorio.
  Dos intentos de la misma orden nunca comparten identidad; dos órdenes
  distintas sólo colisionan por azar.
"""

import hashlib
import secrets

from django.utils import timezone

from modules.pagos.domain.constants import EstadoTransaccionPago
from modules.pagos.domain.models import TransaccionPago

#: Dígitos del alcance (resumen estable de la orden).
DIGITOS_ALCANCE = 6
#: Dígitos de la posición del intento dentro de su orden.
DIGITOS_ORDINAL = 4
#: Dígitos del nonce aleatorio.
DIGITOS_NONCE = 4


class TransaccionPagoCoreService:
    """Operaciones de bajo nivel sobre `TransaccionPago`."""

    def contar_intentos(self, orden_pago_id) -> int:
        """Cuántos intentos tiene la orden.

        Los intentos nunca se borran: son la traza de auditoría, así que el
        conteo es la posición del siguiente intento.
        """
        return TransaccionPago.objects.filter(orden_pago_id=orden_pago_id).count()

    def generar_referencia_proveedor(
        self, orden_pago_id, ordinal: int | None = None
    ) -> str:
        """Genera la identidad técnica del intento.

        Formato: `<alcance 6><ordinal 4><nonce 4>` = 14 dígitos, la misma
        forma que el proveedor ya recibía.

        Args:
            orden_pago_id: UUID de la orden.
            ordinal: posición del intento. Sin él se usa el instante actual.

        Returns:
            La referencia del intento.
        """
        return (
            self._alcance(orden_pago_id)
            + self._ordinal(ordinal)
            + self._nonce(DIGITOS_NONCE)
        )

    def crear_intento(
        self,
        *,
        orden_pago,
        referencia_proveedor: str,
        metadata: dict | None = None,
    ) -> TransaccionPago:
        """Crea el siguiente intento `PENDIENTE` de una orden.

        El ordinal es creciente por orden y único: la base de datos lo
        garantiza con la restricción `transaccion_intento_unico_por_orden`.
        """
        ordinal = self.contar_intentos(orden_pago.id) + 1
        return TransaccionPago.objects.create(
            orden_pago=orden_pago,
            intento=ordinal,
            referencia_proveedor=referencia_proveedor,
            estado=EstadoTransaccionPago.PENDIENTE,
            verificada=False,
            evidencia={},
            codigo_respuesta="",
            mensaje_respuesta="",
            metodo_pago="",
            metadata=metadata or {},
        )

    def obtener_por_referencia_proveedor(
        self, referencia_proveedor: str
    ) -> TransaccionPago | None:
        """El intento por su referencia técnica."""
        if not referencia_proveedor:
            return None
        return (
            TransaccionPago.objects.filter(referencia_proveedor=referencia_proveedor)
            .select_related("orden_pago")
            .first()
        )

    def cerrar_intentos_vivos(self, orden_pago_id) -> int:
        """Cierra todos los intentos `PENDIENTE` de la orden.

        Se usa al reabrir el checkout: el intento anterior se retira y el
        nuevo es el único vivo. Los intentos cerrados se conservan.

        Returns:
            Cuántos intentos se cerraron.
        """
        return TransaccionPago.objects.filter(
            orden_pago_id=orden_pago_id,
            estado=EstadoTransaccionPago.PENDIENTE,
        ).update(
            estado=EstadoTransaccionPago.CANCELADO,
            updated_at=timezone.now(),
        )

    def marcar_exito(
        self,
        intento: TransaccionPago,
        *,
        codigo_respuesta: str = "",
        mensaje_respuesta: str = "",
        metodo_pago: str = "",
        evidencia: dict | None = None,
        metadata: dict | None = None,
        verificada: bool = False,
    ) -> TransaccionPago:
        """Cierra el intento como `EXITO` y guarda su evidencia.

        Idempotente: un intento ya `EXITO` no se reescribe, de modo que una
        notificación tardía no destruye la evidencia original.
        """
        if intento.estado == EstadoTransaccionPago.EXITO:
            return intento
        intento.estado = EstadoTransaccionPago.EXITO
        intento.codigo_respuesta = codigo_respuesta or ""
        intento.mensaje_respuesta = (mensaje_respuesta or "")[:255]
        intento.metodo_pago = metodo_pago or ""
        intento.evidencia = evidencia or {}
        intento.metadata = metadata if metadata is not None else intento.metadata
        intento.verificada = verificada
        intento.save(
            update_fields=[
                "estado",
                "codigo_respuesta",
                "mensaje_respuesta",
                "metodo_pago",
                "evidencia",
                "metadata",
                "verificada",
                "updated_at",
            ]
        )
        return intento

    def marcar_fallido(
        self,
        intento: TransaccionPago,
        *,
        codigo_respuesta: str = "",
        mensaje_respuesta: str = "",
        verificada: bool = False,
    ) -> TransaccionPago:
        """Cierra el intento como `FALLIDO`."""
        if intento.estado == EstadoTransaccionPago.EXITO:
            return intento
        intento.estado = EstadoTransaccionPago.FALLIDO
        intento.codigo_respuesta = codigo_respuesta or ""
        intento.mensaje_respuesta = (mensaje_respuesta or "")[:255]
        intento.verificada = verificada
        intento.save(
            update_fields=[
                "estado",
                "codigo_respuesta",
                "mensaje_respuesta",
                "verificada",
                "updated_at",
            ]
        )
        return intento

    def marcar_cancelado(self, intento: TransaccionPago) -> TransaccionPago:
        """Cierra el intento como `CANCELADO` (intento retirado)."""
        if intento.estado == EstadoTransaccionPago.EXITO:
            return intento
        intento.estado = EstadoTransaccionPago.CANCELADO
        intento.save(update_fields=["estado", "updated_at"])
        return intento

    # ── Internos ─────────────────────────────────────────────────────────────

    def _alcance(self, orden_pago_id) -> str:
        """Resumen estable de la orden: el mismo en todos los procesos."""
        if not orden_pago_id:
            return self._nonce(DIGITOS_ALCANCE)
        resumen = hashlib.sha256(str(orden_pago_id).encode("utf-8")).hexdigest()
        return f"{int(resumen[:12], 16) % (10 ** DIGITOS_ALCANCE):0{DIGITOS_ALCANCE}d}"

    def _ordinal(self, ordinal: int | None) -> str:
        """Posición del intento dentro de su orden."""
        if ordinal is None:
            ordinal = int(timezone.now().timestamp() * 1000) % (10 ** DIGITOS_ORDINAL)
        return f"{ordinal % (10 ** DIGITOS_ORDINAL):0{DIGITOS_ORDINAL}d}"

    def _nonce(self, digitos: int) -> str:
        """Parte aleatoria: la que hace la identidad única."""
        return "".join(secrets.choice("0123456789") for _ in range(digitos))


__all__ = ["TransaccionPagoCoreService"]
