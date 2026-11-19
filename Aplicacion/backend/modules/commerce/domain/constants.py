"""Vocabulario cerrado del módulo `commerce`.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Dos vocabularios cerrados:

1. `OrigenCompra` — el dominio de origen de la compra. **Tres** orígenes, uno
   por dominio (`DEC-11`, `RN-C01`). No existe "compra genérica sin origen":
   el dominio de origen decide cómo se habilita el derecho.
2. `EstadoCompra` — el estado comercial de la compra. Es un hecho DISTINTO
   del estado de la orden de pago y del estado del intento (FR-04 §1.3).

Este archivo NO declara reglas de negocio ni expresiones de dinero: el módulo
`pagos` es dueño del veredicto operativo y este módulo es dueño del hecho
comercial.
"""

from django.db import models


class OrigenCompra(models.TextChoices):
    """Dominio de origen de la compra.

    La lista es CERRADA y no se renumera: `INSCRIPCION`, `PASE` y
    `MARKETPLACE`. Un origen desconocido es un error de configuración, no un
    dominio nuevo silencioso (`DEC-10`).
    """

    INSCRIPCION = "INSCRIPCION", "Inscripción"
    PASE = "PASE", "Pase"
    MARKETPLACE = "MARKETPLACE", "Marketplace"


class EstadoCompra(models.TextChoices):
    """Estado comercial de la compra.

    `PENDIENTE` · `PAGADA` · `CANCELADA`. Es el hecho COMERCIAL: no habilita
    derechos por sí solo (RN-C08, FR-04 §4).
    """

    PENDIENTE = "PENDIENTE", "Pendiente"
    PAGADA = "PAGADA", "Pagada"
    CANCELADA = "CANCELADA", "Cancelada"


class EstadoActivacionCompra(models.TextChoices):
    """Estado de la activación de derechos de una compra.

    Es un hecho DISTINTO del estado comercial de la compra, del estado de la
    orden y del estado del intento (FR-04 §1.3, I-2):

    - `PENDIENTE` — la activación todavía no se ha completado. Puede estar
      esperando a que el dominio de origen registre su activador, o puede
      haber sido abandonada a mitad de camino (un `intento` reservado).
    - `ACTIVADA` — el derecho quedó habilitado. Es TERMINAL: una segunda
      activación de la misma compra no vuelve a invocar al dominio.
    - `FALLIDA` — el intento falló. Es **recuperable**: el pago confirmado se
      conserva y la activación se puede reintentar (RN-C08).
    """

    PENDIENTE = "PENDIENTE", "Pendiente"
    ACTIVADA = "ACTIVADA", "Activada"
    FALLIDA = "FALLIDA", "Fallida"


#: Longitud máxima de la referencia de intención de una compra.
MAX_LEN_REFERENCIA_COMPRA = 200

#: Longitud máxima de la clave de activación de derechos.
MAX_LEN_CLAVE_ACTIVACION = 128

#: Segundos que un intento de activación puede retener el "lease" antes de
#: considerarse ABANDONADO y, por tanto, reclamable por otro reintento.
#:
#: Es la red de seguridad del caso "el proceso murió con el intento
#: reservado": sin este plazo, un fallo de proceso dejaría la activación
#: bloqueada para siempre.
LEGA_ACTIVACION_SEGUNDOS = 300

#: Claves del detalle del dominio que el coordinador conserva. Es una lista
#: **CERRADA**: nada más del resultado del dominio se persiste.
CLAVES_DETALLE_PERMITIDAS = ("cantidad", "codigo", "estado")


__all__ = [
    "CLAVES_DETALLE_PERMITIDAS",
    "LEGA_ACTIVACION_SEGUNDOS",
    "MAX_LEN_CLAVE_ACTIVACION",
    "MAX_LEN_REFERENCIA_COMPRA",
    "EstadoActivacionCompra",
    "EstadoCompra",
    "OrigenCompra",
]
