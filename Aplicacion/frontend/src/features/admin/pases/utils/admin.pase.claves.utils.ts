import type { QueryKey } from "@tanstack/react-query";
import { buildQueryKey } from "@/shared/utils/query-keys";

/**
 * The query keys of the ADMINISTRATIVE PASSES.
 *
 * The area owns its OWN namespace: `["admin", "pases", "cortesias"]`.
 *
 * The shared namespace of the administration (`adminClaves`) is NOT touched:
 * it belongs to another owner and the courtesies are not one of its datasets.
 * One dataset, one namespace (`R7`).
 *
 * EVERY parameter that changes the answer travels in the key: a parameter that
 * is `undefined` is dropped, so `{page: undefined}` and no key at all are the
 * SAME cache entry.
 */

/** The parameters that change the answer of the list of courtesies. */
export interface ParamsListaCortesias {
  /** The edition that scopes the list. */
  edicion_id?: string;
  /** The state of the courtesy (`ACTIVA` | `REVOCADA`). */
  estado?: string;
  /** The page, 1-based. */
  page?: number;
  /** The size of the page. */
  page_size?: number;
}

/** The root of the namespace of the courtesies. */
const CORTESIAS: QueryKey = ["admin", "pases", "cortesias"];

export const adminPaseClaves = {
  /** The root of the whole area: the invalidation target of every dataset. */
  todas: ["admin", "pases"] as const,

  /**
   * The root of the courtesies: the target of the invalidation of a courtesy.
   *
   * It is a PREFIX of every read of the dataset, so invalidating it
   * invalidates the list and nothing else.
   */
  cortesias: () => CORTESIAS,

  /** The key of ONE read of the list of courtesies. */
  cortesiasParams: (params?: ParamsListaCortesias) =>
    buildQueryKey(CORTESIAS, params ? { ...params } : undefined),
} as const;
