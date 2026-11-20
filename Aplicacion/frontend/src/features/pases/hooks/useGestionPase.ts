"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { invalidateDatasets } from "@/shared/utils/cache-policy";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import type { AsignacionPaseData } from "../schemas/comprador-pase.schema";
import {
  asignarBeneficiario,
  obtenerCompra,
  revocarBeneficiario,
} from "../services/pase.service";
import { paseClaves } from "../utils/pase.claves.utils";
import { aPayloadAsignarBeneficiario } from "../utils/pase.payload.utils";

/**
 * The purchase of a batch, opened with the private token (`RT-PS-03`).
 *
 * The token is the CREDENTIAL of the link: it travels in the `X-Pase-Token`
 * header and never in the query string. Without it the answer is 401 and the
 * batch is never exposed.
 *
 * The read is DISABLED when there is no identifier or no token: the frontend
 * never calls a route it cannot open, and it never shows an order it did not
 * read.
 */
export function useCompraPaseDetalle(
  compraPaseId: string | undefined,
  token: string | undefined,
) {
  return useQuery({
    ...datasetQueryOptions({
      queryKey: paseClaves.compra(compraPaseId ?? ""),
      queryFn: () => obtenerCompra(compraPaseId as string, token as string),
      kind: "comercial",
    }),
    enabled: Boolean(compraPaseId) && Boolean(token),
  });
}

/**
 * The assignment of a pass to a person (`RT-PS-05`).
 *
 * The assignment only works on PAID capacity: a pending batch has no passes
 * to share (`RN-P02`), and the server answers 409 when the race is lost.
 *
 * The invalidation is EXACT: it dirties the purchase and its beneficiaries,
 * and nothing else. The answer of the server is the truth about the batch:
 * the browser never writes the new right into the cache by itself.
 */
export function useAsignarBeneficiario(
  compraPaseId: string,
  token: string,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (datos: AsignacionPaseData) => {
      try {
        return await asignarBeneficiario(
          compraPaseId,
          token,
          aPayloadAsignarBeneficiario(datos),
        );
      } finally {
        await invalidateDatasets(queryClient, [paseClaves.compra(compraPaseId)]);
      }
    },
  });
}

/**
 * The revocation of an entry right (`RT-RT-03`).
 *
 * The revocation is IRREVERSIBLE and IDEMPOTENT: a right already revoked
 * answers 200 with `ya_revocado = true`, never an error.
 */
export function useRevocarBeneficiario(
  compraPaseId: string,
  token: string,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (datos: { persona_id: string; motivo?: string }) => {
      try {
        return await revocarBeneficiario(
          compraPaseId,
          token,
          datos.persona_id,
          datos.motivo,
        );
      } finally {
        await invalidateDatasets(queryClient, [paseClaves.compra(compraPaseId)]);
      }
    },
  });
}
