"use client";

import { useApiCreate, useApiDelete, useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import type { AsignacionPaseData } from "../schemas/comprador-pase.schema";
import {
  type BeneficiarioRevocado,
  type BeneficiariosPase,
  beneficiarioRevocadoEnvelope,
  beneficiariosPaseEnvelope,
  CABECERA_TOKEN_PASE,
  compraPasesEnvelope,
} from "../schemas/pase.schema";
import {
  rutaBeneficiario,
  rutaBeneficiarios,
  rutaCompraDetalle,
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
  return useApiQuery({
    queryKey: paseClaves.compra(compraPaseId ?? ""),
    url: compraPaseId ? rutaCompraDetalle(compraPaseId) : null,
    schema: datosDelEnvelope(compraPasesEnvelope),
    config: token ? { headers: { [CABECERA_TOKEN_PASE]: token } } : undefined,
    queryOptions: {
      enabled: Boolean(compraPaseId) && Boolean(token),
      staleTime: STALE_TIME.comercial,
      gcTime: gcTimeFor(STALE_TIME.comercial),
    },
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
export function useAsignarBeneficiario(compraPaseId: string, token: string) {
  const mutacion = useApiCreate({
    url: rutaBeneficiarios(compraPaseId),
    schema: datosDelEnvelope(beneficiariosPaseEnvelope),
    config: { headers: { [CABECERA_TOKEN_PASE]: token } },
    invalidateKeys: [paseClaves.compra(compraPaseId)],
  });

  return {
    ...mutacion,
    mutateAsync: (datos: AsignacionPaseData) =>
      mutacion.mutateAsync(aPayloadAsignarBeneficiario(datos)),
  };
}

/**
 * The revocation of an entry right (`RT-RT-03`).
 *
 * The revocation is IRREVERSIBLE and IDEMPOTENT: a right already revoked
 * answers 200 with `ya_revocado = true`, never an error.
 */
export function useRevocarBeneficiario(compraPaseId: string, token: string) {
  const mutacion = useApiDelete<
    BeneficiarioRevocado,
    { persona_id: string; motivo?: string }
  >({
    getUrl: (variables) =>
      `${rutaBeneficiario(compraPaseId, variables.persona_id)}${
        variables.motivo
          ? `?motivo=${encodeURIComponent(variables.motivo)}`
          : ""
      }`,
    schema: datosDelEnvelope(beneficiarioRevocadoEnvelope),
    config: { headers: { [CABECERA_TOKEN_PASE]: token } },
    invalidateKeys: [paseClaves.compra(compraPaseId)],
  });

  return {
    ...mutacion,
    mutateAsync: (datos: { persona_id: string; motivo?: string }) =>
      mutacion.mutateAsync(datos),
  };
}

export type { BeneficiariosPase };
