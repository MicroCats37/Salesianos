# Next.js Frontend Architecture Contract

> **Version:** 1.0
> **Stack:** Next.js 16 + React 19 + TypeScript + TanStack Query v5 + Zustand v5 + React Hook Form v7 + Zod v4
> **Scope:** Complete frontend architecture: folder structure, naming conventions, component boundaries, state management, and anti-patterns.

---

## Core Principle

> **`app/` is for routing only. `src/features/` is for business logic.**

The `app/` directory handles routing, layouts, and page composition. All reusable logic (hooks, services, schemas) lives in `src/features/`.

---

## 1. Folder Structure

```
src/
├── app/                        # ROUTING ONLY
│   ├── (public)/               # Route group: public pages
│   │   └── products/
│   │       ├── page.tsx        # Thin page: imports from features
│   │       ├── loading.tsx
│   │       └── _components/    # Page-specific UI only (no logic)
│   └── (admin)/                # Route group: admin pages
│       └── products/
│           ├── page.tsx
│           └── _components/
│
├── features/                   # ALL BUSINESS LOGIC
│   ├── products/              # Shared domain logic
│   ├── admin/
│   │   └── products/          # Admin-specific overrides
│   └── public/
│       └── products/          # Public-specific logic
│
├── components/                # GENERIC REUSABLE UI (Legos)
│   └── ui/
│       ├── button.tsx
│       └── input.tsx
│
├── shared/                    # CROSS-FEATURE BUSINESS LOGIC
│   ├── schemas/               # pagination.schema.ts, error.schema.ts
│   ├── types/                 # ApiResponse<T>, PaginatedResult<T>
│   └── utils/                 # helpers used by 2+ features
│
└── lib/                       # INFRASTRUCTURE ONLY
    ├── api.ts                 # Axios instance (used by all services)
    └── query-client.ts        # TanStack Query client config
```

### Feature Folder Anatomy

Every feature follows this internal structure:

```
src/features/auth/
├── schemas/
│   ├── login.schema.ts
│   ├── register.schema.ts
│   └── index.ts               # barrel (internal only)
├── services/
│   ├── login.service.ts
│   ├── register.service.ts
│   └── index.ts
├── hooks/
│   ├── useLogin.ts
│   ├── useRegister.ts
│   └── index.ts
├── utils/
│   ├── auth.utils.ts
│   └── index.ts
└── components/
    ├── LoginForm.tsx
    └── index.ts               # only public UI exposed here
```

---

## 2. Naming Conventions

| Layer | File | Export | Type Export |
|-------|------|--------|-------------|
| Schema | `login.schema.ts` | `LoginFormSchema` | `LoginFormData` |
| Schema (API) | `login.schema.ts` | `LoginResponseSchema` | `LoginResponse` |
| Service | `login.service.ts` | `loginUser()` | — |
| Hook | `useLogin.ts` | `useLogin()` | — |
| Utils | `auth.utils.ts` | `formatAuthError()` | — |
| Component | `LoginForm.tsx` | `LoginForm` | `LoginFormProps` |

### Schema Naming by Operation

```typescript
// Form schemas (client-side)
LoginFormSchema       → LoginFormData
RegisterFormSchema    → RegisterFormData

// API schemas (server contracts)
CreateProductSchema   → CreateProductData    // POST body
UpdateProductSchema  → UpdateProductData    // PATCH body
ProductResponseSchema → ProductResponse      // GET response
```

---

## 3. Server Components vs Client Components

### Golden Rules

| Rule | Reason |
|------|--------|
| Default to **Server Components** | Zero JS sent to client, direct DB access, secure |
| Use `'use client'` **as low as possible** in the tree | Minimizes client bundle |
| Use **Server Actions** for mutations | Replaces API routes for form submissions |

### Server Component (Data Fetching)

```typescript
// app/products/page.tsx — Server Component
import 'server-only';
import { ProductList } from './_components/product-list';

export default async function ProductsPage() {
  // Direct data access in Server Component
  const products = await db.product.findMany();
  
  return (
    <main>
      <ProductList products={products} />
    </main>
  );
}
```

### Client Component (Interactivity)

```typescript
// components/ui/client-toggle.tsx — Client Component
'use client'
import { useState } from 'react';

export function ClientToggle() {
  const [open, setOpen] = useState(false);
  return <button onClick={() => setOpen(!open)}>Toggle</button>;
}
```

### Server Action (Mutation)

```typescript
// app/actions/products.ts
'use server'
import { revalidatePath } from 'next/cache';
import { CreateProductSchema } from '@/features/products/schemas';

export async function createProduct(prevState: any, formData: FormData) {
  const validated = CreateProductSchema.safeParse(Object.fromEntries(formData));
  if (!validated.success) {
    return { error: 'Invalid data', fieldErrors: validated.error.flatten().fieldErrors };
  }

  await db.product.create({ data: validated.data });
  revalidatePath('/products');
  return { success: true };
}
```

### Forbidden: Server Component in Client Component

You cannot import a Server Component directly into a Client Component. Pass it as `children` prop.

---

## 4. State Management

### TanStack Query v5 — Server State

Use for all **server data**: fetching, caching, mutations.

```typescript
// Always use object syntax (REQUIRED)
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryOptions } from "@tanstack/react-query";

const productQueryOptions = queryOptions({
  queryKey: ['products'],
  queryFn: () => api.get<Product[]>('/products'),
  staleTime: 5 * 60 * 1000,
});

export function useProducts() {
  return useQuery(productQueryOptions);
}
```

### Zustand v5 — Client State

Use for **UI state** that persists across components: modals, theme, auth session.

```typescript
// slices/auth.slice.ts
interface AuthSlice {
  user: User | null;
  setUser: (user: User) => void;
  logout: () => void;
}

const createAuthSlice: StateCreator<AuthSlice> = (set) => ({
  user: null,
  setUser: (user) => set({ user }),
  logout: () => set({ user: null }),
});

// store.ts
export const useBoundStore = create<AuthSlice & UISlice>()((...a) => ({
  ...createAuthSlice(...a),
  ...createUISlice(...a),
}));
```

### Rules

| Rule | Why |
|------|-----|
| TanStack Query for **all async server data** | Caching, invalidation, loading states |
| Zustand for **UI state only** | Theme, modals, user session |
| Always use `useShallow` for multi-property selects | Prevents unnecessary re-renders |
| SSR-safe custom `useStore` hook | Avoids hydration mismatches |

---

## 5. Forms Architecture

### Core Principle

> **`GenericForm` owns validation and state. Features own layout and data transformation.**

### Rendering Modes

| Mode | Use Case | Status |
|------|----------|--------|
| Mode 1 — Manual (`children` prop) | Production screens | ✅ REQUIRED |
| Mode 2 — Automatic (`fields` array) | Prototyping only | ❌ FORBIDDEN in production |
| Mode 3 — Sections (`formSections`) | Internal admin tools | ❌ FORBIDDEN in production |
| Mode 4 — Hybrid (`formMethods` prop) | Multi-step wizards | ✅ When needed |

### Payload Strategy

```
Feature Component → mutate(data: T) → useApiCreate → buildApiPayload(data) → API
```

**`buildApiPayload` lives in the mutation hook, NEVER in the form component.**

### Error Handling

All API errors flow through `handleApiError()` which:
1. Parses errors through the chain (Django → DRF → Generic REST)
2. Applies `fieldErrors` to form fields via RHF `setError`
3. Shows toast via the swappable adapter

Components handle **zero raw error logic**.

---

## 6. Import Conventions

### ✅ REQUIRED: Named Imports Always

```typescript
import { useState, useRef } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { z } from "zod";
```

### ❌ FORBIDDEN: Default / Namespace Imports

```typescript
import React from "react";          // ❌ React 18 pattern
import * as React from "react";    // ❌ Never
import * as z from "zod";          // ❌ Never
```

### Import Order (enforced by Biome)

```typescript
// 1. External libraries
import { useQuery } from "@tanstack/react-query";
import { z } from "zod";

// 2. Internal aliases (@/)
import { Button } from "@/components/ui/button";

// 3. Relative imports
import { LoginFormSchema } from "../schemas";
import { loginUser } from "../services";
```

---

## 7. Barrel Rules

### ✅ REQUIRED: Granular re-exports only

```typescript
// features/auth/schemas/index.ts — OK
export { LoginFormSchema, type LoginFormData } from "./login.schema";
export { RegisterFormSchema, type RegisterFormData } from "./register.schema";

// features/auth/index.ts — exposes only public UI
export { LoginForm } from "./components";
```

### ❌ FORBIDDEN: Wildcard re-exports

```typescript
export * from "./schemas";     // ❌ breaks tree-shaking
export * from "./hooks";       // ❌ imports everything
export * from "./services";    // ❌ never
```

### Barrel Depth Rules

| Level | Barrel Allowed? | Rule |
|-------|----------------|------|
| `features/auth/schemas/index.ts` | ✅ Yes | Granular named exports |
| `features/auth/index.ts` | ✅ Yes | Only public UI components |
| `features/index.ts` | ❌ Never | No global feature barrel |
| `components/ui/index.ts` | ✅ Yes | Granular named exports |
| `components/index.ts` | ❌ Never | No global component barrel |

---

## 8. Anti-Patterns (DO NOT DO)

### Components & Rendering

| ❌ FORBIDDEN | ✅ REQUIRED |
|-------------|------------|
| `use client` at page level when only a small child is interactive | Move `'use client'` as low as possible |
| `forwardRef` for passing refs | Use `ref` as a prop directly |
| `useState` + `useEffect` for form state | Use `useActionState` / React Hook Form |
| `useMemo` / `useCallback` in form components | React 19 compiler handles memoization |

### Data Fetching

| ❌ FORBIDDEN | ✅ REQUIRED |
|-------------|------------|
| `useEffect` for initial page data | Fetch in Server Components |
| API routes for internal mutations | Server Actions |
| Mixing `camelCase` and `snake_case` | API uses snake_case; transform in services |

### State Management

| ❌ FORBIDDEN | ✅ REQUIRED |
|-------------|------------|
| Zustand for server data | TanStack Query for server state |
| Multiple independent stores for related data | Single store with slices |
| `useMemo`/`useCallback` without measuring | Profile first, then optimize |

### Forms

| ❌ FORBIDDEN | ✅ REQUIRED |
|-------------|------------|
| Automatic/Sections mode in production | Mode 1 — Manual (`children` prop) |
| `buildApiPayload` inside form `onSubmit` | `buildApiPayload` in mutation hook |
| Manual `try/catch` + `setError` in components | `GenericForm` handles errors |
| Direct `toast()` calls | Use `notify` from toast adapter |

### Imports

| ❌ FORBIDDEN | ✅ REQUIRED |
|-------------|------------|
| Default imports from React | Named imports |
| Namespace imports (`* as React`) | Named imports |
| Relative paths for shared code | Use `@/` alias |
| Global barrels (`features/index.ts`) | Granular per-feature exports |

### Architecture

| ❌ FORBIDDEN | ✅ REQUIRED |
|-------------|------------|
| Business logic in `app/` pages | Delegate to `features/` |
| Prisma imports in Server Components | Use repository pattern |
| Business logic in Server Actions | Call use-cases from `src/core/` |
| Code in `lib/` beyond infrastructure | `lib/` = Axios + QueryClient only |

---

## 9. Shared Contracts

These cross-cutting contracts apply to ALL features:

| Contract | File | Purpose |
|----------|------|---------|
| Error Handling | `src/errors/error-handler.ts` + `src/errors/toast-adapter.ts` | Standardized error parsing + toast |
| API Response | `src/shared/types/api.types.ts` | `ApiResponse<T>`, `PaginatedResult<T>` |
| Payload Builder | `src/utils/payload-builder.ts` | `buildApiPayload()` for FormData |
| Type Conventions | Zod schemas in `features/*/schemas/` | `{Action}{Resource}FormSchema` pattern |

---

## 10. Admin vs Public Feature Strategy

When a domain exists in both admin and public contexts:

### Option A — Namespaced Features (DEFAULT)
Use when admin and public have **different endpoints, permissions, or schemas**.

```
src/features/
├── products/              ← shared types only
├── admin/
│   └── products/          ← full CRUD + permissions
└── public/
    └── products/          ← read-only + filters
```

### Option B — Single Feature with Variants
Use when admin and public **share >70% of logic**.

```
src/features/products/
├── schemas/
│   ├── product-public.schema.ts
│   └── product-admin.schema.ts
├── hooks/
│   ├── usePublicProducts.ts
│   └── useAdminProducts.ts
└── services/
    └── products.service.ts    ← shared service
```

### Decision Criteria

| Condition | Choose |
|-----------|--------|
| Different API endpoints | Option A |
| Different permission logic | Option A |
| Same endpoint, different display | Option B |
| Shared mutations | Option B |
| Large domain with many sub-features | Option A |

---

## 11. API Response Format

### Standard Shape

```typescript
// Success
interface ApiResponse<T> {
  data: T;
  message: string;
  success: true;
}

// Error (non-2xx)
interface ApiError {
  message: string;
  fieldErrors?: Record<string, string>;
  code?: string;
  success: false;
}

// Paginated
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  success: true;
}
```

---

## 12. React 19 Rules

| ❌ FORBIDDEN | ✅ REQUIRED |
|-------------|------------|
| Manual memoization | React Compiler handles it |
| Creating promises inside render | Pass promises as props or create outside |
| `use` hook without `Suspense` | Wrap in `Suspense` boundary |

---

## See Also

- [Lab: Next.js 16 Knowledge Index](../.agent/lab/knowledge/nextjs-16/INDEX.md)
- [Lab: Next.js Forms Spec](../.agent/lab/specs/nextjs/forms/SPEC.md)
- [Lab: Project Structure Spec](../.agent/lab/specs/nextjs/project-structure/SPEC.md)
- [Lab: TanStack Query v5](../.agent/lab/knowledge/tanstack-query-v5/INDEX.md)
- [Lab: Zustand v5](../.agent/lab/knowledge/zustand-v5/INDEX.md)
- [Lab: Shared Contracts](../.agent/lab/specs/shared/INDEX.md)
