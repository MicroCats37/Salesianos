"use client";

import { type UseQueryResult, useQuery } from "@tanstack/react-query";
import {
  getInscripcionDetalle,
  type InscripcionDetalleOut,
} from "../services/inscripcion.service";

/**
 * Stable query key for a given inscripcion detail.
 *
 * Use this everywhere you read/update the cache to avoid key mismatches.
 */
export function inscripcionDetalleKey(inscripcionId: string) {
  return ["inscripcion-detalle", inscripcionId] as const;
}

interface UseInscripcionDetalleOptions {
  /** Disable the query until this is truthy (e.g. once we know the id). */
  enabled?: boolean;
}

/**
 * Query hook for the detail of one inscripcion.
 *
 * - `staleTime` of 30s so navigating away and back doesn't trigger a refetch.
 * - `refetchOnWindowFocus: false` to avoid flicker when the user alt-tabs.
 * - Cache is shared across the app via the QueryClient, so other pages
 *   (e.g. wizard confirmations) can pre-warm it before we land here.
 *
 * For per-mutation cache updates see `useInscripcionDetalleCacheSync`.
 */
export function useInscripcionDetalle(
  inscripcionId: string,
  { enabled = true }: UseInscripcionDetalleOptions = {},
): UseQueryResult<InscripcionDetalleOut, Error> {
  return useQuery<InscripcionDetalleOut, Error>({
    queryKey: inscripcionDetalleKey(inscripcionId),
    queryFn: async () => {
      const res = await getInscripcionDetalle(inscripcionId);
      if (!res.success || !res.data) {
        throw new Error(res.error?.message ?? "Error al cargar la inscripción");
      }
      return res.data;
    },
    enabled: enabled && !!inscripcionId,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}
