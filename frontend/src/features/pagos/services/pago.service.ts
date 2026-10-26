"use client";

/**
 * Payment service — calls the Django backend Izipay endpoints via the existing
 * api wrapper.
 *
 * Endpoints:
 *   POST /compras/{compra_id}/iniciar-pago  - open the provider checkout
 *   POST /pagos/izipay/confirmar            - relay the provider payload once
 *
 * No secrets are sent from the frontend. All sensitive data (buyer info,
 * amount) is derived server-side from the authenticated user's Persona record.
 *
 * The commercial settlement is NOT called from the browser: the backend owns
 * it. The relay is the only payment request the checkout performs.
 */

import { api } from "@/lib/api";
import type {
  IniciarPagoResponse,
  IzipayConfirmIn,
  IzipayConfirmResponse,
} from "../schemas/pago.schema";

/**
 * Open the Izipay checkout for a pending purchase.
 *
 * The backend validates the purchase state and derives every buyer/amount
 * value server-side, then returns the SDK configuration for the popup.
 */
export async function iniciarPagoIzipay(
  compraId: string,
): Promise<IniciarPagoResponse> {
  const { data } = await api.post<IniciarPagoResponse>(
    `/compras/${compraId}/iniciar-pago`,
  );
  return data;
}

/**
 * Relay the provider payload (`kr_answer`) to the verified payment endpoint.
 *
 * The endpoint requires an authenticated caller that owns the order and
 * cross-checks the payload against the persisted transaction. It is
 * idempotent: an already-confirmed transaction converges instead of
 * duplicating. The response reports the payment state AND the commercial
 * settlement state (`settlement_status`).
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
