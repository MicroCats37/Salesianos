/**
 * TypeScript types mirroring the backend IzipayPrepareOut and IzipayConfirmOut schemas.
 * These match backend/modules/pagos/presentation/schemas/pago_schema.py exactly.
 */

import type { ApiResponse } from "@/types/api.types";

// ── Prepare (GET /pagos/izipay/preparar/{inscripcion_id}) ──────────────────

export interface IzipayPrepareOut {
  transaction_id: string;
  order_number: string;
  token: string;
  merchant_code: string;
  amount: string;
  currency: string;
  buyer_email: string;
  buyer_name: string;
  buyer_surname: string;
}

export type IzipayPrepareResponse = ApiResponse<IzipayPrepareOut>;

// ── Confirm (POST /pagos/izipay/confirmar) ──────────────────────────────────

export interface IzipayConfirmIn {
  kr_answer: Record<string, unknown>;
}

export interface IzipayConfirmOut {
  transaction_id: string;
  success: boolean;
  status: string;
  response_code: string | null;
  response_message: string | null;
  metodo_pago: string | null;
  already_confirmed: boolean;
}

export type IzipayConfirmResponse = ApiResponse<IzipayConfirmOut>;
