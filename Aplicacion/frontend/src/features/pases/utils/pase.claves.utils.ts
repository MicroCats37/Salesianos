import type { QueryKey } from "@tanstack/react-query";
import { buildQueryKey } from "@/shared/utils/query-keys";

/**
 * The query keys of the pass domain.
 *
 * They live HERE and nowhere else: a component never spells a key. One
 * dataset, one namespace: every read of the catalogue of passes shares
 * `["pase", "catalogo", …]` and every read of a purchase shares
 * `["pase", "compras", …]`.
 *
 * EVERY parameter that changes the answer travels in the key (`edicion_id`
 * for the catalogue, the identifiers for a purchase). A parameter that is
 * `undefined` is dropped, so `{edicion_id: undefined}` and no key at all are
 * the SAME cache entry.
 */

/** The root of the catalogue namespace. */
const CATALOGO: QueryKey = ["pase", "catalogo"];

/** The root of the purchases namespace. */
const COMPRAS: QueryKey = ["pase", "compras"];

export const paseClaves = {
  /** The root of the whole pass domain. */
  todas: ["pase"] as const,

  /** The catalogue of the passes of one edition. */
  catalogo: () => CATALOGO,

  /**
   * The key of ONE catalogue read.
   *
   * The edition is the only parameter that changes the answer: the server
   * resolves it when it is not declared.
   */
  catalogoParams: (params?: { edicion_id?: string }) =>
    buildQueryKey(CATALOGO, params),

  /** The key of ONE pass detail. */
  detalle: (paseId: string) => ["pase", "detalle", paseId] as const,

  /** The root of the purchases: the target of the invalidation of a purchase. */
  compras: () => COMPRAS,

  /** The key of ONE purchase. */
  compra: (compraPaseId: string) => [...COMPRAS, compraPaseId] as const,

  /** The key of the beneficiaries of ONE purchase. */
  beneficiarios: (compraPaseId: string) =>
    [...COMPRAS, compraPaseId, "beneficiarios"] as const,
} as const;
