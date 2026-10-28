"use client";

import {
  type QueryClient,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type {
  AdminPagoAnularManualEnvelope,
  AdminPagoAnularManualFormData,
  AdminPagoAnularManualPayload,
  AdminPagoAprobarManualEnvelope,
  AdminPagoAprobarManualFormData,
  AdminPagoAprobarManualPayload,
} from "../schemas";
import {
  anularPagoManual,
  aprobarPagoManual,
} from "../services/admin.pago.service";

/**
 * The mutations of the payments — TanStack Query owns EVERY piece of server
 * state, including the writes.
 *
 * The PAYLOAD is built HERE, never in the form component: the form only
 * collects what the administrator typed
 * (`contract/next-app-architecture-contract.md` §5).
 */

/** Variables of the administrative approval of a manual payment. */
export interface VariablesAprobarPagoManual {
  ordenPagoId: string;
  datos: AdminPagoAprobarManualFormData;
}

/** Variables of the administrative annulment of a manual approval. */
export interface VariablesAnularPagoManual {
  ordenPagoId: string;
  datos: AdminPagoAnularManualFormData;
}

/** Build the API body of the manual approval. */
export function construirPayloadAprobarManual(
  datos: AdminPagoAprobarManualFormData,
): AdminPagoAprobarManualPayload {
  return {
    canal: datos.canal,
    referencia: datos.referencia.trim(),
    monto: Number(datos.monto),
    moneda: datos.moneda.trim().toUpperCase(),
    motivo: datos.motivo.trim(),
  };
}

/** Build the API body of the annulment of a manual approval. */
export function construirPayloadAnularManual(
  datos: AdminPagoAnularManualFormData,
): AdminPagoAnularManualPayload {
  return { motivo: datos.motivo.trim() };
}

/**
 * Invalidate the reads that the decision changes.
 *
 * The list carries its filters in its key, so it is invalidated by its
 * prefix: every variant of it is refreshed. The drilldown is invalidated
 * with its EXACT key, and the overview because the paid totals moved.
 */
export async function invalidarLecturasPago(
  queryClient: QueryClient,
  ordenPagoId: string,
): Promise<void> {
  await Promise.all([
    queryClient.invalidateQueries({
      queryKey: ["admin", "pagos"],
      exact: false,
    }),
    queryClient.invalidateQueries({
      queryKey: ["admin", "pago", ordenPagoId],
      exact: true,
    }),
    queryClient.invalidateQueries({
      queryKey: ["admin", "resumen"],
      exact: true,
    }),
  ]);
}

/** Approve a payment received outside the payment provider. */
export function useAprobarPagoManual() {
  const queryClient = useQueryClient();
  return useMutation<
    AdminPagoAprobarManualEnvelope,
    ApiQueryError,
    VariablesAprobarPagoManual
  >({
    mutationFn: async (variables: VariablesAprobarPagoManual) =>
      aprobarPagoManual(
        variables.ordenPagoId,
        construirPayloadAprobarManual(variables.datos),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasPago(queryClient, variables.ordenPagoId);
    },
  });
}

/** Annul the manual approval of a payment order. */
export function useAnularPagoManual() {
  const queryClient = useQueryClient();
  return useMutation<
    AdminPagoAnularManualEnvelope,
    ApiQueryError,
    VariablesAnularPagoManual
  >({
    mutationFn: async (variables: VariablesAnularPagoManual) =>
      anularPagoManual(
        variables.ordenPagoId,
        construirPayloadAnularManual(variables.datos),
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasPago(queryClient, variables.ordenPagoId);
    },
  });
}
