import type { QueryKey } from "@tanstack/react-query";
import { buildQueryKey } from "@/shared/utils/query-keys";

/**
 * The query keys of the store.
 *
 * They live HERE and nowhere else: a component never spells a key. One
 * dataset, one namespace: every read of the catalogue of the store shares
 * `["marketplace", …]` and every read of a product detail shares its own.
 *
 * EVERY parameter that changes the answer travels in the key (the category,
 * the page and the size of the page). A parameter that is `undefined` is
 * dropped, so `{categoria_id: undefined}` and no parameters at all are the
 * SAME cache entry.
 */

/** The root of the catalogue namespace. */
const CATALOGO: QueryKey = ["marketplace", "catalogo"];

/** The root of the product details namespace. */
const PRODUCTOS: QueryKey = ["marketplace", "productos"];

export const marketplaceClaves = {
  /** The root of the whole store domain. */
  todas: ["marketplace"] as const,

  /** The categories of the catalogue. */
  categorias: () => [...CATALOGO, "categorias"] as const,

  /**
   * The key of ONE page of the catalogue.
   *
   * The category, the page and the size travel in it: two pages are two
   * cache entries.
   */
  productosParams: (params?: {
    categoria_id?: string;
    page?: number;
    page_size?: number;
  }) => buildQueryKey([...CATALOGO, "productos"], params),

  /** The key of ONE product detail. */
  detalle: (slug: string) => [...PRODUCTOS, slug] as const,
} as const;
