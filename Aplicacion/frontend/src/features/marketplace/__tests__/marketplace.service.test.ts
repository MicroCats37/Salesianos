import { beforeEach, describe, expect, it, vi } from "vitest";

const { apiSend } = vi.hoisted(() => ({ apiSend: vi.fn() }));

vi.mock("@/lib/api", () => ({
  apiSend,
  default: {
    get: vi.fn(),
    request: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

import {
  ErrorContratoMarketplace,
  listarCategorias,
  listarProductos,
  obtenerProducto,
} from "../services/marketplace.service";
import { marketplaceClaves } from "../utils/marketplace.claves.utils";

/**
 * The wire of the store.
 *
 * The suite proves the rules that the interface depends on: the URL comes
 * from the REGISTERED controller, the pagination has the ONE shape of the
 * target, a body that does not comply is a LOUD failure and the `204` is
 * never parsed.
 */
function envelope(data: unknown) {
  return {
    status: 200,
    data: { success: true, data, error: null, message: null },
  };
}

beforeEach(() => {
  apiSend.mockReset();
});
describe("el cliente de la tienda", () => {
  it("las categorías se piden a la ruta registrada", async () => {
    apiSend.mockResolvedValue(envelope([]));

    await listarCategorias();

    expect(apiSend).toHaveBeenCalledWith(
      "get",
      "/marketplace/categorias",
      undefined,
      expect.objectContaining({ params: undefined }),
    );
  });

  it("el catálogo se pide con el filtro y la página", async () => {
    apiSend.mockResolvedValue(
      envelope({ items: [], total: 0, page: 1, page_size: 25, total_pages: 0 }),
    );

    const pagina = await listarProductos({
      categoria_id: "cat-1",
      page: 2,
      page_size: 25,
    });

    expect(pagina.total).toBe(0);
    expect(pagina.total_pages).toBe(0);
    expect(apiSend).toHaveBeenCalledWith(
      "get",
      "/marketplace/productos",
      undefined,
      expect.objectContaining({
        params: { categoria_id: "cat-1", page: 2, page_size: 25 },
      }),
    );
  });

  it("una paginación con otra forma es un fallo ruidoso", async () => {
    apiSend.mockResolvedValue(envelope({ data: [], count: 3 }));

    await expect(listarProductos()).rejects.toBeInstanceOf(
      ErrorContratoMarketplace,
    );
  });

  it("un 204 nunca se parsea", async () => {
    apiSend.mockResolvedValue({ status: 204, data: null });

    await expect(listarCategorias()).rejects.toBeInstanceOf(
      ErrorContratoMarketplace,
    );
  });

  it("el detalle se pide por el identificador del producto", async () => {
    apiSend.mockResolvedValue(envelope({ id: "x" }));

    await obtenerProducto("producto-de-ejemplo");

    const [, url] = apiSend.mock.calls[0];
    expect(url).toBe("/marketplace/productos/producto-de-ejemplo");
  });
});
describe("las claves de la tienda", () => {
  it("el filtro y la página viajan en la clave del catálogo", () => {
    expect(
      marketplaceClaves.productosParams({ categoria_id: "cat-1", page: 2 }),
    ).toEqual(["marketplace", "catalogo", "productos", { categoria_id: "cat-1", page: 2 }]);
  });

  it("un filtro ausente es la misma entrada que ninguno", () => {
    expect(marketplaceClaves.productosParams()).toEqual([
      "marketplace",
      "catalogo",
      "productos",
    ]);
    expect(
      marketplaceClaves.productosParams({ categoria_id: undefined, page: undefined }),
    ).toEqual(["marketplace", "catalogo", "productos"]);
  });

  it("el detalle vive en su propia familia", () => {
    expect(marketplaceClaves.detalle("producto-de-ejemplo")).toEqual([
      "marketplace",
      "productos",
      "producto-de-ejemplo",
    ]);
  });
});