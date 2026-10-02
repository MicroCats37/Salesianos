"use client";

/**
 * Payment service — calls Django backend Izipay endpoints via the existing api wrapper.
 *
 * Endpoints:
 *   GET  /pagos/izipay/preparar/{inscripcion_id}
 *   POST /pagos/izipay/confirmar
 *
 * No secrets are sent from the frontend. All sensitive data (buyer info, amount)
 * is derived server-side from the authenticated user's Persona record.
 */

import { api } from "@/lib/api";
import type {
  IzipayConfirmIn,
  IzipayPrepareResponse,
  IzipayConfirmResponse,
} from "../schemas/pago.schema";

/**
 * Prepare an Izipay payment session for an inscription.
 * The backend validates ownership and derives all buyer/amount data server-side.
 */
export async function prepararPagoIzipay(
  inscripcionId: string,
): Promise<IzipayPrepareResponse> {
  const { data } = await api.get<IzipayPrepareResponse>(
    `/pagos/izipay/preparar/${inscripcionId}`,
  );
  return data;
}

/**
 * Confirm an Izipay payment from the frontend SDK callback (kr_answer).
 * Idempotent — already-confirmed transactions return success without re-processing.
 */
export async function confirmarPagoIzipay(
  payload: IzipayConfirmIn,
): Promise<IzipayConfirmResponse> {
  const { data } = await api.post<IzipayConfirmResponse>(
    "/pagos/izipay/confirmar",
    payload,
  );
  return data;
}
