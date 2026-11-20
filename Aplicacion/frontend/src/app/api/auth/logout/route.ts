import { NextResponse } from "next/server";

import { clearAuthCookies } from "@/lib/auth";
import { RUTAS } from "@/lib/routes";

/**
 * The logout route handler.
 *
 * TWO verbs, on purpose:
 *
 * - `POST` is the programmatic way: it clears the session and answers with a
 *   JSON envelope, for a client that calls it through `fetch`.
 * - `GET` is the way the ACCOUNT CHROME uses it. The account bar is a
 *   dropdown of plain links, and a link is a `GET`: with only `POST` exported
 *   the "Cerrar sesión" entry answered `405 Method Not Allowed` and the session
 *   stayed alive. The `GET` clears the session and REDIRECTS to the login
 *   page, so the visitor lands on a page that describes the new state.
 *
 * Neither verb decides anything about roles: the session was already granted
 * by the backend and this only forgets it.
 */
export async function POST() {
  await clearAuthCookies();
  return NextResponse.json({ success: true });
}

export async function GET(request: Request) {
  await clearAuthCookies();

  return NextResponse.redirect(new URL(RUTAS.auth.login, request.url));
}
