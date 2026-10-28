/**
 * Resolution of the TWO backend base URLs.
 *
 * They are different on purpose:
 *
 * - `backendPublicUrl()` is the URL the BROWSER calls. It is usually a
 *   relative path (`/backend`) because the browser reaches Django through the
 *   nginx proxy, which rewrites `/backend/*` to the internal `/api/*`.
 * - `backendInternalUrl()` is the URL the NEXT.JS SERVER calls (Server
 *   Components, Route Handlers). The server is NOT behind the browser proxy:
 *   it must reach Django directly, by its internal name inside the Docker
 *   network.
 *
 * The production incident this module fixes: the server-side code used the
 * browser URL (`NEXT_PUBLIC_API_URL=/backend`). A relative URL is invalid in a
 * Node `fetch`, so every server-side call to the backend threw a `TypeError`,
 * the administration guard answered "unavailable" and `/administracion/**`
 * redirected to `/dashboard` for EVERY user.
 *
 * `BACKEND_INTERNAL_URL` is a RUNTIME variable (not `NEXT_PUBLIC_*`), so it
 * is read from the process environment of the server and it is NEVER inlined
 * in the browser bundle.
 */

/** Internal URL of the backend inside the Docker network. */
const DOCKER_INTERNAL_URL = "http://backend:8000/api";

/** Internal URL of the backend when the app runs outside Docker. */
const LOCAL_INTERNAL_URL = "http://localhost:8000/api";

/** Strip the trailing slashes so the callers can always append `/path`. */
function normalizar(url: string): string {
  return url.replace(/\/+$/, "");
}

/**
 * The base URL the BROWSER uses to reach the backend.
 *
 * `NEXT_PUBLIC_API_URL` is a build-time variable: Next.js inlines it in the
 * client bundle. Its default is the relative path the nginx proxy rewrites.
 */
export function backendPublicUrl(): string {
  const configurada = process.env.NEXT_PUBLIC_API_URL?.trim();
  return normalizar(configurada || "/backend");
}

/**
 * The base URL the NEXT.JS SERVER uses to reach the backend.
 *
 * Resolution order:
 * 1. `BACKEND_INTERNAL_URL` — the explicit runtime configuration.
 * 2. `NEXT_PUBLIC_API_URL` when it is an ABSOLUTE url: it already points to a
 *    location the server can reach.
 * 3. `NEXT_PUBLIC_API_URL` when it is RELATIVE (the Docker/proxy setup): the
 *    server must use the internal name of the backend.
 * 4. `http://localhost:8000/api` — the sane default of a local development
 *    run without any configuration.
 */
export function backendInternalUrl(): string {
  const interna = process.env.BACKEND_INTERNAL_URL?.trim();
  if (interna) {
    return normalizar(interna);
  }

  const publica = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (publica) {
    if (/^https?:\/\//i.test(publica)) {
      return normalizar(publica);
    }
    return DOCKER_INTERNAL_URL;
  }

  return LOCAL_INTERNAL_URL;
}
