"use client";

import { useMutation } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";
import type {
  CotizacionRequest,
  CotizacionResponse,
} from "../schemas/cotizacion.schema";
import { cotizarPaquete } from "../services/cotizacion.service";

/**
 * Hook for managing the quotation of the selected package.
 *
 * The quotation lives in local state (not in the TanStack Query cache) because
 * it is ephemeral — it belongs to the current wizard session and to the
 * quantity currently selected.
 *
 * IMPORTANT: there is a SINGLE instance of this hook for the whole package
 * picker. One quote belongs to one package + quantity, so keeping it per card
 * would duplicate mutations and let a stale card overwrite the fresh quote.
 */
export function useCotizacion() {
  const [cotizacion, setCotizacion] = useState<CotizacionResponse | null>(null);

  /**
   * Sequence guard: only the newest request may write the state.
   *
   * Two quotes can be in flight at once (the user switches package while a
   * request is running). Without the guard the slowest response wins and the
   * card shows a price that belongs to another package.
   */
  const requestSeq = useRef(0);

  const mutation = useMutation<CotizacionResponse, Error, CotizacionRequest>({
    mutationFn: async (payload) => {
      const response = await cotizarPaquete(payload);
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Error al cotizar");
      }
      return response.data;
    },
  });

  /**
   * Request a quotation for the given package and quantity.
   *
   * NOTE: depends on `mutation.mutate` (a stable reference in TanStack Query
   * v5), NOT on the `mutation` object — that object is new on every render and
   * depending on it would re-create `cotizar` each render, which in turn
   * re-triggers the consumer effect that calls it, producing an infinite loop.
   */
  const cotizar = useCallback(
    (paquete_id: string, cantidad: number) => {
      const seq = ++requestSeq.current;
      mutation.mutate(
        { paquete_id, cantidad },
        {
          onSuccess: (data) => {
            if (seq !== requestSeq.current) return;
            setCotizacion(data);
          },
        },
      );
    },
    [mutation.mutate],
  );

  /**
   * Drop the current quotation.
   *
   * Used when the selected package changes: the quote belongs to the previous
   * package and must not be shown (nor written to the form) until the new one
   * arrives.
   */
  const invalidate = useCallback(() => {
    requestSeq.current += 1;
    setCotizacion(null);
  }, []);

  return {
    cotizacion,
    /**
     * The backend already tells whether the quote is still usable — no need to
     * poll the clock and re-render the cards every 30 seconds.
     */
    isExpired: cotizacion?.estado === "EXPIRADA",
    isLoading: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
    cotizar,
    invalidate,
  };
}
