"use client";

import { api } from "@/lib/api";
import type { ApiResponse } from "@/types/api.types";
import type {
  CotizacionRequest,
  CotizacionResponse,
} from "../schemas/cotizacion.schema";

/**
 * Fetch a quotation for a package and quantity.
 * POST /api/cotizaciones/
 */
export async function cotizarPaquete(
  payload: CotizacionRequest,
): Promise<ApiResponse<CotizacionResponse>> {
  const { data } = await api.post<ApiResponse<CotizacionResponse>>(
    "/cotizaciones/",
    payload,
  );
  return data;
}
