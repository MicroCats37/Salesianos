import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { AUTH_COOKIES } from "./lib/auth";

/**
 * proxy.ts — server-side route protection.
 *
 * Public routes are always reachable (home, login, register, evento).
 * Any non-public route without a token bounces to the home page; the
 * home CTA links to /login if the user wants to authenticate.
 *
 * Already authenticated users hitting /login go straight to /dashboard.
 *
 * ── SCOPE OF THIS FILE ────────────────────────────────────────────────────────
 * This proxy is the AUTHENTICATION gate of the UX, nothing more:
 *
 * - It decides whether there is a CREDENTIAL at all (the presence of the
 *   access-token cookie). `/administracion/**` is NOT a public path and it IS
 *   covered by the matcher below, so an anonymous visitor never reaches the
 *   area: it bounces to the home page.
 * - It NEVER decides roles, permissions or capabilities. The access-token
 *   cookie is not httpOnly (`lib/auth/cookies.ts`), so any browser script can
 *   write it: this file is a courtesy, never a control.
 * - The AUTHORITY is the backend. `RequireAdmin` / `RequireCapability`
 *   (`backend/core/permissions.py`) evaluate the flags of the caller on every
 *   request, and the server-side guard of the area
 *   (`app/(app)/administracion/layout.tsx`) revalidates the session against
 *   `GET /api/auth/me`.
 * - Do NOT add role logic here: it would duplicate the authority and it would
 *   be based on a cookie the client controls.
 */
const PUBLIC_PATHS = new Set<string>([
  "/",
  "/login",
  "/register",
  "/informacion",
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

  if (PUBLIC_PATHS.has(pathname)) {
    return NextResponse.next();
  }

  if (pathname === "/login" && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  if (!token) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|images|favicon.ico).*)"],
};
