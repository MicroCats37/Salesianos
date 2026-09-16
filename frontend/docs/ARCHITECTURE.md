# Arquitectura — Salesianos FEST 2026 (MVP)

> **Cambio SDD:** `salesianos-mvp-foundation`
> **Estado:** Fase `explore` completa. Pendiente `propose` → `spec` → `tasks` → `apply`.
> **Stack:** Next.js 16 + React 19 + TS + Drizzle (SQLite dev / Postgres prod) + JWT (httpOnly cookies) + TanStack Query v5 + Zustand v5 + React Hook Form v7 + Zod v4 + shadcn/ui + Tailwind v4 + Biome.

---

## 1. Resumen ejecutivo

Plataforma de preinscripción deportiva para exalumnos de la Promoción 2002 (Salesianos FEST 2026). El MVP cubre el flujo del responsable (registro, login, inscripción multi-step, consulta de estado) y un panel mínimo del Comité para validar nóminas. Pago con izipay queda fuera del MVP.

---

## 2. Decisiones arquitectónicas (resueltas)

### 2.1 Forma canónica de respuesta API

```typescript
interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ErrorDetail | null;
  meta?: PaginationMeta | null;
}

interface ErrorDetail {
  code: ErrorCode;       // NOT_FOUND | VALIDATION_ERROR | PERMISSION_DENIED | CONFLICT | BUSINESS_ERROR | INTERNAL_ERROR
  message: string;
  details?: Record<string, unknown> | null;
}
```

**Fuente:** `.agent/lab/specs/nextjs-backend/response-format.md` + `.agent/lab/specs/nextjs-backend/error-codes.md`.
**Migración:** actualizar el tipo `ApiResponse` actual en `frontend/src/types/api.types.ts` (hoy usa `{ data, message, success }`).

### 2.2 Estructura de carpetas (merge DDD + features)

```
src/
├── app/                              # PRESENTATION (Next.js)
│   ├── api/auth/                     # Route Handlers: login, logout, me, refresh (httpOnly cookies)
│   ├── actions/                      # Server Actions: inscripcion/create, update-status, etc.
│   ├── (auth)/                       # Route group: login, register
│   ├── (protected)/                 # Route group: dashboard responsable + admin/comite
│   └── _components/                  # UI específico de páginas (sin lógica)
│
├── core/                             # DOMAIN (TypeScript puro — SIN Next, SIN Drizzle)
│   ├── entities/                     # User, Inscripcion, Equipo, Jugador, Disciplina, Categoria
│   ├── types/
│   │   ├── api-response.ts           # ApiResponse<T>, ErrorDetail, PaginationMeta
│   │   └── index.ts
│   ├── errors/
│   │   ├── AppError.ts               # abstract class
│   │   ├── NotFoundError.ts
│   │   ├── ValidationError.ts        # con fieldErrors
│   │   ├── PermissionDeniedError.ts
│   │   ├── ConflictError.ts
│   │   ├── BusinessError.ts
│   │   ├── InternalError.ts
│   │   └── index.ts
│   ├── repositories/                 # interfaces (puertos)
│   │   ├── user.repository.ts
│   │   ├── inscripcion.repository.ts
│   │   └── ...
│   └── use-cases/                    # lógica de negocio
│       ├── auth/
│       │   ├── register-user.ts
│       │   ├── login-user.ts
│       │   └── get-current-user.ts
│       └── inscripcion/
│           ├── create-inscripcion.ts
│           ├── validate-roster.ts    # duplicados, cupo, categoría
│           ├── update-inscripcion-status.ts
│           └── get-inscripcion-by-responsable.ts
│
├── infra/                            # INFRASTRUCTURE (adaptadores)
│   ├── drizzle/
│   │   ├── client.ts                 # env-driven: sqlite (dev) vs postgres (prod)
│   │   ├── schema/                   # tablas
│   │   │   ├── users.ts
│   │   │   ├── sesiones.ts
│   │   │   ├── promociones.ts
│   │   │   ├── inscripciones.ts
│   │   │   ├── equipos.ts
│   │   │   ├── jugadores.ts
│   │   │   ├── disciplinas.ts
│   │   │   ├── categorias.ts
│   │   │   ├── bases.ts
│   │   │   └── index.ts              # barrel
│   │   └── repositories/             # implementaciones
│   │       ├── drizzle-user.repository.ts
│   │       └── ...
│   ├── auth/
│   │   ├── jwt.ts                    # sign + verify con jose
│   │   └── cookies.ts                # server-side cookies (httpOnly, Secure=false en dev)
│   └── services/                     # adaptadores externos (email, storage)
│
└── features/                         # FRONTEND BUSINESS LOGIC
    ├── auth/
    │   ├── schemas/                  # LoginFormSchema, RegisterFormSchema, MeResponseSchema
    │   ├── services/                 # login(), register(), logout(), me() — llaman Route Handlers
    │   ├── hooks/                    # useLogin, useRegister, useCurrentUser
    │   ├── store/                    # zustand slice (session cache, NO tokens)
    │   ├── utils/                    # formatAuthError, etc.
    │   └── components/               # LoginForm, RegisterForm, AuthHydrationShell
    ├── inscripcion/
    │   ├── schemas/                  # Wizard step schemas + InscripcionPayloadSchema
    │   ├── services/                 # createInscripcion(), getMyInscripcion()
    │   ├── hooks/                    # useCreateInscripcion, useMyInscripcion
    │   ├── components/               # InscripcionWizard (AppStepperFormModal wrapper), step components
    │   └── views/                    # DashboardResponsableView
    └── admin/
        └── inscripciones/
            ├── schemas/
            ├── hooks/                # useAllInscripciones, useUpdateStatus
            ├── components/           # InscripcionListTable, StatusChangeDialog
            └── views/                # AdminComiteView
```

### 2.3 Capa de auth — Route Handlers + Server Actions

| Operación | Capa | Razón |
|-----------|------|-------|
| `POST /api/auth/register` | **Route Handler** | Set cookies httpOnly server-side |
| `POST /api/auth/login` | **Route Handler** | Set cookies httpOnly server-side |
| `POST /api/auth/logout` | **Route Handler** | Clear cookies server-side |
| `GET /api/auth/me` | **Route Handler** | El interceptor de `api.ts` consume este endpoint |
| `POST /api/auth/refresh` | **Route Handler** | Rotación de tokens |
| Mutations de inscripción | **Server Action** | Internal mutation, revalidate automático |
| Status change (Comité) | **Server Action** | Permiso verificado server-side |
| Reads con datos del usuario | **Server Component** | Data fetch directo en la página |

**Excepción documentada:** la spec `nextjs-backend/folder-structure.md` dice "Route Handlers solo para webhooks externos". Esta regla apunta al CRUD de negocio, **no** al contrato externo de auth. Auth es la única excepción porque requiere setear cookies httpOnly en el response.

### 2.4 JWT — cookies httpOnly + Secure condicional

```typescript
// infra/auth/cookies.ts (server-side, Route Handlers only)
cookies().set('auth-token', token, {
  httpOnly: true,                        // anti-XSS
  secure: process.env.NODE_ENV === 'production',  // false en dev (http), true en prod (https)
  sameSite: 'lax',
  path: '/',
  maxAge: 60 * 60 * 24 * 7,             // 7 días access token
});
```

**Importante:** el frontend **nunca** llama `cookies-next.setCookie`. Solo los Route Handlers de auth escriben cookies. `useLogin` solo invoca `POST /api/auth/login`.

### 2.5 Base de datos — Drizzle driver-agnostic

```typescript
// infra/drizzle/client.ts
import { drizzle as drizzleSqlite } from 'drizzle-orm/better-sqlite3';
import { drizzle as drizzlePostgres } from 'drizzle-orm/postgres-js';

const url = process.env.DATABASE_URL!;
export const db = url.startsWith('file:')
  ? drizzleSqlite(new Database(url.replace('file:', '')))
  : drizzlePostgres(url);
```

`schema/` no contiene código driver-específico. Mismo schema push a SQLite o Postgres.

---

## 3. Patrones aplicados

| Patrón | Fuente | Aplicación |
|--------|--------|------------|
| DDD/Hexagonal backend | `.agent/lab/specs/nextjs-backend/folder-structure.md` | `src/core/` puro + `src/infra/` adapters |
| GenericForm Mode 4 (Hybrid) | `.agent/lab/specs/nextjs/forms/SPEC.md` | Wizard multi-step de inscripción |
| AppStepperFormModal | `frontend/src/components-app/forms/AppStepperFormModal.tsx` | Container del wizard |
| TanStack Query v5 | `.agent/skills/tanstack-query/` | Server state para `me`, `myInscripcion` |
| Zustand v5 slices | `.agent/skills/zustand-state-management/` | Session cache + UI state |
| `buildApiPayload` en hook | `.agent/lab/specs/nextjs/forms/SPEC.md` | Auto-detecta File → FormData |
| `handleApiError` + notify adapter | `.agent/lab/specs/shared/error-handling.md` | Errores centralizados |
| Error code registry | `.agent/lab/specs/nextjs-backend/error-codes.md` | 6 codes, mapeo HTTP |
| Composición sobre herencia de schemas | `contract/SCHEMA_DRY_INTENTION.md` | Bloques General + Específico + Identidad |
| Wrappers tipados por feature | `contract/api-wrapper-presenter-contract.md` | Sin `z.any()` |

---

## 4. Esquema de datos (Drizzle, propuesto)

```
users                sesiones               bases
───────              ────────               ─────
id (uuid pk)         id (uuid pk)           id (uuid pk)
email (unique)       user_id (fk users)     version (text)        — ej. "BASES-SF26-2026-09-06"
password_hash        token_hash             aprobado_en (date)
nombre               expires_at             contenido_url (text, nullable)
telefono             user_agent (nullable)  activo (boolean)
dni (unique)         ip (nullable)
rol (enum:           revoked_at (nullable)
  responsable,
  admin_comite,
  admin_finanzas)
created_at
updated_at

promociones (catálogo)
────────────────────
id (uuid pk)
anio (int, unique)        — ej. 2002
colegio (enum: sjb, ma)
activa (boolean)

inscripciones            equipos                 jugadores
─────────────            ───────                 ─────────
id (uuid pk)             id (uuid pk)            id (uuid pk)
user_id (fk users)       inscripcion_id (fk)     equipo_id (fk)
promocion_id (fk)        disciplina_id (fk)      dni (text)
paquete_monto (decimal)  categoria_id (fk)       nombres (text)
status (enum:            created_at              apellidos (text)
  recibida,                                          fecha_nacimiento (date)
  en_revision,                                       created_at
  observada,
  validada,
  pago_pendiente,
  pagada,
  confirmada,
  rechazada)
observacion (text, nullable)
created_at
updated_at

disciplinas (catálogo)
──────────────────────
id (uuid pk)
codigo (enum: fulbito_var, fulbito_dam, voley_mix, basket_var)
nombre (text)
max_jugadores (int)

categorias (catálogo)
─────────────────────
id (uuid pk)
disciplina_id (fk)
codigo (text)            — junior, senior, master, super_master
nombre (text)
anio_min (int)           — para validar fecha_nacimiento
anio_max (int)
```

---

## 5. Riesgos y mitigaciones

| # | Riesgo | Mitigación |
|---|--------|------------|
| R1 | `useLogin` viejo setea cookies client-side (`httpOnly: false`) — no reusable tal cual | Reescribir `useLogin` para que solo llame `POST /api/auth/login`; las cookies las setea el Route Handler |
| R2 | Doble escritura de cookies (server + client) | Convención: solo Route Handlers escriben cookies auth; eliminar `setCookie` en hooks |
| R3 | `better-sqlite3` es síncrono, no compatible con Edge Runtime | Dev usa Node runtime; documentar constraint; migrar a `@neondatabase/serverless` si Edge es necesario |
| R4 | Zod v4 vs v3 API drift | Verificar `safeParse`, `flatten().fieldErrors`, `z.infer` con la versión instalada (`^4.3.6`) |
| R5 | `AppStepperFormModal` + `GenericForm` Mode 4 — race condition si el usuario cierra el modal a mitad de paso | Usar `onBeforeClose` del GenericModal + estado limpio en cada step transition |

---

## 6. Flujo de inscripción (4 steps)

```
[STEP 1: Responsable]      → datos personales + contacto
        ↓
[STEP 2: Promoción]        → año egreso + colegio + nombre equipo
        ↓
[STEP 3: Disciplinas]      → 1-4 disciplinas × (categoría + nómina de jugadores)
        ↓                          ↑ repetidor dinámico (mín 5, máx según disciplina)
[STEP 4: Aceptación]       → checkboxes bases + declaración jurada + submit
        ↓
[POST /api/auth/login]  ó  [createInscripcionAction] → InscripcionWizard
                                                       ↓
                                              [DASHBOARD DEL RESPONSABLE]
                                                       ↓
                                            (status polled via TanStack Query)
```

Validaciones server-side por step:
- STEP 1: email único, DNI formato (8 dígitos PE), teléfono 9 dígitos PE
- STEP 2: promoción activa y existe
- STEP 3: sin duplicados de DNI en la misma nómina, max_jugadores respetado, categoría dentro de rango etario
- STEP 4: ambos checkboxes requeridos

---

## 7. Panel del Comité (admin)

```
/admin/comite/inscripciones
├── Lista paginada (estado, promoción, fecha, responsable)
├── Detalle de inscripción (verifica nómina)
└── Acción: cambiar status
    ├── EN_REVISION → VALIDADA
    ├── EN_REVISION → OBSERVADA (con mensaje al responsable)
    ├── EN_REVISION → RECHAZADA (con razón)
```

Sin edición de nómina. Solo cambio de estado + observación.

---

## 8. Lo que NO está en el MVP

- Pago con izipay (banner bloqueado, como en el mockup)
- Módulo de finanzas
- Notificaciones automáticas por email/WhatsApp (las observaciones se ven en dashboard)
- Integración con padrón de exalumnos
- Multi-idioma
- 2FA
- Refresh token (access token de 7 días, después re-login)

---

## 9. Próximos pasos

1. **sdd-propose** — redactar propuesta formal del cambio
2. **sdd-spec** — escribir specs de cada módulo (auth, inscripcion, admin)
3. **sdd-tasks** — convertir el plan de fases en tareas implementables
4. **sdd-apply** — ejecutar tareas en orden
5. **sdd-verify** — validar contra specs

---

## Referencias

- [Documentación del mockup](./mockup-documentation.md)
- [Explore en Engram: `sdd/salesianos-mvp-foundation/explore`]
- [Contratos del proyecto](../contract/)
- [Specs internas `.agent/lab/specs/`](../.agent/lab/specs/)
- [Frontend viejo reutilizable](../frontend/src/)
