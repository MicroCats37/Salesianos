"use client";

import type { AxiosError } from "axios";
import { z } from "zod";
import { getErrorMessage } from "@/errors";
import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { api } from "@/lib/api";

/**
 * Shared transport of the administration area.
 *
 * Every admin endpoint answers the SAME envelope — `{ success, data, error,
 * message }` — and every payload is validated against its 1:1 Zod mirror
 * BEFORE it leaves this module. A contract drift therefore fails loudly
 * instead of rendering `undefined` deep inside a table.
 *
 * Failures are shaped as `ApiQueryError` so the caller can react to the HTTP
 * status (403 → access denied) and not only to the message.
 */
export async function adminGet<TEnvelope>(
  url: string,
  schema: z.ZodType<TEnvelope>,
  params?: Record<string, string | number>,
): Promise<TEnvelope> {
  try {
    const { data } = await api.get(url, params ? { params } : undefined);
    return schema.parse(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ApiQueryError(
        "La respuesta del servidor no coincide con el contrato de la vista de administración.",
        undefined,
      );
    }

    const axiosError = error as AxiosError;
    throw new ApiQueryError(
      getErrorMessage(error),
      axiosError.response?.status,
    );
  }
}
