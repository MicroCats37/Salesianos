"use client";

import { z } from "zod";
import { handleApiError } from "@/errors";
import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { api } from "@/lib/api";
import {
  type AdminPagoAnularManualEnvelope,
  AdminPagoAnularManualEnvelopeSchema,
  type AdminPagoAnularManualPayload,
  AdminPagoAnularManualPayloadSchema,
  type AdminPagoAprobarManualEnvelope,
  AdminPagoAprobarManualEnvelopeSchema,
  type AdminPagoAprobarManualPayload,
  AdminPagoAprobarManualPayloadSchema,
  type AdminPagoDetalleEnvelope,
  AdminPagoDetalleEnvelopeSchema,
  type AdminPagoListadoEnvelope,
  AdminPagoListadoEnvelopeSchema,
} from "../schemas";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";
import { adminGet } from "./admin.http.service";

/**
 * AdminPagoService — the payments table (A5), its drilldown (A6) and the
 * administrative approval / annulment of a manual payment.
 *
 * Endpoints:
 * - GET  /api/administracion/pagos                          (A5)
 * - GET  /api/administracion/pagos/{orden_pago_id}           (A6)
 * - POST /api/administracion/pagos/{orden_pago_id}/aprobar-manual
 * - POST /api/administracion/pagos/{orden_pago_id}/anular-manual
 *
 * The amounts come from the FROZEN commercial snapshot of the purchase, and
 * the wrapper NEVER carries `metadata`, `token_sesion`, `response_message` nor
 * `transaction_id`.
 */

/** The public message of a drifted contract. */
const MENSAJE_CONTRATO =
  "La respuesta del servidor no coincide con el contrato de la vista de administración.";

/**
 * Send ONE command and validate its answer.
 *
 * The transport is local to this module on purpose: the shared transport of
 * the administration area only knows how to READ, and this module owns its
 * own writes.
 */
async function enviar<TEnvelope>(
  metodo: "post",
  url: string,
  esquema: z.ZodType<TEnvelope>,
  cuerpo?: unknown,
): Promise<TEnvelope> {
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

/** Page of the payments of the active event. */
export async function getAdminPagos(
  estado: AdminEstadoLista,
): Promise<AdminPagoListadoEnvelope> {
  return adminGet(
    "/administracion/pagos",
    AdminPagoListadoEnvelopeSchema,
    adminParametrosConsulta(estado),
  );
}

/** Drilldown of one payment order of the active event. */
export async function getAdminPagoDetalle(
  ordenPagoId: string,
): Promise<AdminPagoDetalleEnvelope> {
  return adminGet(
    `/administracion/pagos/${ordenPagoId}`,
    AdminPagoDetalleEnvelopeSchema,
  );
}

/** Approve a payment received outside the payment provider. */
export async function aprobarPagoManual(
  ordenPagoId: string,
  cuerpo: AdminPagoAprobarManualPayload,
): Promise<AdminPagoAprobarManualEnvelope> {
  return enviar(
    "post",
    `/administracion/pagos/${ordenPagoId}/aprobar-manual`,
    AdminPagoAprobarManualEnvelopeSchema,
    AdminPagoAprobarManualPayloadSchema.parse(cuerpo),
  );
}

/** Annul the manual approval of a payment order. */
export async function anularPagoManual(
  ordenPagoId: string,
  cuerpo: AdminPagoAnularManualPayload,
): Promise<AdminPagoAnularManualEnvelope> {
  return enviar(
    "post",
    `/administracion/pagos/${ordenPagoId}/anular-manual`,
    AdminPagoAnularManualEnvelopeSchema,
    AdminPagoAnularManualPayloadSchema.parse(cuerpo),
  );
}
