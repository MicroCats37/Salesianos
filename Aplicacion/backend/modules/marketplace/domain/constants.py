"""Vocabulario cerrado del módulo `marketplace`.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md` ·
          `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`

Dos vocabularios cerrados:

1. `EstadoProducto` — el estado comercial de un producto del catálogo. La lista
   es CERRADA: `ACTIVO`, `INACTIVO`. El catálogo público sólo expone productos
   `ACTIVO`; el resto es catálogo de administración.
2. `DOMINIO_MEDIA` — el primer segmento de la ruta de almacenamiento de los
   archivos del marketplace: `MEDIA_ROOT/productos/<entidad_id>/<uuid><ext>`
   (FR-06 §2.2). El valor está autorizado en `settings.MEDIA_DOMAINS`.

Este archivo NO declara ninguna constante de "edición activa": el alcance se
resuelve con el ORDEN ÚNICO de FR-02 §2.2, que vive en el módulo `eventos`.
"""

from django.db import models


class EstadoProducto(models.TextChoices):
    """Estado comercial de un producto del catálogo (RN-M02)."""

    ACTIVO = "ACTIVO", "Activo"
    INACTIVO = "INACTIVO", "Inactivo"


class EstadoPedido(models.TextChoices):
    """Estado del PEDIDO de marketplace: su propio ciclo de vida.

    Es un HECHO DISTINTO del pago y de la entrega (RN-M07, RN-C08): un pedido
    `PAGADO` NO es un pedido `ENTREGADO`, y el pago confirmado NO habilita
    ninguna entrega por sí solo.

    - `PENDIENTE` — el pedido existe y su compra sigue pendiente.
    - `PAGADO` — la compra que lo financia quedó confirmada. La entrega sigue
      en `PENDIENTE`: pagada y entregada son hechos separados.
    - `CANCELADO` — la compra que lo financia quedó cancelada.
    """

    PENDIENTE = "PENDIENTE", "Pendiente"
    PAGADO = "PAGADO", "Pagado"
    CANCELADO = "CANCELADO", "Cancelado"


class EstadoPagoPedido(models.TextChoices):
    """Estado del PAGO de un pedido, proyectado desde la compra.

    Es el hecho comercial de `commerce`, traducido al vocabulario del módulo
    para que el presenter nunca exponga la terminología de otro dominio. NO es
    el estado del pedido ni el de la entrega: son TRES hechos distintos.

    - `PENDIENTE` — la compra sigue pendiente de pago.
    - `CONFIRMADO` — la compra quedó pagada (RN-C08: cobro confirmado).
    - `NO_COMPLETADO` — la compra quedó cancelada (RN-C07: "pago no
      completado").
    """

    PENDIENTE = "PENDIENTE", "Pendiente"
    CONFIRMADO = "CONFIRMADO", "Confirmado"
    NO_COMPLETADO = "NO_COMPLETADO", "No completado"


class EstadoEntregaPedido(models.TextChoices):
    """Estado de la ENTREGA de un pedido.

    Es el hecho de la entrega física, y lo avanza `DOM-06` (inventario y
    entrega). `DOM-05` NUNCA lo cambia: el pago no habilita la entrega
    (RN-M07, `QA-M04`).

    - `PENDIENTE` — todavía no entregado.
    - `ENTREGADO` — entregado y registrado por un operador.
    """

    PENDIENTE = "PENDIENTE", "Pendiente"
    ENTREGADO = "ENTREGADO", "Entregado"


class TipoItemPedido(models.TextChoices):
    """Tipo de concepto que una línea de pedido puede declarar.

    El pedido de marketplace SÓLO admite `PRODUCTO` (RN-C01: no existe un
    carrito combinado). `PASE` e `INSCRIPCION` existen para que un cliente
    pueda expresar el error y recibir un rechazo explícito en vez de un
    pedido con conceptos de otro dominio.
    """

    PRODUCTO = "PRODUCTO", "Producto"
    PASE = "PASE", "Pase"
    INSCRIPCION = "INSCRIPCION", "Inscripción"


class AccionPedido(models.TextChoices):
    """Siguiente acción SEGURA que el comprador puede realizar.

    Son verbos del dominio, no operaciones del proveedor: el presenter nunca
    expone una referencia técnica, un intento ni una evidencia de pago
    (FR-01 §4).
    """

    REALIZAR_PAGO = "REALIZAR_PAGO", "Realizar el pago"
    ESPERAR_ENTREGA = "ESPERAR_ENTREGA", "Esperar la entrega"
    REINTENTAR_COMPRA = "REINTENTAR_COMPRA", "Reintentar la compra"
    VER_TICKET = "VER_TICKET", "Ver el ticket"


#: Primer segmento autorizado de la ruta de media del marketplace (FR-06 §2.2).
DOMINIO_MEDIA = "productos"

#: Clave del módulo lógico que habilita la tienda en una edición (FR-02 §2.5).
MODULO_LOGICO = "marketplace"

#: Moneda por defecto del pedido (ISO-4217). El precio del catálogo no trae
#: moneda: la del evento es la del mercado (`PEN`).
MONEDA_PEDIDO = "PEN"

#: Cantidad máxima de unidades de un mismo producto en un pedido.
MAX_CANTIDAD_ITEM_PEDIDO = 99

#: Bytes de entropía del token privado del pedido (enlace de seguimiento).
BYTES_TOKEN_PEDIDO = 32


__all__ = [
    "BYTES_TOKEN_PEDIDO",
    "DOMINIO_MEDIA",
    "MAX_CANTIDAD_ITEM_PEDIDO",
    "MODULO_LOGICO",
    "MONEDA_PEDIDO",
    "AccionPedido",
    "EstadoEntregaPedido",
    "EstadoPagoPedido",
    "EstadoPedido",
    "EstadoProducto",
    "TipoItemPedido",
]
