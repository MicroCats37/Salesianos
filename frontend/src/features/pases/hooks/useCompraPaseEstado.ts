"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import { fetchCompraPase, paseQueryKeys } from "../services";

/**
 * Query options of the state of ONE pass purchase.
 *
 * The state is the authoritative commercial state: the browser reads it after
 * the payment and after every refresh, never the state it had before.
 */
export function paseCompraQueryOptions(compraId: string | null) {
  return queryOptions({
    queryKey: paseQueryKeys.compra(compraId ?? ""),
    queryFn: async () => {
      if (!compraId) {
        throw new Error("compraId es obligatorio");
      }
      return fetchCompraPase(compraId);
    },
    enabled: Boolean(compraId),
    staleTime: 15 * 1000,
  });
}

/** The state of a pass purchase — `null` while there is no purchase yet. */
export function useCompraPaseEstado(compraId: string | null) {
  return useQuery(paseCompraQueryOptions(compraId));
}
