"use client";

import { z } from "zod";
import { handleApiError } from "@/errors";
import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { api } from "@/lib/api";
import {
  type AdminPaseCancelada,
  AdminPaseCanceladaEnvelopeSchema,
  type AdminPaseCancelarPayload,
  AdminPaseCancelarPayloadSchema,
} from "../schemas";

/**
 * AdminPaseService — the administrative operations over the party passes.
 *
 * Endpoint:
 *   POST /api/administracion/pases/compras/{compra_id}/cancelar
 *
 * The operation is NOT a monetary refund: it cancels the purchase and its
 * order and revokes the nominative rights that were delivered with them.
 */

/** The public message of a drifted contract. */
const MENSAJE_CONTRATO =
  "La respuesta del servidor no coincide con el contrato de los pases de fiesta.";

/**
 * Send ONE command and validate its answer.
 *
 * A drifted contract and a failed request are reported with the SAME error
 * type (`ApiQueryError`), so the view never has to know the transport.
 */
async function enviar<T>(
  metodo: "post",
  url: string,
  esquema: z.ZodType<T>,
  cuerpo?: unknown,
): Promise<T> {
  try {
    const respuesta = await api.request({ method: metodo, url, data: cuerpo });
    return esquema.parse(respuesta.data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ApiQueryError(MENSAJE_CONTRATO, undefined);
    }

    const { message, status } = handleApiError(error);
    throw new ApiQueryError(message, status);
  }
}

/**
 * Cancel a pass purchase (administrative).
 *
 * The purchase and its payment order are cancelled, the nominative rights it
 * funded are revoked (permanently) and the effective access of every affected
 * person is recomputed. The motive is mandatory and the decision is audited.
 */
export async function cancelarCompraPase(
  compraId: string,
  cuerpo: AdminPaseCancelarPayload,
): Promise<AdminPaseCancelada> {
  const envelope = await enviar(
    "post",
    `/administracion/pases/compras/${compraId}/cancelar`,
    AdminPaseCanceladaEnvelopeSchema,
    AdminPaseCancelarPayloadSchema.parse(cuerpo),
  );

  if (!envelope.success || !envelope.data) {
    throw new ApiQueryError(
      envelope.error?.message ??
        envelope.message ??
        "No se pudo cancelar la compra de pases.",
      undefined,
    );
  }

  return envelope.data;
}
