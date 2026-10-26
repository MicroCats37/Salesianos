"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import { getAdminMe } from "../services/admin.me.service";

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
