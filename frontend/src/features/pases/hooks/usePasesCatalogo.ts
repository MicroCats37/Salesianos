"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import { fetchCatalogoPases, paseQueryKeys } from "../services";

/**
 * Query options of the public catalogue of the passes.
 *
 * The catalogue changes rarely — it is published by the administration — so it
 * stays fresh for a minute and lives in the cache for five.
 */
export const paseCatalogoQueryOptions = queryOptions({
  queryKey: paseQueryKeys.catalogo,
  queryFn: fetchCatalogoPases,
  staleTime: 60 * 1000,
  gcTime: 5 * 60 * 1000,
});

/**
 * The public catalogue of the passes that can be bought right now.
 *
 * The list is EMPTY while the rollout is off or when there is no active pass:
 * the view shows the empty state instead of inventing a catalogue.
 */
export function usePasesCatalogo() {
  return useQuery(paseCatalogoQueryOptions);
}
