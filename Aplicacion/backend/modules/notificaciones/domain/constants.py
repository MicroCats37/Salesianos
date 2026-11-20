"""Vocabulario cerrado del módulo `notificaciones`.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3, §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

Este módulo **no decide** el proveedor de correo, ni las plantillas, ni los
límites, ni los reintentos, ni la entrega: eso es `PD-08`, que sigue **ABIERTO**
y diferido por `DEC-21`. Lo que sí fija es:

1. La **trazabilidad** del intento de notificación: cada intento deja un
   registro auditable con un código de máquina.
2. La **independencia** del fallo: una notificación fallida NUNCA revierte una
   compra ni un derecho (RN-C08, FR-04 §4).
3. El **código** `PROVEEDOR_NO_APROBADO`: mientras `PD-08` no se ratifique, no
   hay proveedor y el envío se OMITE de forma explícita. No hay un
   "fallback silencioso" ni un envío accidental.
"""

from django.db import models


class TipoNotificacion(models.TextChoices):
    """Qué se notifica.

    La lista es CERRADA: cada tipo es un hecho de negocio que ya existe. La
    notificación no crea hechos nuevos, los cuenta.
    """

    COMPRA_CONFIRMADA = "COMPRA_CONFIRMADA", "Compra confirmada"


class EstadoNotificacion(models.TextChoices):
    """El estado del intento de notificación.

    - `OMITIDA` — no se intentó enviar: no hay proveedor aprobado (`PD-08`).
    - `PENDIENTE` — se registró el intento y hay uno reservado.
    - `ENVIADA` — el proveedor aceptó el envío.
    - `FALLIDA` — se intentó y falló. Es **recuperable**: el pago confirmado
      se conserva (RN-C08).
    """

    OMITIDA = "OMITIDA", "Omitida"
    PENDIENTE = "PENDIENTE", "Pendiente"
    ENVIADA = "ENVIADA", "Enviada"
    FALLIDA = "FALLIDA", "Fallida"


#: El proveedor de correo no está aprobado (`PD-08` abierto, `DEC-21`).
CODIGO_PROVEEDOR_NO_APROBADO = "PROVEEDOR_NO_APROBADO"

#: La notificación se omitió porque no hay proveedor configurado.
CODIGO_SIN_PROVEEDOR = "SIN_PROVEEDOR"

#: La notificación se envió.
CODIGO_ENVIADA = "NOTIFICACION_ENVIADA"

#: El proveedor falló al enviar. El pago confirmado se conserva.
CODIGO_ENVIO_FALLIDO = "ENVIO_FALLIDO"

#: Longitud máxima del código de máquina de un intento.
MAX_LEN_CODIGO_NOTIFICACION = 64

#: Claves del detalle de un intento que se conservan. Es una lista **CERRADA**:
#: nada más del resultado del proveedor se persiste. El texto de una
#: excepción NUNCA se guarda ni se devuelve.
CLAVES_INCIDENCIA_PERMITIDAS = ("codigo", "intento", "fecha")


__all__ = [
    "CLAVES_INCIDENCIA_PERMITIDAS",
    "CODIGO_ENVIO_FALLIDO",
    "CODIGO_ENVIADA",
    "CODIGO_PROVEEDOR_NO_APROBADO",
    "CODIGO_SIN_PROVEEDOR",
    "MAX_LEN_CODIGO_NOTIFICACION",
    "EstadoNotificacion",
    "TipoNotificacion",
]
