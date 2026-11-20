import { type QueryKey, queryOptions } from "@tanstack/react-query";

/**
 * The staleness of each KIND of dataset.
 *
 * From the data contract: catalogues 5-10 min, administrative lists 30 s,
 * commercial/transient state 15 s, live previews 0.
 */
export const STALE_TIME = {
  catalogo: 10 * 60 * 1000,
  listadoAdministrativo: 30 * 1000,
  comercial: 15 * 1000,
  vivo: 0,
} as const;

export type DatasetKind = keyof typeof STALE_TIME;

/**
 * The minimum lifetime of a cached entry that nobody is looking at.
 *
 * Money and eligibility must not disappear from the cache while the operator
 * is looking at the screen.
 */
export const MIN_GC_TIME = 5 * 60 * 1000;

/**
 * `gcTime` is NEVER shorter than `staleTime` and NEVER shorter than five
 * minutes.
 */
export function gcTimeFor(staleTime: number): number {
  return Math.max(staleTime, MIN_GC_TIME);
}

export interface DatasetQueryOptionsInput<TData> {
  /** The key of the read: the namespace of the dataset plus its parameters. */
  queryKey: QueryKey;
  queryFn: () => Promise<TData>;
  /** The kind of dataset, which decides the staleness when none is declared. */
  kind?: DatasetKind;
  staleTime?: number;
  gcTime?: number;
}

/**
 * The `queryOptions` of a read.
 *
 * EVERY read of the target exports its options through this factory: the
 * staleness policy lives in ONE place and the same options can be used by
 * `useQuery`, by `queryClient.fetchQuery` and by the server-side prefetch.
 */
export function datasetQueryOptions<TData>({
  queryKey,
  queryFn,
  kind = "comercial",
  staleTime,
  gcTime,
}: DatasetQueryOptionsInput<TData>) {
  const resolvedStaleTime = staleTime ?? STALE_TIME[kind];

  return queryOptions({
    queryKey,
    queryFn,
    staleTime: resolvedStaleTime,
    gcTime: gcTime ?? gcTimeFor(resolvedStaleTime),
  });
}
