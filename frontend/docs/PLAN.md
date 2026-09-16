# Plan de Implementación — Salesianos FEST 2026 (MVP)

> **Origen:** Fase `explore` del cambio SDD `salesianos-mvp-foundation`.
> **Salida esperada:** Tareas concretas para el phase `tasks` del SDD.
> **Estimación:** ~8 fases, ~40 tareas, base ajustable.

---

## Forma de leer este plan

- Cada fase produce artefactos verificables.
- Las tareas marcadas con `[P]` son paralelizables dentro de la fase.
- Las marcadas con `[B]` son bloqueantes de las siguientes.
- Las marcadas con `[V]` son verificaciones.

---

## Phase 0 — Setup del proyecto

**Objetivo:** scaffold fullstack limpio + Drizzle + envs + biome.

| # | Tarea | Tipo | Deps |
|---|-------|------|------|
| 0.1 | Crear `package.json` con deps: next@16, react@19, typescript, drizzle-orm, better-sqlite3, postgres, jose, axios, @tanstack/react-query, zustand, react-hook-form, zod, @hookform/resolvers, sonner, lucide-react, shadcn, tailwindcss@4, biome | [B] | — |
| 0.2 | `tsconfig.json` con paths `@/*` → `./src/*` | [B] | 0.1 |
| 0.3 | `biome.json` (imports order, naming, formatter) | [B] | 0.1 |
| 0.4 | `.env.example` y `.env.local` con `DATABASE_URL`, `JWT_SECRET`, `NEXT_PUBLIC_APP_URL`, `NODE_ENV` | [B] | 0.1 |
| 0.5 | Instalar shadcn y registrar componentes base: button, input, label, card, dialog, sonner, select, checkbox, separator | [P] | 0.1 |
| 0.6 | `drizzle.config.ts` apuntando a `./src/infra/drizzle/schema` | [B] | 0.4 |
| 0.7 | `src/lib/api.ts` con Axios + interceptor JWT (lee cookie vía `withCredentials: true`, NO localStorage) | [P] | 0.1 |
| 0.8 | `src/lib/query-client.ts` + `src/providers/ReactQueryProvider.tsx` | [P] | 0.7 |
| 0.9 | `src/proxy.ts` para redirigir no-autenticados | [P] | 0.4 |
| 0.10 | Smoke check: `npm run dev` arranca sin errores | [V] | 0.1–0.9 |

**Artefactos:** proyecto arranca, `pnpm dev` funciona, página `/` renderiza.

---

## Phase 1 — Backend core (DDD)

**Objetivo:** capa `src/core/` y `src/infra/drizzle/schema/` listas.

| # | Tarea | Tipo | Deps |
|---|-------|------|------|
| 1.1 | `src/core/types/api-response.ts` con `ApiResponse<T>`, `ErrorDetail`, `PaginationMeta` | [B] | 0.10 |
| 1.2 | `src/core/errors/index.ts` con jerarquía `AppError` + 6 subclases | [B] | 1.1 |
| 1.3 | `src/infra/drizzle/schema/users.ts` (uuid pk, email unique, password_hash, rol enum) | [B] | 0.6 |
| 1.4 | `src/infra/drizzle/schema/sesiones.ts` (token_hash, expires_at, revoked_at) | [B] | 1.3 |
| 1.5 | `src/infra/drizzle/schema/promociones.ts` (catálogo) | [P] | 1.3 |
| 1.6 | `src/infra/drizzle/schema/disciplinas.ts` (catálogo: fulbito_var, fulbito_dam, voley_mix, basket_var) | [P] | 1.3 |
| 1.7 | `src/infra/drizzle/schema/categorias.ts` (vinculado a disciplina, rango años) | [P] | 1.6 |
| 1.8 | `src/infra/drizzle/schema/inscripciones.ts` (user, promocion, status enum, observacion) | [B] | 1.3, 1.5 |
| 1.9 | `src/infra/drizzle/schema/equipos.ts` (inscripcion, disciplina, categoria) | [B] | 1.6, 1.7, 1.8 |
| 1.10 | `src/infra/drizzle/schema/jugadores.ts` (equipo, dni, fecha_nacimiento) | [B] | 1.9 |
| 1.11 | `src/infra/drizzle/schema/bases.ts` (version, aprobado_en, activo) | [P] | 1.3 |
| 1.12 | `src/infra/drizzle/schema/index.ts` barrel + `src/infra/drizzle/client.ts` driver-agnostic | [B] | 1.3–1.11 |
| 1.13 | `npm run db:push` para SQLite + verificación manual | [V] | 1.12 |
| 1.14 | `src/core/repositories/user.repository.ts` (interface: findByEmail, create, findById) | [B] | 1.1, 1.2 |
| 1.15 | `src/infra/drizzle/repositories/drizzle-user.repository.ts` (implementación) | [B] | 1.12, 1.14 |
| 1.16 | Repetir 1.14–1.15 para `inscripcion`, `equipo`, `jugador`, `promocion`, `disciplina`, `categoria` | [P] | 1.12 |

**Artefactos:** schema SQLite pusheado, repos leen/escriben correctamente.

---

## Phase 2 — Auth backend (Route Handlers + JWT)

**Objetivo:** registro, login, logout, me funcionando con cookies httpOnly.

| # | Tarea | Tipo | Deps |
|---|-------|------|------|
| 2.1 | `src/infra/auth/jwt.ts` con `jose`: `signToken(payload)`, `verifyToken(token)` | [B] | 0.4 |
| 2.2 | `src/infra/auth/cookies.ts` con `setAuthCookies(response, token)`, `clearAuthCookies(response)` — httpOnly true, Secure condicional | [B] | 2.1 |
| 2.3 | `src/core/use-cases/auth/register-user.ts` (validaciones: email único, DNI formato, hash password con bcrypt o argon2) | [B] | 1.2, 1.15 |
| 2.4 | `src/core/use-cases/auth/login-user.ts` (verify password, sign JWT, devolver user) | [B] | 1.15, 2.1 |
| 2.5 | `src/core/use-cases/auth/get-current-user.ts` (verify token from cookies) | [B] | 2.1 |
| 2.6 | `src/app/api/auth/register/route.ts` (Route Handler POST: valida Zod, llama use-case, set cookies, devuelve ApiResponse) | [B] | 2.2, 2.3 |
| 2.7 | `src/app/api/auth/login/route.ts` (Route Handler POST) | [B] | 2.2, 2.4 |
| 2.8 | `src/app/api/auth/logout/route.ts` (Route Handler POST: clear cookies) | [B] | 2.2 |
| 2.9 | `src/app/api/auth/me/route.ts` (Route Handler GET: verifica cookie, devuelve user) | [B] | 2.5 |
| 2.10 | `src/app/_lib/response.ts` con helpers `successResponse`, `errorResponse`, `paginationMeta` | [B] | 1.1 |
| 2.11 | Smoke con curl/Postman: register → login → me → logout | [V] | 2.6–2.10 |

**Artefactos:** curl completo funciona, cookies se setean con `HttpOnly`.

---

## Phase 3 — Auth frontend (features/auth/)

**Objetivo:** páginas login + register funcionales, sesión hidratada en client.

| # | Tarea | Tipo | Deps |
|---|-------|------|------|
| 3.1 | `src/features/auth/schemas/login.schema.ts` + `register.schema.ts` (Zod) | [B] | — |
| 3.2 | `src/features/auth/services/auth.service.ts` (`login()` → POST `/api/auth/login`, etc.) | [B] | 2.6–2.9, 3.1 |
| 3.3 | `src/features/auth/hooks/useLogin.ts` (mutation; NO `setCookie` client-side) | [B] | 3.2 |
| 3.4 | `src/features/auth/hooks/useRegister.ts` | [P] | 3.2 |
| 3.5 | `src/features/auth/hooks/useCurrentUser.ts` (query: llama `GET /api/auth/me`) | [P] | 3.2 |
| 3.6 | `src/features/auth/store/auth.store.ts` (zustand slice: `user`, `setUser`, `clearUser` — solo session cache, NO tokens) | [B] | 3.5 |
| 3.7 | `src/features/auth/components/LoginForm.tsx` (GenericForm Mode 1) | [B] | 3.1, 3.3 |
| 3.8 | `src/features/auth/components/RegisterForm.tsx` | [P] | 3.1, 3.4 |
| 3.9 | `src/features/auth/components/AuthHydrationShell.tsx` (envuelve children, hace prefetch `useCurrentUser` con `enabled: !store.user`) | [B] | 3.5 |
| 3.10 | `src/app/(auth)/login/page.tsx` thin page → renderiza `LoginForm` | [B] | 3.7 |
| 3.11 | `src/app/(auth)/register/page.tsx` thin page → renderiza `RegisterForm` | [P] | 3.8 |
| 3.12 | `src/app/(auth)/layout.tsx` con `AuthHydrationShell` | [B] | 3.9 |
| 3.13 | Smoke en browser: register → redirect → login → ver nombre en navbar | [V] | 3.10–3.12 |

**Artefactos:** usuario puede registrarse, hacer login y ver su nombre en la UI.

---

## Phase 4 — Inscripción backend (use-cases + Server Actions)

**Objetivo:** el responsable puede crear y consultar su inscripción.

| # | Tarea | Tipo | Deps |
|---|-------|------|------|
| 4.1 | `src/core/use-cases/inscripcion/create-inscripcion.ts` (transacción: crear inscripción + equipos + jugadores; valida duplicados de DNI, max_jugadores, categoría/año) | [B] | 1.16, 1.2 |
| 4.2 | `src/core/use-cases/inscripcion/get-my-inscripcion.ts` (responsable consulta la suya) | [B] | 1.16 |
| 4.3 | `src/core/use-cases/inscripcion/list-all-inscripciones.ts` (admin) | [B] | 1.16 |
| 4.4 | `src/core/use-cases/inscripcion/update-inscripcion-status.ts` (admin; recibe status + observacion opcional) | [B] | 1.16, 1.2 |
| 4.5 | `src/app/actions/inscripcion.ts` Server Action `createInscripcionAction` con Zod safeParse → use-case → revalidatePath | [B] | 4.1 |
| 4.6 | `src/app/actions/inscripcion.ts` Server Action `updateStatusAction` con check de rol admin | [B] | 4.4 |
| 4.7 | Seed data script: 1 promoción (2002), 4 disciplinas, 8 categorías, 1 versión de bases | [B] | 1.12 |
| 4.8 | Smoke con script: crear inscripción válida + intentar inválida (DNI duplicado) | [V] | 4.5, 4.7 |

**Artefactos:** use-cases funcionan, Server Actions validan, seed cargable.

---

## Phase 5 — Inscripción frontend (wizard multi-step)

**Objetivo:** el responsable completa la inscripción en 4 pasos.

| # | Tarea | Tipo | Deps |
|---|-------|------|------|
| 5.1 | `src/features/inscripcion/schemas/step1-responsable.schema.ts` | [P] | 3.1 |
| 5.2 | `src/features/inscripcion/schemas/step2-promocion.schema.ts` | [P] | — |
| 5.3 | `src/features/inscripcion/schemas/step3-disciplinas.schema.ts` (array de equipos con jugadores) | [B] | — |
| 5.4 | `src/features/inscripcion/schemas/step4-aceptacion.schema.ts` | [P] | — |
| 5.5 | `src/features/inscripcion/schemas/inscripcion-payload.schema.ts` (unión de los 4 steps) | [B] | 5.1–5.4 |
| 5.6 | `src/features/inscripcion/services/inscripcion.service.ts` (`createInscripcion()` llama Server Action) | [B] | 4.5 |
| 5.7 | `src/features/inscripcion/hooks/useCreateInscripcion.ts` (mutation con `buildApiPayload`) | [B] | 5.5, 5.6 |
| 5.8 | `src/features/inscripcion/hooks/useMyInscripcion.ts` (query) | [P] | 4.2 |
| 5.9 | `src/features/inscripcion/components/steps/Step1Responsable.tsx` | [P] | 5.1 |
| 5.10 | `src/features/inscripcion/components/steps/Step2Promocion.tsx` | [P] | 5.2 |
| 5.11 | `src/features/inscripcion/components/steps/Step3Disciplinas.tsx` (repeater dinámico de equipos + jugadores) | [B] | 5.3 |
| 5.12 | `src/features/inscripcion/components/steps/Step4Aceptacion.tsx` | [P] | 5.4 |
| 5.13 | `src/features/inscripcion/components/InscripcionWizard.tsx` (envuelve `AppStepperFormModal`, maneja formMethods compartido entre steps) | [B] | 5.7, 5.9–5.12 |
| 5.14 | `src/app/(protected)/inscripcion/page.tsx` thin page → renderiza `InscripcionWizard` | [B] | 5.13 |
| 5.15 | `src/app/(protected)/dashboard/page.tsx` thin page → muestra `useMyInscripcion` + estado | [B] | 5.8 |
| 5.16 | Smoke en browser: login → wizard completo → ver status `RECIBIDA` en dashboard | [V] | 5.13–5.15 |

**Artefactos:** usuario responsable completa la inscripción end-to-end.

---

## Phase 6 — Admin del Comité

**Objetivo:** el admin puede ver y cambiar el estado de inscripciones.

| # | Tarea | Tipo | Deps |
|---|-------|------|------|
| 6.1 | `src/features/admin/inscripciones/hooks/useAllInscripciones.ts` (query con filtros por status) | [B] | 4.3 |
| 6.2 | `src/features/admin/inscripciones/hooks/useUpdateStatus.ts` (mutation llama Server Action) | [B] | 4.6 |
| 6.3 | `src/features/admin/inscripciones/components/InscripcionListTable.tsx` (usa `AppDataTable`) | [B] | 6.1 |
| 6.4 | `src/features/admin/inscripciones/components/StatusChangeDialog.tsx` (GenericModal + GenericForm Mode 1) | [B] | 6.2 |
| 6.5 | `src/app/(protected)/admin/comite/inscripciones/page.tsx` thin page → compone table + dialog | [B] | 6.3, 6.4 |
| 6.6 | Seed admin user (rol=admin_comite) en script | [B] | 4.7 |
| 6.7 | Smoke en browser: login admin → ver inscripciones → cambiar status → ver reflejado en dashboard del responsable | [V] | 6.5, 6.6 |

**Artefactos:** admin puede gestionar inscripciones.

---

## Phase 7 — Verificación y endurecimiento

**Objetivo:** el MVP está listo para demo.

| # | Tarea | Tipo | Deps |
|---|-------|------|------|
| 7.1 | `npx biome check` sin errores | [V] | todas |
| 7.2 | `tsc --noEmit` sin errores | [V] | todas |
| 7.3 | Smoke E2E completo: register A → login A → inscribir A → login admin → validar A → login A ve status VALIDADA | [V] | 0–6 |
| 7.4 | Verificar que cookies tienen `HttpOnly` y (en prod) `Secure` | [V] | 2 |
| 7.5 | Documentar en README cómo arrancar dev, sembrar DB, migrar a Postgres | [B] | todas |
| 7.6 | Crear `.env.example` completo | [V] | 0.4 |
| 7.7 | Probar `pnpm db:push` contra Postgres (Docker local) y verificar schema compatible | [V] | 1.12 |

**Artefactos:** MVP completo y verificable.

---

## Resumen de dependencias críticas

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 5 ──► Phase 7
                  │                  │              ▲
                  └─► Phase 4 ───────┘              │
                            │                       │
                            └──► Phase 6 ───────────┘
```

---

## Métricas de progreso

| Phase | Tareas | % del MVP |
|-------|--------|-----------|
| 0 — Setup | 10 | 5% |
| 1 — Backend core | 16 | 20% |
| 2 — Auth backend | 11 | 12% |
| 3 — Auth frontend | 13 | 13% |
| 4 — Inscripción backend | 8 | 10% |
| 5 — Inscripción frontend | 16 | 25% |
| 6 — Admin | 7 | 10% |
| 7 — Verificación | 7 | 5% |

---

## Próximo paso del SDD

Correr `sdd-propose` con este plan como input para redactar la propuesta formal del cambio.
