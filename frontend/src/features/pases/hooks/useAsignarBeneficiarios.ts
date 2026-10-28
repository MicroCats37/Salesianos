"use client";

import {
  type QueryClient,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { notify } from "@/errors";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type { PaseBeneficiariosAsignados, PersonaResuelta } from "../schemas";
import { asignarBeneficiariosCompra } from "../services";

/**
 * The mutation that assigns persons to the free slots of a batch.
 *
 * The PAYLOAD is built HERE, never in the form component: the form only
 * collects the persons that already exist
 * (`contract/next-app-architecture-contract.md` §5).
 */

/** Variables of the assignment. */
export interface VariablesAsignarBeneficiarios {
  /** The batch that receives the rights. */
  compraId: string;
  /** The persons that already exist and were selected by the buyer. */
  personas: PersonaResuelta[];
}

/**
 * Build the API body of the assignment.
 *
 * The body carries ONLY the ids: the API never receives names, documents or
 * any other datum of the person.
 */
export function construirPayloadAsignarBeneficiarios(
  personas: PersonaResuelta[],
): { beneficiario_ids: string[] } {
  return { beneficiario_ids: personas.map((persona) => persona.persona_id) };
}

/**
 * Invalidate the reads that the assignment changes.
 *
 * The rights of the batch AND the commercial state of the purchase move: the
 * purchase reports how many rights are assigned and how many slots are free.
 */
export async function invalidarLecturasBeneficiarios(
  queryClient: QueryClient,
  compraId: string,
): Promise<void> {
  await Promise.all([
    queryClient.invalidateQueries({
      queryKey: ["pases", "beneficiarios", compraId],
      exact: true,
    }),
    queryClient.invalidateQueries({
      queryKey: ["pases", "compra", compraId],
      exact: true,
    }),
  ]);
}

/** Assign persons to the free slots of a paid batch. */
export function useAsignarBeneficiarios() {
  const queryClient = useQueryClient();

  return useMutation<
    PaseBeneficiariosAsignados,
    ApiQueryError,
    VariablesAsignarBeneficiarios
  >({
    mutationFn: (variables) =>
      asignarBeneficiariosCompra(
        variables.compraId,
        construirPayloadAsignarBeneficiarios(variables.personas)
          .beneficiario_ids,
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasBeneficiarios(queryClient, variables.compraId);
      notify.success("Los beneficiarios se asignaron correctamente.");
    },
    onError: (error) => {
      notify.error(error.message);
    },
  });
}
