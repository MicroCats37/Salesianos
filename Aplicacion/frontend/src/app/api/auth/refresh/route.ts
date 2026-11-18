"use server";

import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  AUTH_COOKIES,
  accessTokenCookieOptions,
  expiresAtCookieOptions,
  refreshTokenCookieOptions,
} from "@/lib/auth";
import { backendInternalUrl } from "@/lib/server/backend-url";
import { expiracionDeToken } from "@/lib/server/jwt";

/**
 * Fallback lifetime of the access token, used ONLY when the `exp` claim of
 * the issued token cannot be read.
 *
 * It matches the base lifetime of the backend (`ACCESS_TOKEN_LIFETIME = 1h`).
 * The old value was 30 DAYS: the client believed a token that lives one hour
 * was valid for a month and only discovered the truth through a 401.
 */
const MINUTOS_FALLBACK = 60;

/**
 * Refresh access token using the httpOnly refresh cookie.
 *
 * This route handler exists to proxy the backend refresh call from the client.
 * It reads the refresh token from cookies, calls the backend /api/token/refresh
 * endpoint, and sets the rotated tokens as cookies (non-httpOnly for client access).
 *
 * The backend is reached through `backendInternalUrl()`: the browser URL
 * (`/backend`) is relative and a Node `fetch` cannot resolve it, which broke
 * the refresh in production with a 500.
 *
 * `expires_at` is derived from the REAL `exp` claim of the access token the
 * backend just issued. It is a UX hint for the proactive refresh of the
 * client, never an authority: the backend validates the signature of every
 * token on every request.
 */
export async function POST() {
  try {
    const cookieStore = await cookies();

    const refreshToken = cookieStore.get(AUTH_COOKIES.REFRESH_TOKEN)?.value;

    if (!refreshToken) {
      return NextResponse.json(
        { success: false, error: { message: "Refresh token no encontrado" } },
        { status: 401 },
      );
    }

    // Call backend refresh endpoint
    const response = await fetch(`${backendInternalUrl()}/token/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!response.ok) {
      return NextResponse.json(
        { success: false, error: { message: "Refresh fallido" } },
        { status: 401 },
      );
    }

    const data = (await response.json()) as {
      access?: string;
      refresh?: string;
    };

    if (!data.access) {
      return NextResponse.json(
        { success: false, error: { message: "Token de acceso no recibido" } },
        { status: 500 },
      );
    }

    // The REAL expiry of the token the backend just issued. The `exp` claim is
    // the source of truth; the fallback only covers a malformed token.
    const expiracionReal = expiracionDeToken(data.access);
    const expiresAt = (
      expiracionReal ?? new Date(Date.now() + MINUTOS_FALLBACK * 60 * 1000)
    ).toISOString();

    // Set rotated tokens as httpOnly cookies
    cookieStore.set(
      AUTH_COOKIES.ACCESS_TOKEN,
      data.access,
      accessTokenCookieOptions,
    );

    if (data.refresh) {
      // ROTATE_REFRESH_TOKENS=True: new refresh token provided, persist it
      cookieStore.set(
        AUTH_COOKIES.REFRESH_TOKEN,
        data.refresh,
        refreshTokenCookieOptions,
      );
    }

    // Set non-httpOnly expires_at for client-side expiry checks
    cookieStore.set(AUTH_COOKIES.EXPIRES_AT, expiresAt, expiresAtCookieOptions);

    return NextResponse.json({
      success: true,
      data: { expires_at: expiresAt },
    });
  } catch {
    return NextResponse.json(
      { success: false, error: { message: "Error interno del servidor" } },
      { status: 500 },
    );
  }
}
