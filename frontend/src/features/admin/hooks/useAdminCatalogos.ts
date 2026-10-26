"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import { getAdminCatalogos } from "../services/admin.resumen.service";

/**
 * AdminCatalogosQueryOptions — filter option lists of the active event.
 *
 * The catalogs are read once and barely change during an edition, so they are
 * cached for the whole session.
 */
export const adminCatalogosQueryOptions = queryOptions({
  queryKey: ["admin", "catalogos"] as const,
  queryFn: getAdminCatalogos,
  staleTime: 10 * 60 * 1000,
});

export function useAdminCatalogos() {
  return useQuery(adminCatalogosQueryOptions);
}
