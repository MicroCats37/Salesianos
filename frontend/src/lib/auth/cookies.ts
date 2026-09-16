// Re-export the canonical auth cookie name + server-side helpers.
// Cookies are httpOnly + set ONLY in Route Handlers (server-side).
export {
  AUTH_COOKIE_NAME,
  clearAuthCookie,
  getAuthCookie,
  setAuthCookie,
} from "@/infra/auth/cookies";
