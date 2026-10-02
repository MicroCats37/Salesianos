# Frontend Modular Tasks — Salesianos FEST 2026

> **Proyecto:** salesianos
> **Fecha:** 2026-09-19
> **Tipo:** SDD Exploration — Plan de tareas modulares para apply
> **Fuente:** Exploración SDD `sdd/salesianos-frontend-modular-task-plan/explore`
> **Contracts:** `contract/smart.md` (mandatory), `contract/next-app-architecture-contract.md`, `contract/api-wrapper-presenter-contract.md`

---

## Resumen Ejecutivo

Plan de tareas modulares para implementar el frontend de Salesianos FEST 2026 sobre la arquitectura existente (`GenericForm`, TanStack Query, Zustand, shadcn/ui). El mockup define la intención UX/visual; la lógica se construye con los patrones del frontend real.

**Nota:** `promociones` NO es un gap frontend/backend. El flujo es package-first.

---

## Contratos Mandatory

| Contrato | Archivo | Relevancia |
|----------|---------|------------|
| **Smart Fields** | `contract/smart.md` | **MANDATORY** — preservar UI mockup con GenericForm/smart fields |
| Arquitectura Next.js | `contract/next-app-architecture-contract.md` | Folder structure, naming, anti-patterns |
| API Wrappers | `contract/api-wrapper-presenter-contract.md` | Frontend schemas deben mirror backend wrappers |
| Schema DRY | `contract/SCHEMA_DRY_INTENTION.md` | Composición de schemas |

---

## Reglas Explícitas para Apply

### Regla Visual: Colores en Tokens CSS
> La UI del mockup se copia VISUALMENTE tal cual. CUALQUIER color debe usar tokens CSS de `globals.css` (`--primary`, `--accent`, `--background`, etc.) o clases de tailwind. **NO hardcodear** `color: #312e8e` en componentes. Si el token no existe, agregarlo a `globals.css` primero.

### Regla de Formularios: Smart Fields + GenericForm
> La UI del mockup se preserva via smart fields/custom renderers. La lógica de formulario usa **exclusivamente** GenericForm + Zod schemas + hooks del frontend real. **NO copiar lógica** de formularios del mockup.

### Regla de Payload: buildApiPayload en Hook
> `buildApiPayload` vive en el mutation hook, **NUNCA** en el `onSubmit` del form.

### Regla de Errores: handleApiError Automático
> Los errores fluyen por `handleApiError()` a través de GenericForm automáticamente. **NO manejar errores manualmente** en componentes.

---

## Fases de Implementación

### F1-LANDING: Copiar UI del Mockup

**Goal:** Landing page pública funcional con GSAP, conectando a endpoints reales.

**Source/Reference:**
- `frontend-mokup/src/components/landing/*` (Navbar, Hero, Gallery, Paquetes, Disciplines, Process, Reglamento)
- `frontend/src/app/globals.css` — design tokens CIP ya definidos

**Files likely touched:**
- `frontend/src/app/page.tsx` → reemplazar redirect por landing real
- `frontend/src/components/landing/*` → copiar componentes visuales
- `frontend/src/features/landing/components/*` → layout GSAP

**Out of scope:**
- Lógica de autenticación
- Wizard de inscripción
- Dashboard

**Contracts/Docs to read before apply:**
1. `contract/smart.md` — mandatory
2. `contract/next-app-architecture-contract.md`
3. `frontend/src/app/globals.css` — design tokens CIP ya definidos
4. `frontend/src/lib/api.ts` — Axios instance
5. `frontend/src/hooks/callsApi/useApiQuery.ts` — patrón de query

**Verification:**
```bash
npm run dev
# Navegar a http://localhost:3000
# Verificar: Hero GSAP, navbar sticky, secciones scroll, GSAP orbs
```

**Acceptance Criteria:**
- [ ] Landing visible en `/` con todos los componentes del mockup
- [ ] GSAP animations funcionan (reduced-motion respetado)
- [ ] Navbar scroll-aware con backdrop-blur
- [ ] Botones de CTA pointing a `/register`, `/login`
- [ ] NO hardcoded colors en componentes — usar tokens CSS
- [ ] NO lógica de formularios copiada

---

### F2-FRONT-SCAFFOLD: Estructura de Features

**Goal:** Crear la estructura vacía de features `auth/`, `inscripciones/`, `catalogos/` bajo `src/features/`.

**Source/Reference:**
- `frontend/src/features-example-app/` (estructura de referencia)
- `contract/next-app-architecture-contract.md` (sección 1 y 2)

**Files likely created:**
```
frontend/src/features/
├── auth/
│   ├── schemas/index.ts
│   ├── services/index.ts
│   ├── hooks/index.ts
│   ├── utils/index.ts
│   └── components/index.ts
├── catalogos/
│   ├── schemas/index.ts
│   ├── services/index.ts
│   ├── hooks/index.ts
│   └── components/index.ts
└── inscripciones/
    ├── schemas/index.ts
    ├── services/index.ts
    ├── hooks/index.ts
    └── components/
        ├── steps/
        └── index.ts
```

**Out of scope:**
- Implementación de componentes
- Conexión a endpoints

**Contracts/Docs to read before apply:**
1. `contract/next-app-architecture-contract.md` — sección 1 (folder structure) y 2 (naming conventions)

**Verification:**
```bash
ls frontend/src/features/
# Debe mostrar: auth/ catalogos/ inscripciones/
```

**Acceptance Criteria:**
- [ ] Carpetas creadas con `index.ts` barrel exports
- [ ] Naming conventions seguidas (`LoginFormSchema`, `useLogin`, etc.)
- [ ] NO wildcard re-exports

---

### F3-AUTH: Login + Register con GenericForm

**Goal:** Login (tabs DNI/email) y Register funcional con GenericForm, smart fields, y endpoints reales.

**Source/Reference:**
- `frontend-mokup/src/features/auth/components/LoginForm.tsx` (UI visual)
- `frontend-mokup/src/features/auth/components/RegisterForm.tsx` (UI visual)
- `frontend/src/components/genericForm/GenericForm.tsx` (orchestrador)
- `frontend/src/hooks/callsApi/useApiCreate.ts` (patrón mutation)
- `contract/smart.md` — mandatory para smart fields

**Files likely touched:**
- `frontend/src/features/auth/schemas/login.schema.ts`
- `frontend/src/features/auth/schemas/register.schema.ts`
- `frontend/src/features/auth/services/auth.service.ts`
- `frontend/src/features/auth/hooks/useLogin.ts`
- `frontend/src/features/auth/hooks/useRegister.ts`
- `frontend/src/features/auth/components/LoginForm.tsx`
- `frontend/src/features/auth/components/RegisterForm.tsx`
- `frontend/src/app/(auth)/login/page.tsx` → completar
- `frontend/src/app/(auth)/register/page.tsx` → crear

**Out of scope:**
- `/auth/me` y `/auth/logout` (opcionales, ver blockers)
- Dashboard post-login redirect logic

**Contracts/Docs to read before apply:**
1. `contract/smart.md` — **MANDATORY**
2. `contract/next-app-architecture-contract.md` — secciones 3, 4, 5
3. `frontend/src/components/genericForm/GenericForm.tsx`
4. `frontend/src/hooks/callsApi/useApiCreate.ts`
5. `doc/FRONTEND_ARCHITECTURE_EXPLORE.md` — sección 7 (validación con superRefine)

**Verification:**
```bash
npm run dev
# POST /auth/login/dni con {dni, password}
# POST /auth/login/email con {email, password}
# POST /auth/register con payload del schema
```

**Acceptance Criteria:**
- [ ] Login con tabs DNI/Email — UI copiada del mockup visualmente
- [ ] Register con validación superRefine (DNI=8 dígitos, CE=9, PAS=mín 4 alfanum)
- [ ] GenericForm Mode 1 (`children` prop)
- [ ] Smart fields para preserve UI del mockup
- [ ] `buildApiPayload` en mutation hook, NO en onSubmit
- [ ] `handleApiError` fluye por GenericForm automáticamente
- [ ] POST `/auth/register` → redirect a login o auto-login
- [ ] Redirect post-login: admins→`/admin/dashboard`, responsables→`/dashboard`

---

### F4-CATALOGS: Hooks de Catálogos

**Goal:** API wrappers y hooks para paquetes, disciplinas, eventos, categorías.

**Source/Reference:**
- `frontend/src/hooks/callsApi/useApiQuery.ts` (patrón query)
- `doc/FRONTEND_IMPLEMENTATION_FLOW.md` — sección de endpoints

**Files likely touched:**
- `frontend/src/features/catalogos/schemas/paquetes.schema.ts`
- `frontend/src/features/catalogos/schemas/disciplinas.schema.ts`
- `frontend/src/features/catalogos/schemas/eventos.schema.ts`
- `frontend/src/features/catalogos/services/catalogos.service.ts`
- `frontend/src/features/catalogos/hooks/usePaquetes.ts`
- `frontend/src/features/catalogos/hooks/useDisciplinas.ts`
- `frontend/src/features/catalogos/hooks/useEventos.ts`
- `frontend/src/features/catalogos/hooks/useCategorias.ts`

**Endpoints a consumir:**
| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/inscripciones/disciplinas/` | Listar disciplinas activas |
| GET | `/inscripciones/disciplinas/{id}/categorias/` | Categorías por disciplina |
| GET | `/inscripciones/paquetes/` | Listar paquetes activos |
| GET | `/inscripciones/paquetes/{id}/disciplinas/` | Disciplinas de un paquete |
| GET | `/inscripciones/eventos/` | Listar eventos activos |

**Out of scope:**
- `GET /inscripciones/promociones/` (no requerido en flujo package-first)
- Panel admin

**Contracts/Docs to read before apply:**
1. `contract/next-app-architecture-contract.md` — secciones 3, 4
2. `contract/api-wrapper-presenter-contract.md` — sección 7 (frontend schema mirror)
3. `frontend/src/hooks/callsApi/useApiQuery.ts`

**Verification:**
```bash
# En landing page o wizard, verificar:
# - useDisciplinas() returns disciplinas
# - usePaquetes() returns paquetes
# - useEventos() returns eventos
```

**Acceptance Criteria:**
- [ ] Typed schemas para cada catálogo (Zod, alineado a backend wrapper)
- [ ] TanStack Query `queryOptions` pattern
- [ ] snake_case → camelCase transformation en service
- [ ] Stale time apropiado (5 min para catálogos)
- [ ] Error handling via `handleApiError`

---

### F5-INSCRIPCION-WIZARD: Wizard Package-First

**Goal:** Wizard de inscripción en 4 pasos con GenericForm Mode 4 (`formMethods` prop), smart fields, y submit completo a `POST /inscripciones/`.

**Source/Reference:**
- `frontend-mokup/src/features/inscripcion/components/InscripcionWizard.tsx` (UI visual steps)
- `frontend-mokup/src/features/inscripcion/components/steps/Step*.tsx` (cada paso)
- `frontend/src/components/genericForm/GenericForm.tsx` — Mode 4 (`formMethods` prop)
- `contract/smart.md` — **MANDATORY**

**Files likely touched:**
- `frontend/src/features/inscripciones/schemas/inscripcion-payload.schema.ts`
- `frontend/src/features/inscripciones/schemas/step*.schema.ts`
- `frontend/src/features/inscripciones/services/inscripcion.service.ts`
- `frontend/src/features/inscripciones/hooks/useCreateInscripcion.ts`
- `frontend/src/features/inscripciones/hooks/useInscripcionDetail.ts`
- `frontend/src/features/inscripciones/components/InscripcionWizard.tsx`
- `frontend/src/features/inscripciones/components/steps/Step1Package.tsx`
- `frontend/src/features/inscripciones/components/steps/Step2Team.tsx`
- `frontend/src/features/inscripciones/components/steps/Step3Participants.tsx`
- `frontend/src/features/inscripciones/components/steps/Step4Declarations.tsx`
- `frontend/src/app/(protected)/inscripcion/page.tsx`

**Payload alignment (InscripcionCreateIn):**
```typescript
{
  evento_id: string,
  paquete_id: string,
  promocion_id: string | null,
  fusion_promocion_id: string | null,
  observacion: string | null,
  accepted_bases: boolean,
  fitness_declaration: boolean,  // ✅ Aceptado por backend
  image_consent: boolean,        // ✅ Aceptado por backend
  equipos: [{
    disciplina_id: string,
    categoria_id: string | null,
    nombre: string,
    participantes: [{
      persona_id: string,  // UUID — debe existir (ver blockers)
      rol: "JUGADOR" | "CAPITAN" | "DELEGADO",
      talle_camiseta: string | null
    }]
  }]
}
```

**Out of scope:**
- `GET /inscripciones/promociones/` (flujo package-first no lo requiere)
- Admin panel

**Contracts/Docs to read before apply:**
1. `contract/smart.md` — **MANDATORY**
2. `contract/next-app-architecture-contract.md` — sección 5 (Forms Architecture)
3. `frontend/src/components/genericForm/GenericForm.tsx` — Mode 4
4. `doc/FRONTEND_IMPLEMENTATION_FLOW.md` — sección 2.2 (payload analysis)

**Verification:**
```bash
npm run dev
# Ir a /inscripcion
# Step 1: seleccionar paquete
# Step 2: crear equipo (nombre + disciplina)
# Step 3: agregar participantes (nombre, doc, rol)
# Step 4: aceptaciones
# Submit → POST /inscripciones/
```

**Acceptance Criteria:**
- [ ] Wizard 4 pasos con GenericForm Mode 4 (`formMethods` prop)
- [ ] Step 1: Package-first — selector de paquete (no catálogo promociones)
- [ ] Step 2: Equipo — nombre + disciplina (categoria nullable)
- [ ] Step 3: Participantes — tabla con persona_id (ver blockers)
- [ ] Step 4: Declaraciones (`acceptedBases`, `fitnessDeclaration`, `imageConsent`)
- [ ] Smart fields para preservar UI del mockup
- [ ] `buildApiPayload` en mutation hook
- [ ] `fitnessDeclaration` + `imageConsent` en payload ✅
- [ ] Redirect a `/dashboard` post-submit exitoso

---

### F6-DASHBOARD: Mis Inscripciones

**Goal:** Dashboard del responsable mostrando sus inscripciones con opción a editar.

**Source/Reference:**
- `frontend-mokup/src/features/inscripcion/views/ResponsableDashboardView.tsx` (UI)
- `frontend/src/hooks/callsApi/useApiQuery.ts` (patrón query)
- `frontend/src/hooks/callsApi/useApiUpdate.ts` (patrón update)

**Files likely touched:**
- `frontend/src/features/inscripciones/schemas/inscripcion-list.schema.ts`
- `frontend/src/features/inscripciones/services/inscripcion.service.ts`
- `frontend/src/features/inscripciones/hooks/useMyInscripciones.ts`
- `frontend/src/features/inscripciones/hooks/useUpdateInscripcion.ts`
- `frontend/src/features/inscripciones/components/InscripcionList.tsx`
- `frontend/src/features/inscripciones/components/InscripcionEditModal.tsx`
- `frontend/src/app/(protected)/dashboard/page.tsx`

**Endpoints a consumir:**
| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/inscripciones/` | Lista del responsable |
| GET | `/inscripciones/{id}` | Detalle |
| PATCH | `/inscripciones/{id}` | Actualizar |

**Out of scope:**
- Admin panel (`GET /inscripciones/admin/listar`)
- Panel Comité

**Contracts/Docs to read before apply:**
1. `contract/next-app-architecture-contract.md` — secciones 3, 4
2. `frontend/src/hooks/callsApi/useApiQuery.ts`
3. `frontend/src/hooks/callsApi/useApiUpdate.ts`

**Verification:**
```bash
npm run dev
# Login como responsable
# Ir a /dashboard
# Ver lista de inscripciones del responsable
```

**Acceptance Criteria:**
- [ ] Lista de inscripciones del responsable desde `GET /inscripciones/`
- [ ] Detalle de inscripción desde `GET /inscripciones/{id}`
- [ ] Edición inline de participantes/equipos via `PATCH /inscripciones/{id}`
- [ ] Estados mostrados con badge/badge visual
- [ ] Botón a `/inscripcion` si no tiene inscripciones

---

## Backend Blockers — Análisis Realista

| Blocker | Endpoint | Impacto | Estado |
|---------|----------|---------|--------|
| **participant person lookup/create** | `POST /inscripciones/` espera `persona_id` existente | 🔴 CRÍTICO — Wizard Step 3 no puede enviar participantes sin esto | Gap real de integración |
| **Admin list endpoint** | `GET /inscripciones/admin/listar` | 🔴 Admin panel no funcional | Deferido si no es MVP |
| `GET /auth/me` | `/auth/me/` | ⚠️ Opcional — cliente puede leer de cookies JWT | Opcional |
| `POST /auth/logout` | `/auth/logout/` | ⚠️ Opcional — cliente puede borrar JWT localmente | Opcional |
| `GET /inscripciones/promociones/` | Catálogo promociones | ✅ NO ES BLOQUEADOR — flujo package-first no lo requiere | Confirmado 2026-09-19 |

### Decisión Requerida: participant lookup/create

**Problema:** El mockup envía datos de persona nueva (tipo, numero, nombres) en `deportistas[]`. El backend espera `persona_id` (UUID) existente.

**Opciones:**
1. **Backend**: Crear endpoint `POST /personas/lookup-or-create` que busque por documento y cree si no existe
2. **Backend**: Modificar `POST /inscripciones/` para hacer upsert de personas por documento
3. **Frontend**: Pre-buscar persona existente antes de enviar, mostrar error si no existe

**Recomendación:** Opción 1 o 2 (backend decide) — requerido antes de F5.

---

## Orden de Apply Recomendada

```
F2-FRONT-SCAFFOLD  → Estructura vacía (prerrequisito)
F1-LANDING         → Copy UI visual (sin lógica)
F3-AUTH            → Login + Register
F4-CATALOGS        → Hooks de catálogos
F5-INSCRIPCION     → Wizard (requiere: participant lookup/create)
F6-DASHBOARD       → Mis inscripciones
```

**Nota:** F5 requiere que el backend implemente participant lookup/create antes o durante F5.

---

## Referencias Clave

- `frontend/src/components/genericForm/GenericForm.tsx` — Orchestrador de formularios (4 modos)
- `frontend/src/components/genericForm/GenericInput.tsx` — Tipos `FieldType`, `FormField`
- `frontend/src/hooks/callsApi/useApiCreate.ts` — Pattern de mutation hook
- `frontend/src/hooks/callsApi/useApiQuery.ts` — Pattern de query hook
- `frontend/src/features-example-app/` — Ejemplo funcional completo
- `frontend/src/errors/error-handler.ts` — `handleApiError` con parser chain
- **`contract/smart.md`** — **CONTRATO MANDATORY para Smart Fields y preservación de UI mockup**
- `contract/next-app-architecture-contract.md` — Contrato de arquitectura Next.js
- `contract/api-wrapper-presenter-contract.md` — Contrato de wrappers y presenters
- `doc/FRONTEND_IMPLEMENTATION_FLOW.md` — Flujo de implementación con gaps actualizados
- `doc/FRONTEND_ARCHITECTURE_EXPLORE.md` — Arquitectura frontend real + plan de migración UI

---

*Documento generado como resultado de SDD explore phase para plan de tareas frontend modular — 2026-09-19*
