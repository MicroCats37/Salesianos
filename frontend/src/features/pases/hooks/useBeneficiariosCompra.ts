"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import { fetchBeneficiariosCompra } from "../services";

/**
 * Query options of the nominative rights of ONE batch.
 *
 * The state of the rights is the authoritative one: the browser never derives
 * it from the purchase summary.
 */
export function paseBeneficiariosQueryOptions(compraId: string | null) {
  return queryOptions({
    queryKey: ["pases", "beneficiarios", compraId ?? ""],
    queryFn: async () => {
      if (!compraId) {
        throw new Error("compraId es obligatorio");
      }
      return fetchBeneficiariosCompra(compraId);
    },
    enabled: Boolean(compraId),
    staleTime: 15 * 1000,
  });
}

/** The rights of a batch, with the immutable slot accounting. */
export function useBeneficiariosCompra(compraId: string | null) {
  return useQuery(paseBeneficiariosQueryOptions(compraId));
}
