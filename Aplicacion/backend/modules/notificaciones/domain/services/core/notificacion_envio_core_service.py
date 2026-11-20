"""`NotificacionEnvioCoreService` — la trazabilidad del intento.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

Escribe y lee el registro `NotificacionEnvio`. No envía nada: el envío es
responsabilidad del **proveedor**, que es un puerto sin implementación hasta
que `PD-08` se ratifique.

La escritura es **idempotente por `(orden_pago_id, tipo)`**: la restricción
única de la base de datos es la guarda real. Un webhook duplicado o una
llegada tardía actualizan el mismo registro y **no** crean un segundo.
"""

import logging

from django.db import IntegrityError
from django.utils import timezone

from modules.notificaciones.domain.constants import (
    CLAVES_INCIDENCIA_PERMITIDAS,
    EstadoNotificacion,
    TipoNotificacion,
)
from modules.notificaciones.models import NotificacionEnvio

logger = logging.getLogger(__name__)


class NotificacionEnvioCoreService:
    """Operaciones de persistencia del registro de notificación."""

    def obtener(self, orden_pago_id, tipo: str) -> NotificacionEnvio | None:
        """El registro de la notificación de una orden, si existe."""
        if not orden_pago_id:
            return None
        return NotificacionEnvio.objects.filter(
            orden_pago_id=orden_pago_id,
            tipo=tipo,
        ).first()

    def registrar_intento(
        self,
        *,
        orden_pago_id,
        persona_id=None,
        tipo: str = TipoNotificacion.COMPRA_CONFIRMADA,
        estado: str = EstadoNotificacion.OMITIDA,
        codigo: str = "",
    ) -> NotificacionEnvio:
        """Registra (o actualiza) el intento de notificación de una orden.

        Idempotente: si el registro ya existe, se **actualiza** (con el
        contador de intentos) en vez de crear otro. La carrera la resuelve la
        restricción única de la base de datos.
        """
        registro = self.obtener(orden_pago_id, tipo)
        if registro is not None:
            registro.intentos = (registro.intentos or 0) + 1
            registro.estado = estado
            registro.codigo = codigo or ""
            registro.incidencia = self.incidencia(codigo, registro.intentos)
            if persona_id:
                registro.persona_id = persona_id
            if estado == EstadoNotificacion.ENVIADA:
                registro.enviada_en = timezone.now()
            registro.save(
                update_fields=[
                    "persona_id",
                    "estado",
                    "codigo",
                    "intentos",
                    "incidencia",
                    "enviada_en",
                    "updated_at",
                ]
            )
            return registro

        try:
            return NotificacionEnvio.objects.create(
                orden_pago_id=orden_pago_id,
                persona_id=persona_id,
                tipo=tipo,
                estado=estado,
                codigo=codigo or "",
                intentos=1,
                incidencia=self.incidencia(codigo, 1),
                enviada_en=(
                    timezone.now() if estado == EstadoNotificacion.ENVIADA else None
                ),
            )
        except IntegrityError:
            # Otra vuelta ganó la carrera: la guarda real es la restricción
            # única, no esta comprobación.
            existente = self.obtener(orden_pago_id, tipo)
            if existente is None:  # pragma: no cover - defensa
                raise
            return existente

    def incidencia(self, codigo: str, intento: int) -> dict:
        """La incidencia persistida: SÓLO datos seguros.

        Nunca el texto de una excepción, ni un payload de proveedor, ni un
        identificador interno, ni un secreto (FR-04 §4).
        """
        if not codigo:
            return {}
        datos = {
            "codigo": codigo,
            "intento": int(intento or 0),
            "fecha": timezone.now().isoformat(),
        }
        return {clave: datos[clave] for clave in CLAVES_INCIDENCIA_PERMITIDAS}


__all__ = ["NotificacionEnvioCoreService"]
