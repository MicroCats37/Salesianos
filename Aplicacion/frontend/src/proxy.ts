import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { AUTH_COOKIES } from "./lib/auth";

/**
 * proxy.ts — server-side route protection.
 *
 * Public routes are always reachable (portada, información, pases, tienda,
 * recuperación de compra, login y registro).
 * Any non-public route without a token bounces to the login page.
 *
 * Already authenticated users hitting /login go straight to /mi-cuenta.
 *
 * ── SCOPE OF THIS FILE ────────────────────────────────────────────────────────
 * This proxy is the AUTHENTICATION gate of the UX, nothing more:
 *
 * - It decides whether there is a CREDENTIAL at all (the presence of the
 *   access-token cookie). `/administracion/**` is NOT a public path and it IS
 *   covered by the matcher below, so an anonymous visitor never reaches the
 *   area: it bounces to the login page.
 * - It NEVER decides roles, permissions or capabilities. The access-token
 *   cookie is not httpOnly (`lib/auth/cookies.ts`), so any browser script can
 *   write it: this file is a courtesy, never a control.
 * - The AUTHORITY is the backend. `RequireAdmin` / `RequireCapability`
 *   (`backend/core/permissions.py`) evaluate the flags of the caller on every
 *   request, and the server-side guard of the area
 *   (`app/(administracion)/layout.tsx`) revalidates the session.
 * - Do NOT add role logic here: it would duplicate the authority and it would
 *   be based on a cookie the client controls.
 */
const PUBLIC_PATHS = new Set<string>([
  "/",
  "/informacion",
  "/pases",
  "/tienda",
  "/recuperar-compra",
  "/login",
  "/registro",
]);

export default function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip static assets and any path with a file extension so the auth gate
  // does not intercept images, fonts, css, etc. Otherwise requests like
  // `/logo-oficial-salesianos-2002.jpeg` would be redirected to "/" when the
  // visitor is unauthenticated and the browser would receive HTML instead of
  // the binary — making every logo on the marketing page look broken.
  if (/\.[^/]+$/.test(pathname)) {
    return NextResponse.next();
  }

  const token = request.cookies.get(AUTH_COOKIES.ACCESS_TOKEN)?.value;

  // The guest links carry their token in the path: the token IS the
  // credential and its expiry is the server's business.
  if (
    pathname.startsWith("/pases/gestionar/") ||
    pathname.startsWith("/tienda/pedidos/")
  ) {
    return NextResponse.next();
  }

  // A visitor that already has a credential does not need the login form.
  if (pathname === "/login" && token) {
    return NextResponse.redirect(new URL("/mi-cuenta", request.url));
  }

  if (PUBLIC_PATHS.has(pathname)) {
    return NextResponse.next();
  }

  if (!token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|images|favicon.ico).*)"],
};
