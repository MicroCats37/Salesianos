import type { Method } from "axios";
import type { ZodType } from "zod";
import { apiSend } from "@/lib/api";
import type { PaginatedResult } from "@/shared/schemas/pagination.schema";
import {
  categoriasEnvelope,
  productoDetalleEnvelope,
  productosEnvelope,
  type CategoriaLista,
  type ProductoDetalle,
  type ProductoListItem,
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

/** The base of every route of the store. */
const BASE = "/marketplace";

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
): Promise<T> {
  const { status, data } = await apiSend<unknown>(method, url, undefined, {
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
  return pedir("get", `${BASE}/categorias`, categoriasEnvelope);
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
  return pedir("get", `${BASE}/productos`, productosEnvelope, params);
}

/** The detail of a product (`RT-MK-03`). */
export function obtenerProducto(slug: string): Promise<ProductoDetalle> {
  return pedir(
    "get",
    `${BASE}/productos/${encodeURIComponent(slug)}`,
    productoDetalleEnvelope,
  );
}
