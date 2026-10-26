/**
 * TypeScript mirrors of the backend Izipay HTTP contracts.
 *
 * Source of truth (backend):
 *   - `modules/pagos/presentation/schemas/pago_schema.py`
 *   - `modules/salesianos_fest/presentation/schemas/compra_schemas.py`
 *
 * These types mirror the backend wrappers 1:1 — no `z.any()` and no
 * `Record<string, unknown>` for a whole payload
 * (see `contract/api-wrapper-presenter-contract.md` §7).
 */

import type { ApiResponse } from "@/types/api.types";

// ── Provider callback payload (POST /pagos/izipay/confirmar) ──────────────────
//
// The provider owns the shape of its own payload: the backend models accept
// unknown fields (`extra="allow"`) and keep them for the audit metadata.
// The index signature expresses that pass-through WITHOUT degrading the known
// fields to `any`.

/** One order entry of the provider payload — backend `IzipayOrdenDetalleIn`. */
export interface IzipayOrdenDetalle {
  /** Provider order number. */
  orderNumber?: string | null;
  /** Amount of the order. */
  amount?: string | null;
  /** Currency of the order. */
  currency?: string | null;
  /** Extra provider fields (preserved, never interpreted by the frontend). */
  [key: string]: unknown;
}

/** The `response` bag of the provider payload — backend `IzipayRespuestaIn`. */
export interface IzipayRespuesta {
  /** Payment method used. */
  payMethod?: string | null;
  /** Alternative name of the payment method. */
  paymentMethodType?: string | null;
  /** Transaction id reported inside the response bag. */
  transactionId?: string | null;
  /** Orders covered by the transaction. */
  order?: IzipayOrdenDetalle[];
  /** Extra provider fields (preserved, never interpreted by the frontend). */
  [key: string]: unknown;
}

/**
 * The provider payload delivered by the Izipay Perú frontend SDK.
 *
 * Mirrors backend `IzipayCallbackIn`. The whole object is relayed to the
 * backend so it can verify the provider signature over `payloadHttp` and
 * cross-check the amount/order against the persisted transaction.
 */
export interface IzipayCallback {
  /** Provider response code — "00" means approved. */
  code: string;
  /** Provider response message. */
  message?: string | null;
  /** Provider transaction id. */
  transactionId?: string | null;
  /** Provider order number. */
  orderNumber?: string | null;
  /** Provider amount. */
  amount?: string | null;
  /** HMAC-SHA256 signature of `payloadHttp` (Base64). */
  signature?: string | null;
  /** Raw signed payload of the provider. */
  payloadHttp?: string | null;
  /** Provider response bag. */
  response?: IzipayRespuesta | null;
  /** Extra provider fields (preserved, never interpreted by the frontend). */
  [key: string]: unknown;
}

// ── Confirm (POST /pagos/izipay/confirmar) ───────────────────────────────────

/** Request body of the browser relay — backend `IzipayConfirmIn`. */
export interface IzipayConfirmIn {
  /** The provider payload (`kr_answer`) delivered by the SDK. */
  kr_answer: IzipayCallback;
}

/**
 * Commercial settlement state of the paid order.
 *
 * Mirrors backend `SettlementStatus`:
 *   - `SETTLED` — the purchase is paid and its rights are allocated.
 *   - `PENDING` — the payment is recorded but the settlement is not complete.
 *   - `NOT_APPLICABLE` — there was no settlement to perform.
 */
export type SettlementStatus = "SETTLED" | "PENDING" | "NOT_APPLICABLE";

/** Output of the browser relay — backend `IzipayConfirmOut`. */
export interface IzipayConfirmOut {
  /** Provider transaction id (the idempotency key). */
  transaction_id: string;
  /** Whether the payment succeeded. */
  success: boolean;
  /** `TransaccionPago` status: EXITO, FALLIDO, CANCELADO. */
  status: string;
  /** `OrdenPago` UUID (available after a successful payment). */
  orden_pago_id: string | null;
  /** Provider response code (`code` from the relayed payload). */
  response_code: string | null;
  /** Provider response message. */
  response_message: string | null;
  /** Payment method used (e.g. CARD, YAPE, PLIN). */
  metodo_pago: string | null;
  /** True when the transaction was already confirmed (idempotent hit). */
  already_confirmed: boolean;
  /** Commercial settlement state of the paid order. */
  settlement_status: SettlementStatus;
}

export type IzipayConfirmResponse = ApiResponse<IzipayConfirmOut>;

// ── Start checkout (POST /compras/{compra_id}/iniciar-pago) ───────────────────

/**
 * Output of starting the checkout — backend `IniciarPagoOut`.
 *
 * It carries the SDK configuration (token, merchant code, order number,
 * amount). No secret travels here: the token is the provider session token
 * of the popup, not an API key.
 */
export interface IniciarPagoOut {
  /** `commerce.Compra` UUID. */
  compra_id: string;
  /** `OrdenPago` UUID. */
  orden_pago_id: string;
  /** 14-digit transaction id. */
  transaction_id: string;
  /** 10-digit order number. */
  order_number: string;
  /** Izipay Perú session token for the SDK popup. */
  token: string;
  /** Izipay Perú merchant/shop code. */
  merchant_code: string;
  /** Total amount of the order. */
  amount: number;
  /** ISO currency code. */
  currency: string;
  /** Buyer email passed to the provider. */
  buyer_email: string;
  /** Buyer first name passed to the provider (sanitized). */
  buyer_name: string;
  /** Buyer last name passed to the provider (sanitized). */
  buyer_surname: string;
}

export type IniciarPagoResponse = ApiResponse<IniciarPagoOut>;
