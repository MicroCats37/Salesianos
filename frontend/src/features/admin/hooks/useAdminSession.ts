"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import { getAdminMe } from "../services/admin.me.service";
import {
  type AdminCapacidad,
  adminTieneCapacidad,
} from "../utils/admin.capacidades";

/**
 * AdminSessionQueryOptions — client-side revalidation of the session.
 *
 * The navigation entry of the administration area is rendered ONLY when the
 * backend confirms `es_admin`. The `USER_SESSION` cookie is a client-writable
 * snapshot, so it never decides the visibility of the entry on its own.
 *
 * `retry: false` — a refused probe (401/403) is an answer, not a transient
 * failure: retrying it would only delay the decision.
 */
export const adminSessionQueryOptions = queryOptions({
  queryKey: ["admin", "session"] as const,
  queryFn: getAdminMe,
  staleTime: 5 * 60 * 1000,
  retry: false,
});

export function useAdminSession() {
  return useQuery(adminSessionQueryOptions);
}

/**
 * Whether the backend confirmed the administration privilege.
 *
 * `false` until the probe answers: the entry stays hidden rather than
 * flashing for a non-administrator.
 */
export function useEsAdmin(): boolean {
  const { data } = useAdminSession();
  return data?.success === true && data.data?.es_admin === true;
}

/**
 * The capabilities the backend granted to the caller.
 *
 * EMPTY until the probe answers: the navigation fails closed instead of
 * showing sections the caller may not open.
 */
export function useAdminCapacidades(): string[] {
  const { data } = useAdminSession();

  if (data?.success !== true || !data.data) {
    return [];
  }

  return data.data.capacidades ?? [];
}

/**
 * Whether the caller holds the given capability.
 *
 * The answer is ADVISORY: it decides what the interface SHOWS. The authority
 * is the backend, which re-evaluates the capability on every request and
 * answers 403 when it is missing.
 */
export function useAdminTieneCapacidad(capacidad: AdminCapacidad): boolean {
  return adminTieneCapacidad(useAdminCapacidades(), capacidad);
}
