"use client";

import { useMutation } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";
import type { Cotizacion } from "../schemas/cotizacion.schema";
import { cotizarPaquete } from "../services/cotizacion.service";

/**
 * The hook of the QUOTATION of the selected package.
 *
 * ## Why the quotation lives in local state
 *
 * The quotation is EPHEMERAL: it belongs to the wizard session and to the
 * quantity that is currently selected. It is not a dataset of the server, so
 * it does not live in the cache of TanStack Query (which holds the reads that
 * the server owns).
 *
 * ## Why there is ONE instance
 *
 * One quotation belongs to ONE package AND ONE quantity. Keeping it per card
 * would duplicate the mutations and would let a stale card overwrite a fresh
 * quotation, so the whole picker shares this single instance.
 *
 * ## The sequence guard
 *
 * Two quotations can be in flight at once (the visitor changes the quantity
 * while a request is travelling). Without the guard the slowest answer wins
 * and the card shows a price that belongs to another quantity, so only the
 * NEWEST request may write the state.
 */
export function useCotizacion() {
  const [cotizacion, setCotizacion] = useState<Cotizacion | null>(null);

  /**
   * The sequence of the requests: only the newest one may write the state.
   */
  const secuencia = useRef(0);

  const mutation = useMutation<
    Cotizacion,
    Error,
    { paquete_id: string; cantidad: number }
  >({
    mutationFn: async (payload) => {
      const respuesta = await cotizarPaquete(payload);
      return respuesta.data;
    },
  });

  /**
   * Ask the server for the quotation of a package and a quantity.
   *
   * It depends on `mutation.mutate` (a stable reference in TanStack Query
   * v5), NOT on the `mutation` object: that object is new on every render and
   * depending on it would re-create `cotizar` on every render, which in turn
   * would re-trigger the effect of the consumer that calls it, and that would
   * be an infinite loop.
   */
  const cotizar = useCallback(
    (paqueteId: string, cantidad: number) => {
      const numero = ++secuencia.current;
      mutation.mutate(
        { paquete_id: paqueteId, cantidad },
        {
          onSuccess: (data) => {
            if (numero !== secuencia.current) return;
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
   * It is used when the selected package or the quantity changes: the
   * quotation belongs to the previous combination and it must not be shown
   * (nor written to the form) until the new one arrives.
   */
  const invalidar = useCallback(() => {
    secuencia.current += 1;
    setCotizacion(null);
  }, []);

  return {
    /** The last quotation that the server answered. */
    cotizacion,
    /** Whether the server already declared the quotation expired. */
    estaExpirada: cotizacion?.estado === "EXPIRADA",
    /** Whether a request is travelling. */
    estaCargando: mutation.isPending,
    /** Whether the last request failed. */
    hayError: mutation.isError,
    /** The error of the last request, verbatim. */
    error: mutation.error,
    /** Ask the server for the quotation of a package and a quantity. */
    cotizar,
    /** Drop the current quotation. */
    invalidar,
  };
}
