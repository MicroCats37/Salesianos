# Salesianos FEST 2026

Plataforma de preinscripción deportiva — Promoción 2002 / Rumbo a Bodas de Plata.

> Evento: Sábado 21 de noviembre de 2026, Av. Asturias 588 — Ate.
> Documento de bases: `BASES-SF26-2026-09-06` (aprobado 2026-09-05).

## Stack

- **Framework:** Next.js 16 + React 19 + TypeScript
- **ORM:** Drizzle (SQLite dev / Postgres prod)
- **Auth:** JWT en cookies httpOnly (jose)
- **Data:** TanStack Query v5 + Zustand v5
- **Forms:** React Hook Form v7 + Zod v4
- **UI:** shadcn/ui + Tailwind v4

## Setup local

```bash
# 1. Instalar dependencias
npm install

# 2. Configurar env (ya hay .env.local con valores de dev)
cp .env.example .env.local  # si no existe

# 3. Crear DB SQLite y aplicar schema
npm run db:push

# 4. Sembrar catálogos + admin user
npm run db:seed

# 5. Dev server
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000).

## Credenciales de admin (después del seed)

- **Email:** `admin@salesianosfest.com`
- **Password:** `Admin2026!`

## Estructura

```
src/
├── app/
│   ├── (auth)/          # /login, /register (layout con AuthHydrationShell)
│   ├── (protected)/      # /dashboard, /inscripcion, /admin/comite
│   ├── api/auth/        # Route Handlers: register, login, logout, me
│   ├── actions/         # Server Actions: inscripcion/create, update-status
│   ├── _lib/            # jsonSuccess, jsonFromUnknownError helpers
│   └── layout.tsx       # root layout (ReactQueryProvider)
├── core/                # Domain puro (sin imports de Next/Drizzle)
│   ├── entities/, errors/, repositories/, types/, use-cases/
├── infra/               # Infrastructure adapters
│   ├── auth/             # jwt.ts, cookies.ts (httpOnly server-side)
│   └── drizzle/          # client.ts, schema/, repositories/, seed.ts
├── features/             # Frontend business logic
│   ├── auth/             # schemas, services, hooks, store, components
│   ├── inscripcion/      # wizard schemas + InscripcionWizard
│   └── admin/inscripciones/  # list + status change
├── lib/                  # Axios + TanStack Query config
├── providers/            # ReactQueryProvider
├── shared/types/         # ApiResponse<T> canónico
├── components/           # GenericForm, GenericModal, ui/, etc.
├── components-app/       # AppFormModal, AppStepperFormModal, PageWrapper
├── hooks/                # useApiCreate/Update/Delete/Query
├── errors/               # handleApiError, toast-adapter
└── proxy.ts              # Next.js 16 auth pre-filter
docs/                     # ARCHITECTURE.md, PLAN.md, mockup-documentation.md, django-orchestrator-flow-core.md
```

## Scripts

| Script | Descripción |
|--------|-------------|
| `npm run dev` | Dev server |
| `npm run build` | Build producción |
| `npm run start` | Start producción |
| `npm run lint` | Biome check |
| `npm run lint:fix` | Biome check --write |
| `npm run format` | Biome format --write |
| `npm run typecheck` | tsc --noEmit |
| `npm run db:push` | Aplicar schema a SQLite |
| `npm run db:studio` | Drizzle Studio |
| `npm run db:seed` | Sembrar catálogos |

## Documentación

- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) — Arquitectura técnica consolidada
- [docs/PLAN.md](./docs/PLAN.md) — Plan de implementación por fases
- [docs/mockup-documentation.md](./docs/mockup-documentation.md) — Inventario del mockup original
- [docs/django-orchestrator-flow-core.md](./docs/django-orchestrator-flow-core.md) — Patrón Django 4-capas (referencia)
