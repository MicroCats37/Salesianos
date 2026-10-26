"use server";

import { cookies } from "next/headers";
import { AUTH_COOKIES } from "@/lib/auth";
import { AdminMeEnvelopeSchema, type AdminMeResponse } from "../schemas";

/**
 * Outcome of the server-side revalidation of the administration session.
 *
 * - `admin` — the backend confirmed `es_admin = true`.
 * - `forbidden` — the caller is authenticated but is NOT an administrator.
 * - `unauthenticated` — there is no usable access token (401 / no cookie).
 * - `unavailable` — the backend could not be reached or answered something
 *   unexpected. The area FAILS CLOSED: an unverified caller never gets in.
 */
export type AdminSessionStatus =
  | "admin"
  | "forbidden"
  | "unauthenticated"
  | "unavailable";

export interface AdminSession {
  status: AdminSessionStatus;
  /** Mirrors the backend `es_admin` flag. Never inferred from a cookie. */
  esAdmin: boolean;
  /** The confirmed identity, when the backend answered. */
  user: AdminMeResponse | null;
}

const BACKEND_API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

/**
 * Revalida la sesión administrativa contra el BACKEND.
 *
 * Endpoint: GET /api/auth/me  (A0)
 *
 * The `USER_SESSION` cookie is a non-httpOnly snapshot that the client can
 * forge and that nothing revalidates, so it is NEVER used as authority. The
 * only source of truth is the answer of the backend, where the flag is
 * computed with the project rule `admin = is_staff OR is_superuser` — the
 * very same rule the `RequireAdmin` permission applies to every admin
 * endpoint (`sdd/administracion-operativa-fest/admin-surface` §6).
 *
 * The call is made with `cache: "no-store"` on purpose: the guard must
 * observe a revocation, not a cached answer.
 */
export async function revalidateAdminSession(): Promise<AdminSession> {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIES.ACCESS_TOKEN)?.value;

  if (!token) {
    return { status: "unauthenticated", esAdmin: false, user: null };
  }

  let response: Response;

  try {
    response = await fetch(`${BACKEND_API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
  } catch {
    return { status: "unavailable", esAdmin: false, user: null };
  }

  if (response.status === 401) {
    return { status: "unauthenticated", esAdmin: false, user: null };
  }

  if (!response.ok) {
    return { status: "unavailable", esAdmin: false, user: null };
  }

  let payload: unknown;

  try {
    payload = await response.json();
  } catch {
    return { status: "unavailable", esAdmin: false, user: null };
  }

  const envelope = AdminMeEnvelopeSchema.safeParse(payload);

  if (!envelope.success || !envelope.data.data) {
    return { status: "unavailable", esAdmin: false, user: null };
  }

  const user = envelope.data.data;

  return {
    status: user.es_admin ? "admin" : "forbidden",
    esAdmin: user.es_admin,
    user,
  };
}
