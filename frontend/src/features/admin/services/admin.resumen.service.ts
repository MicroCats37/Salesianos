"use client";

import type { AxiosError } from "axios";
import { getErrorMessage } from "@/errors";
import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { api } from "@/lib/api";
import {
  type AdminCatalogosEnvelope,
  AdminCatalogosEnvelopeSchema,
  type AdminResumenEnvelope,
  AdminResumenEnvelopeSchema,
} from "../schemas";

/**
 * AdminResumenService — read-only access to the operational administration
 * surface of the active event.
 *
 * Endpoint: GET /api/administracion/resumen  (A1)
 *
 * The service NEVER re-derives a metric: every number is computed by the
 * backend (`contract/api-wrapper-presenter-contract.md` §7). The payload is
 * validated against the 1:1 Zod mirror of `AdminResumenOut` before it leaves
 * this module, so a contract drift fails loudly instead of rendering
 * `undefined`.
 *
 * Failures are shaped as `ApiQueryError` so the caller can react to the HTTP
 * status (403 → access denied) and not only to the message.
 */
export async function getAdminResumen(): Promise<AdminResumenEnvelope> {
  try {
    const { data } = await api.get("/administracion/resumen");
    return AdminResumenEnvelopeSchema.parse(data);
  } catch (error) {
    const axiosError = error as AxiosError;
    throw new ApiQueryError(
      getErrorMessage(error),
      axiosError.response?.status,
    );
  }
}

/**
 * Filter option lists of the active event.
 *
 * Endpoint: GET /api/administracion/catalogos  (A2)
 *
 * The catalogs expose OPTION LISTS only — identifiers, display names and the
 * state vocabularies of the owning modules. No PII and no credential.
 */
export async function getAdminCatalogos(): Promise<AdminCatalogosEnvelope> {
  try {
    const { data } = await api.get("/administracion/catalogos");
    return AdminCatalogosEnvelopeSchema.parse(data);
  } catch (error) {
    const axiosError = error as AxiosError;
    throw new ApiQueryError(
      getErrorMessage(error),
      axiosError.response?.status,
    );
  }
}
