"use client";

import type { AxiosError } from "axios";
import { getErrorMessage } from "@/errors";
import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { api } from "@/lib/api";
import { type AdminMeEnvelope, AdminMeEnvelopeSchema } from "../schemas";

/**
 * AdminMeService — revalidation of the session against the backend.
 *
 * Endpoint: GET /api/auth/me  (A0)
 *
 * The client NEVER trusts the `USER_SESSION` cookie as authority: it is a
 * non-httpOnly snapshot that nothing revalidates. The only authorization flag
 * the UI consumes is `es_admin`, and it is always read from this endpoint,
 * where the backend applies the project rule
 * `admin = is_staff OR is_superuser`.
 *
 * The request goes through the shared axios instance, so the 401 → refresh →
 * retry interceptor of `lib/api.ts` applies.
 */
export async function getAdminMe(): Promise<AdminMeEnvelope> {
  try {
    const { data } = await api.get("/auth/me");
    return AdminMeEnvelopeSchema.parse(data);
  } catch (error) {
    const axiosError = error as AxiosError;
    throw new ApiQueryError(
      getErrorMessage(error),
      axiosError.response?.status,
    );
  }
}
