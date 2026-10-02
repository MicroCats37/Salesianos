# Exploration: `/dashboard/inscripcion/<id>` Infinite Reload Loop

**Topic Key**: `sdd/dashboard-detail-reload-loop/explore`
**Project**: Salesianos
**Date**: 2026-09-21
**Type**: bugfix
**Status**: investigation complete

---

## Executive Summary

The infinite reload loop at `/dashboard/inscripcion/<id>` after login is caused by **two interacting issues**:

1. **`LoginClientShell` ignores `nextUrl`** — after successful login, it hardcodes redirect to `/dashboard` instead of reading and using the `nextUrl` query parameter. This breaks the intended UX but does NOT directly cause an infinite loop.

2. **Token validation failure on the detail page** — The most likely root cause of an actual loop is a 401 from `/auth/me` after login, causing `AuthHydrationShell` to call `logout()`, which triggers `ProtectedLayout` to redirect back to `/login`, creating a cycle if the token is persistently invalid.

Additionally, `InscripcionDetailView`'s `fetchDetalle` effect has `user` in its dependency array, which could contribute to repeated API calls if the `user` object identity changes unexpectedly.

---

## Current State

### Auth Flow Architecture

```
User → /dashboard/inscripcion/<id>
     → ProtectedLayout [hasHydrated?, user?, pathname?]
     → If !user: router.replace(`/login?nextUrl=${pathname}`)
     → /login?nextUrl=/dashboard/inscripcion/123
     → LoginClientShell.onSubmit() → setAuth() → router.push("/dashboard")
     → /dashboard (NOT nextUrl!)
```

### Key Files and Their Roles

| File | Role | Relevant Issue |
|------|------|---------------|
| `app/(app)/layout.tsx` | `ProtectedLayout` — auth guard with `[hasHydrated, user, pathname, router]` effect | Redirects to login if `!user && pathname` after hydration |
| `app/layout.tsx` | Root layout with `AuthHydrationShell` wrapping all children | Shell always present, validates on every mount |
| `features/auth/components/AuthHydrationShell.tsx` | Calls `GET /auth/me` when `hasHydrated && user`; calls `logout()` on 401 | If 401 after login → logout → redirect loop |
| `features/auth/views/LoginClientShell.tsx` | Login form — ignores `nextUrl`, hardcodes `/dashboard` redirect | UX bug: user loses intended destination |
| `features/inscripciones/views/InscripcionDetailView.tsx` | Detail view with `fetchDetalle` effect on `[user, inscripcionId]` | `user` dep could cause repeated fetches |
| `lib/api.ts` | Axios interceptor with single-retry 401→refresh logic | Refresh failure propagates 401, could trigger logout |

---

## Affected Areas

- `frontend/src/app/(app)/layout.tsx` — `ProtectedLayout` redirects to login; `router` and `pathname` in dep array
- `frontend/src/features/auth/views/LoginClientShell.tsx` — **Does NOT read `nextUrl`**; always pushes `/dashboard`
- `frontend/src/features/auth/components/AuthHydrationShell.tsx` — Calls `logout()` on `/auth/me` failure; could trigger redirect loop
- `frontend/src/features/inscripciones/views/InscripcionDetailView.tsx` — `fetchDetalle` effect has `user` in deps; `user` reference from store may not be stable
- `frontend/src/lib/api.ts` — Single-retry 401 interceptor; refresh failure returns original 401

---

## Root Cause Analysis

### Issue 1: `LoginClientShell` Ignores `nextUrl` (UX Bug)

```typescript
// LoginClientShell - onSubmit handler
const onSubmit = async (data) => {
  const result = await loginMutation.mutateAsync(data);
  setAuth(result);           // ✅ Updates store
  router.push("/dashboard"); // ❌ HARDCODED - ignores nextUrl!
};
```

The URL at login is `/login?nextUrl=/dashboard/inscripcion/123`, but `LoginClientShell` never reads `nextUrl`. After login, user always goes to `/dashboard`.

**This is a bug but not an infinite loop.**

### Issue 2: Token Validation Failure → Logout Loop (Likely Root Cause of Loop)

If `/auth/me` returns 401 after login, `AuthHydrationShell` calls `logout()`:

```typescript
// AuthHydrationShell.tsx
} catch {
  if (!cancelled) {
    logout();  // Clears user from store
  }
}
```

When `logout()` is called:
1. `user` becomes `null` in Zustand store
2. `ProtectedLayout`'s effect fires: `!user && pathname` → `true` → `router.replace("/login?nextUrl=...")`
3. User is redirected to login
4. After re-login, same failure occurs → **loop**

**Possible reasons `/auth/me` fails after login:**
- Token not properly stored in cookies after `setCookie`
- Token refresh rotation failing
- Backend login endpoint not returning a valid token
- Server-side `/api/auth/refresh` route failing

### Issue 3: `InscripcionDetailView` `user` Dependency

```typescript
// InscripcionDetailView.tsx
useEffect(() => {
  fetchDetalle();
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [user, inscripcionId]);
```

The `user` variable is `useAuthStore((s) => s.user)` — a store selector result. If the store updates cause `user` to get a new object reference, this effect re-fires. Combined with `fetchDetalle` calling the API, any instability in the user object could cause repeated fetches.

---

## Approaches

### Approach A: Fix `LoginClientShell` to Respect `nextUrl` (Minimal Fix)

Read `nextUrl` from search params and redirect there after successful login instead of hardcoding `/dashboard`.

```typescript
// In onSubmit after setAuth:
const params = new URLSearchParams(window.location.search);
const nextUrl = params.get("nextUrl") || "/dashboard";
router.push(nextUrl);
```

- **Pros**: Simple, fixes UX bug
- **Cons**: Does not fix the underlying loop if token validation is failing
- **Effort**: Low

### Approach B: Add Auth Guard on Login Page to Prevent Authenticated Access

If user is already authenticated and visits `/login`, redirect to dashboard instead of showing login form.

- **Pros**: Prevents confusion if user is already logged in
- **Cons**: Minor; doesn't address the main loop issue
- **Effort**: Low

### Approach C: Stabilize `InscripcionDetailView` `fetchDetalle` Effect

Remove `user` from the dependency array since it's not actually used inside the effect, or use a stable user ID reference.

```typescript
useEffect(() => {
  fetchDetalle();
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [inscripcionId]); // Remove user - not needed
```

- **Pros**: Prevents unnecessary re-fetches if user object identity changes
- **Cons**: Might miss auth state changes that should trigger re-fetch
- **Effort**: Low

### Approach D: Debug Token Storage/Validation

Add logging to trace token storage and validation flow:
1. Log cookies after `setCookie` in `useLogin`
2. Log token read in `api.ts` interceptor
3. Log `/auth/me` response

- **Pros**: Identifies root cause of 401 loop
- **Cons**: Requires instrumentation; not a fix itself
- **Effort**: Medium (instrumentation)

---

## Recommendation

**Immediate fix**: Approach A (respect `nextUrl`) + Approach C (stabilize `fetchDetalle` deps).

**Then investigate**: Approach D to confirm whether the 401→logout→redirect loop is happening due to token issues or something else.

The `LoginClientShell` issue is definitely present and should be fixed. The `fetchDetalle` dep array is a code smell but likely not the loop cause. The most concerning issue is the potential 401→logout cycle in `AuthHydrationShell`.

---

## Risks / Open Questions

1. **Is the loop actually happening?** The `LoginClientShell` issue means users get to `/dashboard` instead of `/dashboard/inscripcion/<id>`. User might perceive this as a "loop" because they keep ending up at the wrong page.

2. **Token validity**: After login, is the token properly stored and sent with `/auth/me`? Check if `setCookie` in `useLogin.ts` is working correctly and if the cookie is being sent with subsequent requests.

3. **Refresh failure**: If `/api/auth/refresh` fails (401), does the user get stuck in a redirect cycle? The single-retry logic in `api.ts` should prevent infinite retries, but if refresh itself is failing, the 401 propagates.

4. **`user` reference stability**: Does the store's `user` object identity change in a way that triggers the `InscripcionDetailView` effect repeatedly?

5. **Hydration timing**: On hard refresh after login, `hasHydrated` is `false` initially. Does `ProtectedLayout` redirect before hydration completes, causing visible flicker or potential loop?

---

## Ready for Proposal

**Yes** — the investigation identifies clear issues:

1. `LoginClientShell` definitely ignores `nextUrl` (confirmed in code)
2. `InscripcionDetailView` has `user` in deps unnecessarily
3. Token validation failure could cause logout loop (needs verification)

The recommended apply plan is minimal:
1. Fix `LoginClientShell` to read and use `nextUrl`
2. Remove `user` from `fetchDetalle` effect deps (or verify it's stable)
3. Add debugging/logging to confirm token validation flow
