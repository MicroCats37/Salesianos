import type { QueryKey } from "@tanstack/react-query";

/**
 * The parameters that change the answer of a read.
 *
 * A parameter that is `undefined` does NOT change the answer: it is dropped so
 * that `{ page: 1 }` and `{ page: 1, q: undefined }` are the SAME cache entry
 * and not two.
 */
export function queryParams<T extends Record<string, unknown>>(
  params: T,
): Partial<T> {
  const result: Partial<T> = {};

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      result[key as keyof T] = value as T[keyof T];
    }
  }

  return result;
}

/**
 * The key of a read of a dataset.
 *
 * EVERY parameter that changes the answer travels in the key. A read without
 * parameters keeps the key of its family, so ONE dataset is ONE namespace.
 */
export function buildQueryKey<T extends Record<string, unknown>>(
  baseKey: QueryKey,
  params?: T,
): QueryKey {
  if (params === undefined) return [...baseKey];
  return [...baseKey, queryParams(params)];
}

/**
 * The key factory of ONE dataset.
 *
 * The literals of a key live HERE and nowhere else: a component never spells
 * a key. The root of the namespace (`all`) is the invalidation target of the
 * whole dataset: invalidating it invalidates every read of that dataset and
 * nothing else.
 */
export interface DatasetQueryKeys<
  TParams extends Record<string, unknown> = Record<string, never>,
  TId = string | number,
> {
  /** The root of the namespace: `["catalogo"]`. */
  readonly all: QueryKey;
  /** The family of the list reads: `["catalogo", "list"]`. */
  readonly list: QueryKey;
  /** The key of ONE list read: every response-changing parameter travels in it. */
  listPage(params?: TParams): QueryKey;
  /** The key of ONE detail read: `["catalogo", "detail", id]`. */
  detail(id: TId): QueryKey;
}

/**
 * Builds the key factory of a dataset.
 *
 * @example
 * const catalogo = createDatasetQueryKeys<{ page: number }>("catalogo");
 * catalogo.listPage({ page: 2 }); // ["catalogo", "list", { page: 2 }]
 * catalogo.detail(7);            // ["catalogo", "detail", 7]
 */
export function createDatasetQueryKeys<
  TParams extends Record<string, unknown> = Record<string, never>,
  TId = string | number,
>(scope: string): DatasetQueryKeys<TParams, TId> {
  const all: QueryKey = [scope];
  const list: QueryKey = [scope, "list"];

  return {
    all,
    list,
    listPage: (params?: TParams) => buildQueryKey(list, params),
    detail: (id: TId) => [scope, "detail", id],
  };
}
