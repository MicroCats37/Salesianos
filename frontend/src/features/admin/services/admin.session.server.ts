import { cookies } from "next/headers";
import { cache } from "react";
import { AUTH_COOKIES } from "@/lib/auth";
import { backendInternalUrl } from "@/lib/server/backend-url";
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

/**
 * The revalidated administration session, memoized per request.
 *
 * `cache()` collapses the calls of the layout of the area and the layout of
 * the section into ONE backend request: both read the same session and can
 * never disagree about it.
 *
 * The module has NO `"use server"` directive on purpose: the exported value is
 * a memoized function, not a server action. The server-action façade lives in
 * `admin.guard.service.ts`.
 */
export const getAdminSession = cache(async (): Promise<AdminSession> => {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIES.ACCESS_TOKEN)?.value;

  if (!token) {
    return { status: "unauthenticated", esAdmin: false, user: null };
  }

  let response: Response;

  try {
    response = await fetch(`${backendInternalUrl()}/auth/me`, {
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
});
