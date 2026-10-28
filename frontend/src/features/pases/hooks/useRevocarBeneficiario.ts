"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { notify } from "@/errors";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type { PaseBeneficiarioRevocado } from "../schemas";
import { revocarBeneficiarioCompra } from "../services";
import { invalidarLecturasBeneficiarios } from "./useAsignarBeneficiarios";

/**
 * The mutation that revokes a right PERMANENTLY.
 *
 * The revocation is NOT a transfer: the slot is consumed forever and the
 * right never moves to somebody else.
 */

/** Variables of the revocation. */
export interface VariablesRevocarBeneficiario {
  /** The batch that owns the right. */
  compraId: string;
  /** The person that holds the right. */
  personaId: string;
  /** The audited motive — mandatory. */
  motivo: string;
}

/** Build the API body of the revocation. */
export function construirPayloadRevocarBeneficiario(motivo: string): {
  motivo: string;
} {
  return { motivo: motivo.trim() };
}

/** Revoke the right of a person, permanently. */
export function useRevocarBeneficiario() {
  const queryClient = useQueryClient();

  return useMutation<
    PaseBeneficiarioRevocado,
    ApiQueryError,
    VariablesRevocarBeneficiario
  >({
    mutationFn: (variables) =>
      revocarBeneficiarioCompra(
        variables.compraId,
        variables.personaId,
        construirPayloadRevocarBeneficiario(variables.motivo).motivo,
      ),
    onSuccess: async (_resultado, variables) => {
      await invalidarLecturasBeneficiarios(queryClient, variables.compraId);
      notify.success(
        "El pase del beneficiario se revocó. El slot queda consumido.",
      );
    },
    onError: (error) => {
      notify.error(error.message);
    },
  });
}
