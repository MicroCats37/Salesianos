"""Las reglas del pedido de marketplace (`DOM-05`).

Freeze: `FREEZE-CM-1.0.0` · `FREEZE-MD-1.0.0` · `FREEZE-PS-1.0.0`
Plan: `RN-C01` · `RN-C02` · `RN-C03` · `RN-C04` · `RN-E01` · `RN-E02` ·
      `RN-M03` · `RN-M07` · `RN-U02` · `QA-M03` · `QA-M04`

GIVEN  un comprador, un alcance de edición y un catálogo
WHEN   se pide un pedido
THEN   el pedido se RECHAZA o se RECUPERA según las reglas, y cada rechazo
       viaja con su CÓDIGO estable — nunca con un error de forma.

La prueba es de COMPORTAMIENTO: mira lo que el dominio GARANTIZA, no cómo
está escrito. Los dobles no hacen falta: los servicios son los de producción
y se resuelven por el inyector.

**Sin concurrencia.** Estas pruebas son SECUENCIALES a propósito: la
concurrencia se decide en la base de datos (índice parcial único) y su
verificación pertenece a la fase de verificación, no a este paquete.
"""

import uuid
from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync

from modules.marketplace.domain.constants import MAX_CANTIDAD_ITEM_PEDIDO
from modules.marketplace.domain.exceptions import (
    CompradorSinPersonaError,
    ModuloNoHabilitadoError,
    PedidoCantidadInvalidaError,
    PedidoItemNoPermitidoError,
    PedidoItemsMixtosError,
    PedidoNoAutorizadoError,
    ProductoNoDisponibleError,
    ProductoNoEncontradoError,
)
from modules.marketplace.domain.models import Pedido
from modules.marketplace.domain.schemas.pedido_schemas import (
    PedidoCreateData,
    PedidoItemCreateData,
)


def _item(producto_id, cantidad: int = 1, tipo: str = "PRODUCTO"):
    """Un artículo declarado: QUÉ pide y CUÁNTO. NUNCA un importe."""
    return PedidoItemCreateData(
        tipo=tipo,
        producto_id=producto_id,
        cantidad=cantidad,
    )


def _intencion(*items) -> PedidoCreateData:
    """La intención de compra."""
    return PedidoCreateData(items=list(items))


# ── RN-C01 · no hay carrito combinado ────────────────────────────────────────


@pytest.mark.django_db
def test_un_pedido_no_puede_mezclar_productos_y_pases(
    pedido_orchestrator, usuario_comprador, producto
):
    """GIVEN una intención con un producto y un pase
    WHEN  se crea el pedido
    THEN  se rechaza con `PEDIDO_ITEMS_MIXTOS`: la tienda y el pase tienen
          su propio checkout (RN-C01).
    """
    intencion = _intencion(_item(producto.id), _item(producto.id, tipo="PASE"))

    with pytest.raises(PedidoItemsMixtosError):
        async_to_sync(pedido_orchestrator.crear_pedido)(usuario_comprador, intencion)

    assert Pedido.objects.count() == 0


@pytest.mark.django_db
def test_un_pedido_solo_con_pases_se_rechaza(
    pedido_orchestrator, usuario_comprador, producto
):
    """GIVEN una intención con SÓLO pases
    WHEN  se crea el pedido
    THEN  se rechaza con `PEDIDO_ITEM_NO_PERMITIDO`: un pase no es un
          producto de la tienda (RN-C01, DEC-10).
    """
    intencion = _intencion(_item(producto.id, tipo="PASE"))

    with pytest.raises(PedidoItemNoPermitidoError):
        async_to_sync(pedido_orchestrator.crear_pedido)(usuario_comprador, intencion)

    assert Pedido.objects.count() == 0


@pytest.mark.django_db
def test_un_pedido_solo_con_inscripciones_se_rechaza(
    pedido_orchestrator, usuario_comprador, producto
):
    """GIVEN una intención con SÓLO inscripciones
    WHEN  se crea el pedido
    THEN  se rechaza con `PEDIDO_ITEM_NO_PERMITIDO`: una inscripción se
          compra por su propio flujo (RN-C01).
    """
    intencion = _intencion(_item(producto.id, tipo="INSCRIPCION"))

    with pytest.raises(PedidoItemNoPermitidoError):
        async_to_sync(pedido_orchestrator.crear_pedido)(usuario_comprador, intencion)


# ── La cantidad la valida el SERVIDOR ────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.parametrize("cantidad", [0, -1, MAX_CANTIDAD_ITEM_PEDIDO + 1])
def test_una_cantidad_invalida_se_rechaza(
    pedido_orchestrator, usuario_comprador, producto, cantidad
):
    """GIVEN una cantidad que no es admisible
    WHEN  se crea el pedido
    THEN  se rechaza con `PEDIDO_CANTIDAD_INVALIDA`: la cantidad la decide
          el servidor, no el cliente.
    """
    intencion = _intencion(_item(producto.id, cantidad=cantidad))

    with pytest.raises(PedidoCantidadInvalidaError):
        async_to_sync(pedido_orchestrator.crear_pedido)(usuario_comprador, intencion)

    assert Pedido.objects.count() == 0


# ── El producto tiene que existir y estar disponible ─────────────────────────


@pytest.mark.django_db
def test_un_producto_inexistente_se_rechaza(
    pedido_orchestrator, usuario_comprador, edicion_publicada
):
    """GIVEN un producto que no existe
    WHEN  se crea el pedido
    THEN  se rechaza con `PRODUCTO_NO_ENCONTRADO` (404) y NO se crea ningún
          pedido: la resolución del catálogo ocurre ANTES de escribir.
    """
    intencion = _intencion(_item(uuid.uuid4()))

    with pytest.raises(ProductoNoEncontradoError):
        async_to_sync(pedido_orchestrator.crear_pedido)(usuario_comprador, intencion)

    assert Pedido.objects.count() == 0


@pytest.mark.django_db
def test_un_producto_retirado_no_se_pide(
    pedido_orchestrator, usuario_comprador, producto_inactivo
):
    """GIVEN un producto `INACTIVO`
    WHEN  se crea el pedido
    THEN  se rechaza con `PRODUCTO_NO_DISPONIBLE`: el catálogo público sólo
          ofrece productos `ACTIVO`.
    """
    intencion = _intencion(_item(producto_inactivo.id))

    with pytest.raises(ProductoNoDisponibleError):
        async_to_sync(pedido_orchestrator.crear_pedido)(usuario_comprador, intencion)

    assert Pedido.objects.count() == 0


@pytest.mark.django_db
def test_un_producto_de_otra_edicion_no_se_pide(
    pedido_orchestrator, usuario_comprador, producto_ajeno, edicion_publicada
):
    """GIVEN un producto que pertenece a OTRA edición
    WHEN  se crea el pedido
    THEN  se rechaza con `PRODUCTO_NO_DISPONIBLE`: la coherencia de edición
          es estructural (FR-02 §3 · RN-E01).
    """
    intencion = _intencion(_item(producto_ajeno.id))

    with pytest.raises(ProductoNoDisponibleError):
        async_to_sync(pedido_orchestrator.crear_pedido)(usuario_comprador, intencion)

    assert Pedido.objects.count() == 0


# ── El alcance lo resuelve el servidor ───────────────────────────────────────


@pytest.mark.django_db
def test_una_edicion_sin_la_tienda_no_acepta_pedidos(
    pedido_orchestrator, usuario_comprador, edicion_publicada_sin_tienda
):
    """GIVEN una edición con el módulo `marketplace` DESHABILITADO
    WHEN  se crea el pedido
    THEN  se rechaza con `MODULO_NO_HABILITADO` (RN-E02): el cliente no
          elige el alcance, y una edición sin tienda no expone la tienda.
    """
    from modules.marketplace.domain.models import Producto

    producto = Producto.objects.create(
        edicion=edicion_publicada_sin_tienda,
        nombre="Producto fuera de alcance",
        slug="fuera-de-alcance",
        precio="5.00",
        estado="ACTIVO",
    )
    intencion = _intencion(_item(producto.id))

    with pytest.raises(ModuloNoHabilitadoError):
        async_to_sync(pedido_orchestrator.crear_pedido)(usuario_comprador, intencion)

    assert Pedido.objects.count() == 0


# ── El comprador es la persona de la cuenta ──────────────────────────────────


@pytest.mark.django_db
def test_una_cuenta_sin_persona_no_puede_comprar(
    pedido_orchestrator, usuario_sin_persona, producto
):
    """GIVEN una cuenta autenticada SIN `Persona` vinculada
    WHEN  se crea el pedido
    THEN  se rechaza con `COMPRADOR_SIN_PERSONA`: el comprador es la persona
          de la cuenta, nunca el documento (RN-U04).
    """
    intencion = _intencion(_item(producto.id))

    with pytest.raises(CompradorSinPersonaError):
        async_to_sync(pedido_orchestrator.crear_pedido)(usuario_sin_persona, intencion)

    assert Pedido.objects.count() == 0


# ── RN-U02 · la titularidad del pedido ───────────────────────────────────────


@pytest.mark.django_db
def test_otro_usuario_no_puede_consultar_el_pedido(
    pedido_orchestrator, usuario_comprador, usuario_ajeno, producto
):
    """GIVEN un pedido de un comprador
    WHEN  OTRO actor autenticado intenta consultarlo con el token
    THEN  se rechaza con `PEDIDO_NO_AUTORIZADO` (403): ser administrador no
          sustituye la titularidad (RN-U02, FR-03 §2.1).
    """
    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(_item(producto.id)),
    )

    with pytest.raises(PedidoNoAutorizadoError):
        async_to_sync(pedido_orchestrator.obtener_pedido_por_token)(
            resultado.token,
            usuario_ajeno,
        )


@pytest.mark.django_db
def test_el_comprador_consulta_su_pedido_con_el_token(
    pedido_orchestrator, usuario_comprador, producto
):
    """GIVEN un pedido del comprador
    WHEN  el propio comprador lo consulta con su token
    THEN  lo obtiene con sus TRES estados por separado.
    """
    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(_item(producto.id)),
    )

    seguimiento = async_to_sync(pedido_orchestrator.obtener_pedido_por_token)(
        resultado.token,
        usuario_comprador,
    )

    assert seguimiento.id == resultado.id
    assert seguimiento.estado == resultado.estado
    assert seguimiento.estado_pago == resultado.estado_pago
    assert seguimiento.estado_entrega == resultado.estado_entrega


# ── RN-C03 / RN-C04 · un reintento NO duplica el pedido ──────────────────────


@pytest.mark.django_db
def test_un_reintento_recupera_el_mismo_pedido(
    pedido_orchestrator, usuario_comprador, producto
):
    """GIVEN un pedido ya creado
    WHEN  se repite EXACTAMENTE la misma intención
    THEN  se RECUPERA el mismo pedido (mismo id, mismo token) y NO se crea
          un segundo: la huella identifica la INTENCIÓN (RN-C03, RN-C04).
    """
    intencion = _intencion(_item(producto.id, cantidad=2))

    primero = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador, intencion
    )
    segundo = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador, intencion
    )

    assert primero.recuperado is False
    assert segundo.recuperado is True
    assert segundo.id == primero.id
    assert segundo.token == primero.token
    assert Pedido.objects.count() == 1


@pytest.mark.django_db
def test_un_reintento_no_duplica_la_compra(
    pedido_orchestrator, usuario_comprador, producto
):
    """GIVEN un pedido ya creado
    WHEN  se repite la misma intención
    THEN  la COMPRA que lo financia es la MISMA: la referencia de la compra
          es la del pedido (FR-04 I-4, RN-C04).
    """
    from modules.commerce.domain.models import Compra

    intencion = _intencion(_item(producto.id, cantidad=2))

    primero = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador, intencion
    )
    async_to_sync(pedido_orchestrator.crear_pedido)(usuario_comprador, intencion)

    assert Compra.objects.count() == 1
    assert Pedido.objects.get(id=primero.id).compra_id is not None


@pytest.mark.django_db
def test_una_intencion_distinta_crea_otro_pedido(
    pedido_orchestrator, usuario_comprador, producto, producto_con_oferta
):
    """GIVEN un pedido de un producto
    WHEN  se pide OTRO producto
    THEN  es OTRA intención: se crea un segundo pedido (la huella es lo que
          identifica la intención, no la persona).
    """
    primero = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(_item(producto.id)),
    )
    segundo = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(_item(producto_con_oferta.id)),
    )

    assert primero.id != segundo.id
    assert segundo.recuperado is False
    assert Pedido.objects.count() == 2


# ── El total lo deriva el servidor ───────────────────────────────────────────


@pytest.mark.django_db
def test_el_total_lo_deriva_el_servidor_de_las_lineas(
    pedido_orchestrator, usuario_comprador, producto_con_oferta
):
    """GIVEN un producto con oferta vigente
    WHEN  se crea el pedido
    THEN  el total es la suma de las líneas con el PRECIO APLICADO: el
          cliente no impone ningún importe (RN-C02).
    """
    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        _intencion(_item(producto_con_oferta.id, cantidad=3)),
    )

    assert resultado.total == Decimal("21.00")
    assert resultado.moneda == "PEN"
