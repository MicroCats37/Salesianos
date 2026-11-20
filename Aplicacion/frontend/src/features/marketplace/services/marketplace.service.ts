import type { AxiosRequestConfig, Method } from "axios";
import type { ZodType } from "zod";
import { apiSend } from "@/lib/api";
import type { PaginatedResult } from "@/shared/schemas/pagination.schema";
import type { PayloadResult } from "@/utils/payload-builder";
import {
  type CrearPedido,
  crearPedidoSchema,
  type IzipayConfirmacionPedido,
  type IzipayPreparacionPedido,
  izipayConfirmacionPedidoSchema,
  izipayPreparacionPedidoEnvelope,
  type PagoConfirmadoPedido,
  type PedidoCreado,
  type PedidoSeguimiento,
  pagoConfirmadoPedidoEnvelope,
  pedidoCreadoEnvelope,
  pedidoSeguimientoEnvelope,
  type TransaccionPedido,
  transaccionPedidoEnvelope,
} from "../schemas/pedido.schema";
import {
  type CategoriaLista,
  categoriasEnvelope,
  type ProductoCreado,
  type ProductoCrearPayload,
  type ProductoDetalle,
  type ProductoListItem,
  productoCreadoEnvelope,
  productoDetalleEnvelope,
  productosEnvelope,
} from "../schemas/producto.schema";

/**
 * The ONE client of the store.
 *
 * Every URL comes from the REGISTERED controller
 * (`Aplicacion/backend/modules/marketplace/presentation/controllers/producto_controller.py`
 * → `ProductoController`): a route that is not registered does not exist and
 * is never called from here.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `RT-MK-01` | GET | `/marketplace/categorias` | `list[CategoriaListaOut]` |
 * | `RT-MK-02` | GET | `/marketplace/productos` | `PaginatedData[ProductoListItemOut]` |
 * | `RT-MK-03` | GET | `/marketplace/productos/{slug}` | `ProductoDetalleOut` |
 *
 * The transport is `apiSend` (`src/lib/api.ts`), the single owner of the
 * HTTP client and of the rule that a `204` is never parsed.
 *
 * **THE ORDERS ARE NOT HERE.** `PedidoController` is NOT registered
 * (`A0-RTV-02`), so `POST /marketplace/pedidos` and
 * `GET /marketplace/pedidos/{token}` do NOT exist: binding them would be
 * binding a route that is dead code by design (`FR-07` §3.1 regla 2).
 */

/** The root of every route of the store. */
export const RUTA_MARKETPLACE = "/marketplace";

/** The root of every route of the store, for the client of the area. */
const BASE = RUTA_MARKETPLACE;

/**
 * The route of the Izipay session of ONE order.
 *
 * The payment lives in its own namespace (`/pagos`) and it is scoped to the
 * private token of the order: the route is built here, in the client, so the
 * hook never spells a path.
 */
export function rutaPreparacionPago(token: string): string {
  return `/pagos${RUTA_MARKETPLACE}/pedidos/${encodeURIComponent(token)}/izipay`;
}

/** The route of the confirmation of the payment of ONE order. */
export function rutaConfirmacionPago(token: string): string {
  return `/pagos${RUTA_MARKETPLACE}/pedidos/${encodeURIComponent(token)}/izipay/confirmar`;
}

/**
 * The routes of the store, published for the GENERIC family.
 *
 * The family calls the ENDPOINT: it needs the URL of the route and the mirror
 * of its envelope, and both of them live HERE, in the ONE client of the store.
 * A hook never spells a path.
 */

/** The route of the categories of the catalogue (`RT-MK-01`). */
export function rutaCategorias(): string {
  return `${BASE}/categorias`;
}

/** The route of the catalogue of products (`RT-MK-02`). */
export function rutaProductos(): string {
  return `${BASE}/productos`;
}

/** The route of the detail of ONE product (`RT-MK-03`). */
export function rutaProductoDetalle(slug: string): string {
  return `${BASE}/productos/${encodeURIComponent(slug)}`;
}

/** The route of the order opened by ONE private recovery credential. */
export function rutaPedido(token: string): string {
  return `${BASE}/pedidos/${encodeURIComponent(token)}`;
}

/** The route of the commercial order of the store. */
export function rutaPedidos(): string {
  return `${BASE}/pedidos`;
}

/** The route of the attempt of the provider of ONE order. */
export function rutaTransaccionPedido(
  token: string,
  transactionId: string,
): string {
  return `/pagos${BASE}/pedidos/${encodeURIComponent(token)}/transacciones/${encodeURIComponent(transactionId)}`;
}

/**
 * The answer of the server does NOT comply with the frozen contract.
 *
 * It is NOT a network failure: the request arrived and the body is not the
 * shape the presenter promises. The mirror parses LOUDLY, so this error
 * never hides behind a partial trust.
 */
export class ErrorContratoMarketplace extends Error {
  constructor(
    message: string,
    public readonly causa?: unknown,
  ) {
    super(message);
    this.name = "ErrorContratoMarketplace";
  }
}

/**
 * The single way this feature talks to the backend.
 *
 * It applies the rules of the envelope ONCE: the `204` is never parsed, the
 * body is parsed with the Zod mirror of the wrapper and a body that does not
 * comply is a loud failure.
 */
async function pedir<T>(
  method: Method,
  url: string,
  envelope: ZodType<{ success: boolean; data: T | null }>,
  params?: Record<string, string | number | undefined>,
  config?: AxiosRequestConfig,
): Promise<T> {
  const { status, data } = await apiSend<unknown>(method, url, undefined, {
    ...config,
    params,
  });

  if (status === 204 || data === null) {
    // El 204 no lleva cuerpo: NUNCA se parsea (FREEZE-ENV-1.0.0 §4.4).
    throw new ErrorContratoMarketplace(
      "El servidor respondió sin contenido donde se esperaba un cuerpo.",
    );
  }

  const parseado = envelope.safeParse(data);

  if (!parseado.success) {
    throw new ErrorContratoMarketplace(
      "La respuesta del servidor no cumple el contrato esperado.",
      parseado.error,
    );
  }

  if (!parseado.data.success || parseado.data.data === null) {
    throw new ErrorContratoMarketplace("El servidor respondió sin datos.");
  }

  return parseado.data.data;
}

/** The categories of the catalogue (`RT-MK-01`). */
export function listarCategorias(): Promise<CategoriaLista[]> {
  return pedir("get", rutaCategorias(), categoriasEnvelope);
}

/**
 * The catalogue of products (`RT-MK-02`).
 *
 * The browser NEVER filters a catalogue on its own: the category travels to
 * the server and the server answers with the page that belongs to it.
 */
export function listarProductos(params?: {
  categoria_id?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResult<ProductoListItem>> {
  return pedir("get", rutaProductos(), productosEnvelope, params);
}

/** The detail of a product (`RT-MK-03`). */
export function obtenerProducto(
  slug: string,
  config?: AxiosRequestConfig,
): Promise<ProductoDetalle> {
  return pedir(
    "get",
    rutaProductoDetalle(slug),
    productoDetalleEnvelope,
    undefined,
    config,
  );
}

/** Creates the commercial order and returns its private recovery credential. */
export async function crearPedido(payload: CrearPedido): Promise<PedidoCreado> {
  const body = crearPedidoSchema.parse(payload);
  const { status, data } = await apiSend<unknown>("post", rutaPedidos(), body);
  if (status === 204 || data === null) {
    throw new ErrorContratoMarketplace(
      "El servidor no devolvió el pedido creado.",
    );
  }
  const parseado = pedidoCreadoEnvelope.safeParse(data);
  if (
    !parseado.success ||
    !parseado.data.success ||
    parseado.data.data === null
  ) {
    throw new ErrorContratoMarketplace(
      "La respuesta del servidor no cumple el contrato esperado.",
      parseado.success ? undefined : parseado.error,
    );
  }
  return parseado.data.data;
}

/** Reads the authoritative state opened by the private recovery token. */
export function obtenerPedido(token: string): Promise<PedidoSeguimiento> {
  return pedir("get", rutaPedido(token), pedidoSeguimientoEnvelope);
}

/** Starts one Izipay session for the private order opened by the token. */
export function prepararPagoPedido(
  token: string,
): Promise<IzipayPreparacionPedido> {
  return pedir(
    "post",
    rutaPreparacionPago(token),
    izipayPreparacionPedidoEnvelope,
  );
}

/** Relays Izipay's signed callback to the token-scoped confirmation endpoint. */
export async function confirmarPagoPedido(
  token: string,
  payload: IzipayConfirmacionPedido,
): Promise<PagoConfirmadoPedido> {
  const body = izipayConfirmacionPedidoSchema.parse(payload);
  const { status, data } = await apiSend<unknown>(
    "post",
    rutaConfirmacionPago(token),
    { kr_answer: body },
  );

  if (status === 204 || data === null) {
    throw new ErrorContratoMarketplace(
      "El servidor no devolvió la confirmación.",
    );
  }

  const parseado = pagoConfirmadoPedidoEnvelope.safeParse(data);
  if (
    !parseado.success ||
    !parseado.data.success ||
    parseado.data.data === null
  ) {
    throw new ErrorContratoMarketplace(
      "La respuesta del servidor no cumple el contrato esperado.",
      parseado.success ? undefined : parseado.error,
    );
  }
  return parseado.data.data;
}

/** Reads the provider attempt when the browser relay is inconclusive. */
export function obtenerEstadoTransaccionPedido(
  token: string,
  transactionId: string,
): Promise<TransaccionPedido> {
  return pedir(
    "get",
    rutaTransaccionPedido(token, transactionId),
    transaccionPedidoEnvelope,
  );
}

/** Creates a product through the administrator-only marketplace endpoint. */
export async function crearProducto(
  payload: PayloadResult<ProductoCrearPayload>,
): Promise<ProductoCreado> {
  const { status, data } = await apiSend<unknown>(
    "post",
    rutaProductos(),
    payload,
  );

  if (status === 204 || data === null) {
    throw new ErrorContratoMarketplace(
      "El servidor respondió sin contenido al crear el producto.",
    );
  }

  const parseado = productoCreadoEnvelope.safeParse(data);
  if (
    !parseado.success ||
    !parseado.data.success ||
    parseado.data.data === null
  ) {
    throw new ErrorContratoMarketplace(
      "La respuesta del servidor no cumple el contrato esperado.",
      parseado.success ? undefined : parseado.error,
    );
  }

  return parseado.data.data;
}
