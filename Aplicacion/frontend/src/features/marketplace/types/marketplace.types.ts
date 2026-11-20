/**
 * The view models of the store area (`SHOP-01`, `SHOP-02`, `SHOP-03`).
 *
 * The SHAPE of the wire is owned by the Zod mirrors:
 *
 * - `schemas/producto.schema.ts` mirrors the presenters of `DOM-04`
 *   (`ProductoListItemOut`, `ProductoDetalleOut`, `ProductoImagenOut` and
 *   `CategoriaListaOut`).
 * - `schemas/pedido.schema.ts` mirrors the presenters of `DOM-05`
 *   (`PedidoSeguimientoOut` and `PedidoLineaOut`). **The order routes are NOT
 *   registered** (`A0-RTV-02`): the mirror is a seam, not a binding.
 *
 * No business rule lives here. A price, an offer, an availability, a stock,
 * a payment state and a delivery state are DECLARED by the presenter and
 * never derived in the browser (`SH-01` T-03).
 */

/** The order of the store (`DOM-05`) — NOT REGISTERED, NOT BOUND. */
export type {
  PedidoLinea as LineaPedido,
  PedidoSeguimiento as SeguimientoPedido,
} from "../schemas/pedido.schema";
/** The catalogue of the store (`DOM-04`). */
export type {
  CategoriaLista as CategoriaProducto,
  ProductoDetalle,
  ProductoImagen as ImagenProducto,
  ProductoListItem,
} from "../schemas/producto.schema";

/** The five presentable payment states of `SH-03` section 3. */
export type RolPago =
  | "pendiente"
  | "verificando"
  | "confirmado"
  | "sin-confirmar"
  | "atencion";

/** The verdict of the backend (`EstadoOperativo`, `FREEZE-ENV-1.0.0` 5). */
export interface EstadoPagoOperativo {
  codigo: string;
  etiqueta: string;
  descripcion: string;
}

/**
 * A payment verdict with its visual bucket.
 *
 * `estado` is what the backend says; `rol` is how the adapter decided to
 * paint it. Both travel together so the label and the colour can never
 * disagree.
 */
export interface VeredictoPago {
  estado: EstadoPagoOperativo;
  rol: RolPago;
}

/**
 * A fact of the backend with its label.
 *
 * The presenters of `DOM-05` publish the payment and the delivery as machine
 * codes (`estado_pago`, `estado_entrega`). The interface never shows a code
 * (`SH-03` 6), so the ADAPTER resolves the label and both travel together.
 */
export interface EstadoDeclarado {
  codigo: string;
  etiqueta: string;
}

/**
 * The state a route is in.
 *
 * The default is the honest one and `cargando` is the state of a read that is
 * in flight: the route says it is working and it never invents a remaining
 * time (`SH-03` S-08).
 */
export type EstadoVistaTienda =
  | "sin-datos"
  | "cargando"
  | "listo"
  | "sin-permiso"
  | "error";
