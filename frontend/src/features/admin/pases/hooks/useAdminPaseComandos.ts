"use client";

import {
  type QueryClient,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { notify } from "@/errors";
import { paseQueryKeys } from "@/features/pases/services";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type { AdminPaseCancelada, AdminPaseCancelarPayload } from "../schemas";
import { cancelarCompraPase } from "../services";

/**
 * The administrative commands over the party passes.
 *
 * TanStack Query owns EVERY piece of server state, including the writes: the
 * component NEVER owns a value and NEVER validates by itself
 * (`contract/next-app-architecture-contract.md` §5).
 */

/** Variables of the administrative cancellation of a pass purchase. */
export interface VariablesCancelarCompraPase {
  /** The purchase that is cancelled. */
  compraId: string;
  /** The payment order of the purchase — `null` when it has none. */
  ordenPagoId?: string | null;
  /** The audited motive — mandatory. */
  motivo: string;
}

/** Build the API body of the cancellation. */
export function construirPayloadCancelarCompraPase(
  motivo: string,
): AdminPaseCancelarPayload {
  return { motivo: motivo.trim() };
}

/**
 * Invalidate the reads that the cancellation changes.
 *
 * The payments table, the drilldown of the order, the overview and the state
 * of the purchase (the buyer sees the cancelled batch and its revoked rights).
 */
export async function invalidarLecturasPase(
  queryClient: QueryClient,
  variables: VariablesCancelarCompraPase,
): Promise<void> {
  await Promise.all([
    queryClient.invalidateQueries({
      queryKey: ["admin", "pagos"],
      exact: false,
    }),
    queryClient.invalidateQueries({
      queryKey: ["admin", "resumen"],
      exact: true,
    }),
    ...(variables.ordenPagoId
      ? [
          queryClient.invalidateQueries({
            queryKey: ["admin", "pago", variables.ordenPagoId],
            exact: true,
          }),
        ]
      : []),
    queryClient.invalidateQueries({
      queryKey: paseQueryKeys.compra(variables.compraId),
      exact: true,
    }),
    queryClient.invalidateQueries({
      queryKey: ["pases", "beneficiarios", variables.compraId],
      exact: true,
    }),
  ]);
}

/**
 * Cancel a pass purchase (administrative).
 *
 * The operation is NOT a monetary refund: it cancels the purchase and its
 * order and revokes the nominative rights that were delivered with them.
 */
export function useCancelarCompraPase() {
  const queryClient = useQueryClient();

  return useMutation<
    AdminPaseCancelada,
    ApiQueryError,
    VariablesCancelarCompraPase
  >({
    mutationFn: (variables) =>
      cancelarCompraPase(
        variables.compraId,
        construirPayloadCancelarCompraPase(variables.motivo),
      ),
    onSuccess: async (resultado, variables) => {
      await invalidarLecturasPase(queryClient, variables);
      notify.success(
        resultado.ya_cancelada
          ? "La compra de pases ya estaba cancelada."
          : `La compra de pases fue cancelada. Se revocaron ${resultado.beneficiarios_revocados} derecho(s) de pase.`,
      );
    },
    onError: (error) => {
      notify.error(error.message);
    },
  });
}
