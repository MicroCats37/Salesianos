"use client";

import {
  type AdminPagoDetalleEnvelope,
  AdminPagoDetalleEnvelopeSchema,
  type AdminPagoListadoEnvelope,
  AdminPagoListadoEnvelopeSchema,
} from "../schemas";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";
import { adminGet } from "./admin.http.service";

/**
 * AdminPagoService — the payments table (A5) and its drilldown (A6).
 *
 * Endpoints:
 * - GET /api/administracion/pagos             (A5)
 * - GET /api/administracion/pagos/{orden_pago_id} (A6)
 *
 * The amounts come from the FROZEN commercial snapshot of the purchase, and
 * the wrapper NEVER carries `metadata`, `token_sesion`, `response_message` nor
 * `transaction_id`.
 */

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
