"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notify } from "@/errors";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type { PaseCompraCreada, PaseComprarIn } from "../schemas";
import { crearCompraPase, paseQueryKeys } from "../services";

/**
 * The mutation of the purchase of a batch of passes.
 *
 * TanStack Query owns EVERY piece of server state, including the writes: the
 * component NEVER owns a value and NEVER validates by itself
 * (`contract/next-app-architecture-contract.md` §5).
 */

/**
 * Build the body of the purchase.
 *
 * The body carries ONLY the pass and the quantity: the price and the total are
 * ALWAYS computed by the server.
 */
export function construirPayloadCompraPase(datos: {
  pase_id: string;
  cantidad: number;
}): PaseComprarIn {
  return {
    pase_id: datos.pase_id,
    cantidad: Number(datos.cantidad),
  };
}

/**
 * Register the purchase of a batch of passes.
 *
 * The catalogue is invalidated because the inventory of the pass moves with
 * every purchase.
 */
export function useCrearCompraPase() {
  const queryClient = useQueryClient();

  return useMutation<PaseCompraCreada, ApiQueryError, PaseComprarIn>({
    mutationFn: (payload) => crearCompraPase(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: paseQueryKeys.catalogo,
        exact: false,
      });
    },
    onError: (error) => {
      notify.error(error.message);
    },
  });
}
