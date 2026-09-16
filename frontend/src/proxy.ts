import { type NextRequest, NextResponse } from "next/server";

export const AUTH_COOKIE_NAME = "auth-token";

const PROTECTED_PATHS = ["/dashboard", "/inscripcion", "/admin"];
const AUTH_PATHS = ["/login", "/register"];

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const hasAuth = !!request.cookies.get(AUTH_COOKIE_NAME)?.value;

  if (
    hasAuth &&
    AUTH_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))
  ) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  if (
    !hasAuth &&
    PROTECTED_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))
  ) {
    const redirectTo = encodeURIComponent(pathname + search);
    return NextResponse.redirect(
      new URL(`/login?redirect=${redirectTo}`, request.url),
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|_next/webpack-hmr|images|favicon.ico).*)",
  ],
};
