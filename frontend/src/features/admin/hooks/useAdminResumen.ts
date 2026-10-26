"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type { AdminResumenEnvelope } from "../schemas";
import { getAdminResumen } from "../services/admin.resumen.service";

/**
 * AdminResumenQueryOptions — TanStack Query v5 object syntax (REQUIRED by
 * `contract/next-app-architecture-contract.md` §4).
 *
 * The overview is server state: it is fetched, cached and invalidated by
 * TanStack Query. The numbers are NEVER recomputed in the browser.
 *
 * The error type is explicit: `ApiQueryError` keeps the HTTP status, so the
 * view can tell an access denial (403) apart from a transport failure.
 */
export const adminResumenQueryOptions = queryOptions<
  AdminResumenEnvelope,
  ApiQueryError,
  AdminResumenEnvelope,
  readonly ["admin", "resumen"]
>({
  queryKey: ["admin", "resumen"],
  queryFn: getAdminResumen,
  staleTime: 30 * 1000,
});

export function useAdminResumen() {
  return useQuery(adminResumenQueryOptions);
}
