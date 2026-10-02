# Exploration: Dashboard Flicker/Refresh Bug

## Current State

The dashboard re-renders or "flickers" constantly. The architecture has:
- `app/(app)/layout.tsx` — Server Component that calls `getUserSession()` (reads `USER_SESSION` cookie directly) and redirects to `/` if no user
- `app/layout.tsx` — RootLayout wrapping all routes in `AuthHydrationShell`
- `AuthHydrationShell` — client component that re-validates user via `GET /auth/me` on every mount
- Zustand persist store — syncs `user` to localStorage, no `hasHydrated` flag
- `proxy.ts` — server-side route guard checking `ACCESS_TOKEN` cookie only

## Affected Areas

- `frontend/src/features/auth/components/AuthHydrationShell.tsx` — re-validates /auth/me on every layout mount
- `frontend/src/features/auth/store/auth.store.ts` — Zustand persist with async rehydration, no hydration-ready flag
- `frontend/src/components/ui/sidebar.tsx` (SidebarProvider) — `setOpen` callback depends on `open` value
- `frontend/src/proxy.ts` — changed redirect from `/login` to `/`; only checks `ACCESS_TOKEN`, not `USER_SESSION`
- `frontend/src/app/layout.tsx` — wraps all routes in `AuthHydrationShell` unconditionally

## Root Cause Analysis

### Candidate 1: AuthHydrationShell re-validation loop (HIGHEST PROBABILITY)

`AuthHydrationShell` runs its `useEffect` on **every layout mount** (i.e., every navigation):

```typescript
useEffect(() => {
  if (!user) return;   // guards on null user only
  async function validate() {
    const response = await api.get("/auth/me");
    if (!response.data?.success) logout(); // clears store!
  }
  validate();
}, [user, setAuth, logout]); // user reference changes after logout → re-runs
```

**Problem A**: After `logout()` is called, `user` becomes `null` in store. But `logout` is stable from the store, so the next render still has `logout` in the dep array. On the next render, `user` IS null, so the guard exits — this is fine.

**Problem B**: If `/auth/me` returns success but with **different user data**, `setAuth` is called with new data. This changes the `user` reference, re-running the effect. If the server returns data that doesn't match localStorage (e.g., server has the user but the session expired mid-request), this could cause rapid re-auth cycles.

**Problem C**: On initial load, the store initializes with `user: null`. The persist middleware rehydrates from localStorage asynchronously. Result:
1. First render: `user = null` (from initial state) → guard exits, no validation
2. Store rehydrates: `user = persistedUser` (from localStorage) → re-render triggered
3. `AuthHydrationShell` sees `user != null` → calls `/auth/me`
4. If `/auth/me` fails → calls `logout()` → flicker

The removed `hasHydrated` flag was specifically designed to prevent this race.

### Candidate 2: SidebarProvider setOpen callback instability (MEDIUM PROBABILITY)

```typescript
const setOpen = React.useCallback(
  (value) => {
    const openState = typeof value === "function" ? value(open) : value;
    if (setOpenProp) setOpenProp(openState); else _setOpen(openState);
    document.cookie = `${SIDEBAR_COOKIE_NAME}=${openState}; ...`;
  },
  [setOpenProp, open], // ← open is the computed value (openProp ?? _open)
);
```

If `openProp` is `undefined` (not passed), `open = _open`. The dep array contains `open`, which is `openProp ?? _open`. If neither changes, `open` is stable. **However**, if `SidebarProvider` receives a new `openProp` reference on every render (passed from parent), `open` changes every render → `setOpen` recreated every render → all consumers re-render.

But in `DashboardLayout`, `SidebarProvider` receives no props — this is likely NOT the cause.

### Candidate 3: proxy.ts cookie mismatch (MEDIUM PROBABILITY)

`proxy.ts` checks only `ACCESS_TOKEN`:
```typescript
const token = request.cookies.get(AUTH_COOKIES.ACCESS_TOKEN)?.value;
if (!token) return NextResponse.redirect(new URL("/", request.url));
```

`getUserSession` reads `USER_SESSION` cookie:
```typescript
const raw = cookieStore.get(AUTH_COOKIES.USER_SESSION)?.value;
```

If `ACCESS_TOKEN` is present but `USER_SESSION` is missing/corrupted:
- `proxy.ts` allows the request through (has token)
- `getUserSession` returns `null`
- Server layout redirects to `/`
- User sees brief dashboard → redirect to `/` → flicker

This could happen if the cookies get out of sync (e.g., token refreshed but user session not updated).

### Candidate 4: Zustand selector creating new reference (LOW PROBABILITY)

```typescript
export const useAuthUser = () => useAuthStore((state) => state.user);
```

This selector returns the `user` object. If `user` is a new reference on every store update (even if content is the same), components subscribing to `user` would re-render. But `setAuth` always creates a new user object, which is correct behavior — the user actually changed.

### Candidate 5: useIsMobile in SidebarProvider (LOW PROBABILITY)

```typescript
const [isMobile, setIsMobile] = React.useState<boolean | undefined>(undefined);
useEffect(() => {
  const mql = window.matchMedia(...);
  const onChange = () => setIsMobile(...);
  mql.addEventListener("change", onChange);
  setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
  return () => mql.removeEventListener("change", onChange);
}, []);
```

`isMobile` starts as `undefined`, then set to `true`/`false` after effect runs. This is a one-time setup. It could cause a brief layout shift on mobile but not constant flickering.

## Approaches

### Fix A: Re-add hasHydrated flag to Zustand store (Recommended)
- **What**: Add a `hasHydrated` boolean to the store, set by the persist middleware's `onRehydrateStorage` callback
- **Pros**: Directly fixes the race condition, simple change
- **Cons**: Requires store migration, all consumers need to wait for hydration
- **Effort**: Low

### Fix B: hasHydrated via event instead of store flag
- **What**: Use a custom event to broadcast hydration completion instead of a store flag
- **Pros**: No store changes needed
- **Cons**: More indirection, components need to subscribe to event
- **Effort**: Medium

### Fix C: Conditionally render AuthHydrationShell only on auth pages
- **What**: Move `AuthHydrationShell` out of RootLayout into `(app)` layout only
- **Pros**: Fixes unnecessary re-validation on public pages
- **Cons**: Doesn't fix the flicker on dashboard itself
- **Effort**: Low

### Fix D: Add hasHydrationGuard to AuthHydrationShell
- **What**: Use `persist` middleware's `onRehydrateStorage` to set a `hasHydrated` flag; only run validation when `hasHydrated && user != null`
- **Pros**: Fixes the exact race condition
- **Cons**: Requires changes to the store
- **Effort**: Low

### Fix E: Investigate proxy.ts / getUserSession mismatch
- **What**: Ensure both cookies are always set together; add `USER_SESSION` check to proxy or ensure token check covers both
- **Pros**: Fixes the cookie mismatch scenario
- **Cons**: Could have edge cases with token-only auth flows
- **Effort**: Low

## Recommendation

**Fix D (hasHydrationGuard in AuthHydrationShell) combined with Fix C (move AuthHydrationShell to (app) layout)** is the minimal, focused fix:

1. **Fix C**: Move `AuthHydrationShell` out of `RootLayout` into `app/(app)/layout.tsx`. It only needs to run for authenticated routes. This eliminates unnecessary re-validation on public pages.

2. **Fix D**: Add `hasHydrated` tracking to the store. `AuthHydrationShell` should skip validation until `hasHydrated === true`. This prevents the race condition where `user` appears null → rehydrates → re-render → validation → potential logout flicker.

This directly addresses the two most likely causes: (1) re-validation on every mount, and (2) the async rehydration race.

## Risks

- Adding `hasHydrated` flag changes store shape — ensure all store consumers handle `hasHydrated: false` gracefully
- Moving `AuthHydrationShell` to `(app)` layout means public pages won't auto-refresh user session — but public pages don't need auth validation
- `proxy.ts` cookie mismatch is harder to reproduce without more instrumentation

## Open Questions

- Can we confirm whether the flicker happens on initial page load, or on subsequent navigation?
- Does the flicker happen when accessing `/dashboard` directly, or only after navigating from another page?
- Does the flicker happen in Incognito/private browsing mode (where localStorage is empty)?
- Is there a specific network condition (slow API, token expiry) that triggers the flicker?

## Ready for Proposal

**Yes** — the investigation identified two concrete, high-probability root causes and two targeted fixes. The orchestrator should ask the user the open questions above to confirm, then proceed to `sdd-propose` for the combined fix: `hasHydrated` guard + move `AuthHydrationShell` to `(app)` layout.
