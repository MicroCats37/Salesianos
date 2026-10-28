"use server";

import { type AdminSession, getAdminSession } from "./admin.session.server";

/**
 * Revalida la sesión administrativa contra el BACKEND.
 *
 * Endpoint: GET /api/auth/me  (A0)
 *
 * The `USER_SESSION` cookie is a non-httpOnly snapshot that the client can
 * forge and that nothing revalidates, so it is NEVER used as authority. The
 * only source of truth is the answer of the backend, where the flags are
 * computed with the project rule `admin = is_staff OR is_superuser` — the
 * very same rule the `RequireAdmin` permission applies to every admin
 * endpoint (`sdd/administracion-operativa-fest/admin-surface` §6).
 *
 * The call is made with `cache: "no-store"` on purpose: the guard must
 * observe a revocation, not a cached answer.
 *
 * The server-side call reaches the backend through `backendInternalUrl()`:
 * the browser URL (`/backend`) is RELATIVE and a Node `fetch` cannot resolve
 * it, which is exactly what broke the area in production.
 *
 * NOTE: a `"use server"` module may ONLY export async functions. Re-exporting
 * a type from here makes the server-action proxy try to re-export it at
 * runtime ("Export AdminSession doesn't exist in target module"). The types
 * are re-exported from `admin.session.server` / `services/index.ts` instead.
 */
export async function revalidateAdminSession(): Promise<AdminSession> {
  return getAdminSession();
}
