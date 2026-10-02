# Exploration: Auth Flow Simplification

## Topic
Compare how CIP/CAM (canonical example) handles login routing vs Salesianos, and identify simplification opportunities.

---

## 1. How CIP/CAM Structures Auth

### 1.1 `/login` Route
- **File**: `app/(auth)/login/page.tsx`
- **Pattern**: Thin server component that renders `LoginClientShell`
- **Post-login redirect**: Hardcoded `router.push("/solicitudes")` in each form's `onSubmit`
- **No `nextUrl` query param used** — destination is always the same

```tsx
// CIP/CAM: app/(auth)/login/page.tsx
export default function LoginPage() {
  return <LoginClientShell />;
}
```

### 1.2 proxy.ts — Server-Side Route Protection
- **File**: `src/proxy.ts` (24 lines)
- **Pattern**: Reads `auth_access_token` cookie. Two rules only:
  1. `/login` with token → redirect to `/liquidaciones`
  2. Any path without token → redirect to `/login`

```ts
// CIP/CAM proxy.ts — SIMPLIFIED
export default function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("auth_access_token")?.value;

  if (pathname === "/login" && token) {
    return NextResponse.redirect(new URL("/liquidaciones", request.url));
  }
  if (!token && !pathname.startsWith("/login")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  return NextResponse.next();
}
```

### 1.3 Protected Route Layout — Server-Side Guard
- **File**: `app/(protected)/layout.tsx`
- **Pattern**: Server Component (`async`) calls `getUserSession()` → `redirect("/login")` if null
- **No client-side guard needed**

```tsx
// CIP/CAM: (protected)/layout.tsx — SERVER COMPONENT
export default async function ProtectedLayout({ children }) {
  const user = await getUserSession();
  if (!user) redirect("/login");
  return (
    <div className="flex h-svh">
      <ProtectedSidebar user={user} />
      <main>{children}</main>
    </div>
  );
}
```

### 1.4 AuthHydrationShell — "Refresh on Mount"
- **File**: `features/auth/components/AuthHydrationShell.tsx`
- **Pattern**: On client mount, if user is persisted in Zustand store → call `GET /auth/me` to validate token → on 401 clear store
- **No `hasHydrated` check** — simpler effect dependency

### 1.5 Post-Login Redirect Strategy
- **CIP/CAM**: Hardcoded per-form `router.push("/solicitudes")` or `router.push("/liquidaciones")`
- **No `nextUrl` param** — no dynamic redirect logic

---

## 2. How Salesianos Currently Handles Auth

### 2.1 `/login` Route
- **File**: `app/(auth)/login/page.tsx` with `Suspense` wrapper
- **Post-login redirect**: Uses `usePostLoginTarget()` hook → reads `nextUrl` query param

### 2.2 proxy.ts — More Complex (72 lines)
- **File**: `src/proxy.ts`
- **Adds**: `safeNextUrl()` function to validate and decode `nextUrl` param
- **Protected prefixes**: `["/dashboard", "/inscripcion"]`
- **Three rules**: (1) `/login` with token → safeNextUrl or `/dashboard`, (2) `/register` with token → `/dashboard`, (3) protected without token → `/login?nextUrl=<path>`

### 2.3 `(app)/layout.tsx` — Client-Side Guard
- **File**: `app/(app)/layout.tsx`
- **Pattern**: `'use client'` component that watches `useAuthStore` → redirects to `/login?nextUrl=<pathname>` if unauthenticated
- **Waits for `hasHydrated`** before redirecting to avoid flash

```tsx
// Salesianos: (app)/layout.tsx — CLIENT COMPONENT GUARD
export default function ProtectedLayout({ children }) {
  const user = useAuthUser();
  const hasHydrated = useAuthStore((s) => s.hasHydrated);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!hasHydrated) return;
    if (!user && pathname) {
      router.replace(`/login?nextUrl=${encodeURIComponent(pathname)}`);
    }
  }, [hasHydrated, user, pathname, router]);

  if (!hasHydrated || (!user && pathname)) return null;
  return <>{children}</>;
}
```

### 2.4 AuthHydrationShell — with `hasHydrated` Check
- **File**: `features/auth/components/AuthHydrationShell.tsx`
- **Pattern**: Same "refresh on mount" but waits for `hasHydrated` before calling `/auth/me`

### 2.5 usePostLoginTarget Hook
- **File**: `features/auth/hooks/usePostLoginTarget.ts`
- **Pattern**: Reads `nextUrl` query param, validates it starts with `/`, not `//`, not `/login`, decodes it, returns decoded path or `/dashboard`

---

## 3. Key Differences Summary

| Aspect | CIP/CAM (Canonical) | Salesianos (Current) |
|--------|---------------------|---------------------|
| **Protected layout** | Server Component with `redirect()` | Client Component with `useEffect` + `router.replace` |
| **Auth check location** | `(protected)/layout.tsx` (server) | `(app)/layout.tsx` (client) |
| **post-login redirect** | Hardcoded `router.push("/solicitudes")` | Dynamic `usePostLoginTarget()` reading `nextUrl` |
| **nextUrl validation** | None needed | `safeNextUrl()` in proxy.ts + duplicated in hook |
| **hasHydrated state** | Not used | Required to avoid premature redirect |
| **AuthHydrationShell** | Simple effect without `hasHydrated` guard | Effect waits for `hasHydrated` |
| **proxy.ts complexity** | 24 lines, 2 rules | 72 lines, 3 rules + safeNextUrl |
| **Zustand store** | Simple: user + isAuthenticated | Adds `hasHydrated` + `setHasHydrated` |

---

## 4. Files Affected

### Salesianos files involved in current auth flow:
- `src/proxy.ts` — route protection with nextUrl logic
- `src/app/(app)/layout.tsx` — client-side auth guard
- `src/app/layout.tsx` — RootLayout with AuthHydrationShell
- `src/features/auth/components/AuthHydrationShell.tsx` — token validation on mount
- `src/features/auth/hooks/usePostLoginTarget.ts` — post-login redirect target
- `src/features/auth/store/auth.store.ts` — hasHydrated state
- `src/features/auth/hooks/useLogin.ts` — sets cookies + returns user
- `src/features/auth/views/LoginClientShell.tsx` — login form with 3 tab types

---

## 5. Over-Engineering Analysis

Salesianos adds complexity in **4 areas** that CIP/CAM doesn't need:

### 5.1 Client-Side Guard vs Server Redirect
**CIP/CAM**: `redirect("/login")` in a Server Component — zero JS sent, no hydration issues, instant.
**Salesianos**: `useEffect` in a `'use client'` component — requires `hasHydrated` to avoid premature redirect flash.

**Over-engineering**: The client-side guard requires `hasHydrated` tracking in the Zustand store and the `AuthHydrationShell` pattern. A server-side redirect in a layout would eliminate all of this.

### 5.2 Dynamic nextUrl vs Hardcoded Destinations
**CIP/CAM**: Hardcoded `router.push("/solicitudes")` — one destination, no validation needed.
**Salesianos**: `usePostLoginTarget` + `safeNextUrl()` in proxy — validates, decodes, and redirects to the originally requested page.

**Over-engineering**: For a typical app where post-login always goes to `/dashboard`, the dynamic nextUrl adds significant complexity (safeNextUrl validation, encoding/decoding, two places where it lives). However, if the user needs to preserve the intended destination across login, this is genuinely useful.

### 5.3 Duplicated safeNextUrl Logic
The `safeNextUrl()` validation appears in **both**:
- `src/proxy.ts` (proxy layer)
- `src/features/auth/hooks/usePostLoginTarget.ts` (application layer)

CIP/CAM doesn't have this duplication because it doesn't use nextUrl at all.

### 5.4 hasHydrated State
Required because the client-side guard in `(app)/layout.tsx` runs before Zustand persist rehydrates from localStorage. Without this flag, the guard would redirect authenticated users back to `/login` during the brief window before the store loads.

A server-side layout would eliminate this because the server renders once with known auth state.

---

## 6. Recommended Approach

### Minimal Change: Server-Side Protected Layout

Replace the client-side `(app)/layout.tsx` guard with a server-side `(protected)/layout.tsx` pattern, matching CIP/CAM.

**Changes needed**:
1. Create `app/(app)/layout.tsx` as an `async` Server Component that calls `getToken()` or similar server-side auth check
2. Redirect to `/login` if unauthenticated
3. Remove `usePostLoginTarget` hook — hardcode post-login redirect destinations in each form
4. Simplify `AuthHydrationShell` to remove `hasHydrated` check
5. Remove `hasHydrated` from Zustand store
6. Simplify `proxy.ts` to match CIP/CAM (remove `safeNextUrl`, simplify to 2 rules)

**What is preserved**:
- Three-tab login form (DNI, Email, Username) — **keep**
- AuthHydrationShell token validation pattern — **keep**
- Zustand store for user state — **keep** (simplified)
- All participant/aceptaciones/smart DNI functionality — **not affected**

### Files That Could Be Removed/Simplified

| File | Action | Rationale |
|------|--------|-----------|
| `src/app/(app)/layout.tsx` | **Replace** with server-side layout | Client-side guard is redundant with server redirect |
| `src/features/auth/hooks/usePostLoginTarget.ts` | **Delete** | Only needed for dynamic nextUrl; hardcoded redirect is simpler |
| `src/features/auth/store/auth.store.ts` | **Simplify** — remove `hasHydrated` + `setHasHydrated` | Only needed because client guard runs before persist rehydrates |
| `src/features/auth/components/AuthHydrationShell.tsx` | **Simplify** — remove `hasHydrated` check in useEffect | Server layout means auth is known at render time |
| `src/proxy.ts` | **Simplify** to CIP/CAM pattern (24 lines, 2 rules) | safeNextUrl and register redirect are over-engineering |

---

## 7. Complexity Reduction Estimate

**Lines of code reduction**: ~120-150 lines across 5 files
- proxy.ts: 72 → ~24 lines (-48)
- usePostLoginTarget.ts: delete (-40 lines)
- auth.store.ts: 76 → ~50 lines (-26)
- AuthHydrationShell.tsx: 59 → ~45 lines (-14)
- (app)/layout.tsx: 40 lines → replaced with ~15 line server component (-25)

**Net reduction**: ~120-150 lines removed

**Files that could be deleted**: 1 (`usePostLoginTarget.ts`)

---

## 8. Risks & Open Questions

1. **Smart DNI lookup feature**: Does any feature rely on the `nextUrl` being preserved across login? If a user initiates an action that requires login, do they need to return to that exact page?
2. **participants/aceptaciones flows**: Are there any post-login redirects that are NOT `/dashboard`? If so, hardcoded destinations may break those flows.
3. **Register flow**: Salesianos proxy handles `/register` with token → redirect to `/dashboard`. CIP/CAM doesn't have this rule. Is it needed?
4. **AuthHydrationShell in RootLayout**: Moving to server-side layout means AuthHydrationShell's token validation is less critical (server already knows auth state). Could it be removed entirely?

---

## 9. Ready for Proposal

**Yes** — with the following clarification needed first:

> Before proposing, confirm: Does any user flow depend on being redirected to a page OTHER than `/dashboard` after login? If yes, which flows and what destinations?
