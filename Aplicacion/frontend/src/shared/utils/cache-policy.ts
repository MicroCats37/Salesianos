import type { QueryClient, QueryKey } from "@tanstack/react-query";
import {
  isPaginatedResult,
  type PaginatedResult,
} from "../schemas/pagination.schema";

/** The keys that a mutation invalidates when it settles. */
export type InvalidationTargets = readonly QueryKey[];

/**
 * Invalidates ONLY the affected keys.
 *
 * The keys are prefixes: invalidating `["catalogo"]` invalidates every read
 * of that dataset (`["catalogo","list",…]` and `["catalogo","detail",…]`) and
 * nothing else.
 */
export async function invalidateDatasets(
  queryClient: QueryClient,
  keys: InvalidationTargets = [],
): Promise<void> {
  for (const key of keys) {
    await queryClient.invalidateQueries({ queryKey: key });
  }
}

/**
 * Writes into a cached PLAIN LIST.
 *
 * The write happens ONLY when the cached value IS a plain list. A paginated
 * envelope, a detail object or an absent entry are left alone: the exact
 * shape is not known, so the invalidation does the work.
 */
export function updateCachedList<T>(
  queryClient: QueryClient,
  queryKey: QueryKey,
  updater: (items: T[]) => T[],
): boolean {
  const cached = queryClient.getQueryData(queryKey);

  if (!Array.isArray(cached)) return false;

  queryClient.setQueryData(queryKey, updater(cached as T[]));

  return true;
}

/**
 * Writes into a cached PAGINATED page, preserving the whole envelope.
 */
export function updateCachedPage<T>(
  queryClient: QueryClient,
  queryKey: QueryKey,
  updater: (page: PaginatedResult<T>) => PaginatedResult<T>,
): boolean {
  const cached = queryClient.getQueryData(queryKey);

  if (!isPaginatedResult(cached)) return false;

  queryClient.setQueryData(queryKey, updater(cached as PaginatedResult<T>));

  return true;
}

/**
 * Writes into a cached DETAIL.
 *
 * The entry MUST already exist: a detail that was never read is not created
 * out of thin air (that would be an orphan entry in the cache).
 */
export function updateCachedDetail<T>(
  queryClient: QueryClient,
  queryKey: QueryKey,
  updater: (detail: T) => T,
): boolean {
  const cached = queryClient.getQueryData(queryKey);

  if (cached === undefined) return false;

  queryClient.setQueryData(queryKey, updater(cached as T));

  return true;
}

/** Removes ONE entry, exactly. It never removes a family by prefix. */
export function removeCachedEntry(
  queryClient: QueryClient,
  queryKey: QueryKey,
): void {
  queryClient.removeQueries({ queryKey, exact: true });
}
