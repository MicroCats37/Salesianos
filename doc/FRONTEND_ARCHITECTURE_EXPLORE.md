# SDD Exploration: Arquitectura Frontend Real + Migración UI desde Mockup

> **Proyecto:** salesianos
> **Fecha:** 2026-09-19
> **Tipo:** Arquitectura — SDD Exploration
> **Fuente mockup:** `frontend-mokup/` (referencia UX/visual — NO es contrato de API)
> **Fuente contracts:** `contract/next-app-architecture-contract.md`, `contract/api-wrapper-presenter-contract.md`, `contract/smart.md`, `doc/FRONTEND_IMPLEMENTATION_FLOW.md`, `doc/BACKEND_DOMAIN_PLAN.md`

---

## Resumen Ejecutivo

El frontend real (`frontend/`) ya tiene una arquitectura sólida: GenericForm, hooks de API, TanStack Query, Zustand, shadcn/ui, y un ejemplo funcional en `features-example-app/`. El mockup define la intención UX/visual pero NO el contrato de API ni la arquitectura correcta. Esta exploración documenta:

1. La arquitectura real del frontend
2. qué UI del mockup se puede copiar visualmente
3. qué lógica debe reconstruirse con GenericForm y hooks
4. Los gaps de backend que bloquean el desarrollo frontend

---

## 1. Estado Actual del Frontend Real

### Stack confirmado

| Librería | Versión | Rol |
|----------|---------|-----|
| Next.js 16 | 16.2.9 | Framework |
| React | 19.2.4 | UI |
| TanStack Query | 5.95.2 | Estado servidor |
| Zustand | 5.0.12 | Estado cliente |
| React Hook Form | 7.72.0 | Estado formulario |
| Zod | 4.3.6 | Validación |
| Axios | 1.14.0 | HTTP client |
| shadcn + Tailwind | v4 | Diseño |

### Estructura de carpetas (contrato)

```
frontend/src/
├── app/                        # Routing ONLY
│   ├── (auth)/login/          # Grupo público
│   ├── (protected)/            # Grupo protegido
│   └── api/                   # Server routes
├── components/
│   ├── ui/                    # shadcn components (Button, Input, Card, etc.)
│   └── genericForm/            # ✅ Core del sistema de formularios
│       ├── GenericForm.tsx     # Orchestrador (Mode 1: children prop)
│       ├── GenericInput.tsx   # Despachador de campos (FieldType registry)
│       └── inputs/            # InputText, InputSelect, InputCheckbox, etc.
├── hooks/
│   ├── callsApi/              # useApiCreate, useApiUpdate, useApiDelete, useApiQuery
│   └── cache/                 # useGenericCreateMutation, etc.
├── errors/
│   ├── error-handler.ts       # handleApiError (parser chain)
│   └── toast-adapter.ts       # notify (usa sonner)
├── lib/
│   ├── api.ts                 # Axios instance + interceptors auth/refresh
│   └── query-client.ts
├── features/                   # ✅ VACÍO — aquí van los nuevos features Salesianos
├── features-example-app/       # Ejemplo funcional existente (referencia)
│   └── auth/                  # Login funcional con GenericForm
└── types/api.types.ts         # ApiResponse<T>, PaginatedResult<T>
```

### GenericForm — 4 Modos de Renderizado

| Modo | Props | Uso | Status |
|------|------|-----|--------|
| Mode 1 | `children` render prop | Production screens | ✅ **REQUIRED** |
| Mode 2 | `fields` array | Prototyping only | ❌ **FORBIDDEN** |
| Mode 3 | `formSections` | Internal admin tools | ❌ **FORBIDDEN** |
| Mode 4 | `formMethods` prop (hybrid) | Multi-step wizards | ✅ When needed |

### Pattern de Feature Module

```
src/features/<dominio>/
├── schemas/
│   ├── login.schema.ts
│   └── index.ts              # granular re-exports (NO wildcard)
├── services/
│   └── login.service.ts
├── hooks/
│   ├── useLogin.ts
│   └── index.ts
├── utils/
│   └── auth.utils.ts
└── components/
    ├── LoginForm.tsx
    └── index.ts              # Solo UI pública
```

---

## 2. Mapa de UI del Mockup

### Landing Page — Copiar visualmente tal cual

| Sección | Archivo mockup | Copiar | Notas |
|---------|---------------|--------|-------|
| Navbar | `landing/Navbar.tsx` | ✅ | Navegación + branding |
| Hero | `landing/Hero.tsx` | ✅ | GSAP animations + cycling words |
| Gallery | `landing/Gallery.tsx` | ✅ | Fotos del evento |
| Paquetes | `landing/Paquetes.tsx` | ✅ | Cards con precio, límite participantes |
| Disciplines | `landing/Disciplines.tsx` | ✅ | Grid de disciplinas |
| Process | `landing/Process.tsx` | ✅ | Pasos del wizard |
| Reglamento | `landing/Reglamento.tsx` | ✅ | Aceptaciones/bases |
| Footer | Inline en `page.tsx` | ✅ | Links sociales + branding |

**GSAP requerido:** El Hero usa animaciones GSAP para entrada y palabra rotatoria (`cancha` → `familia` → `reencuentro` → `promocion`). Ya está en el package.json del frontend real.

### Login — Copiar UI, reconstruir lógica

- **UI:** Tabs DNI/email con gradients y card elevada — copiar visualmente tal cual
- **Lógica:** NO copiar del mockup. Usar GenericForm + `LoginDniFormSchema`/`LoginEmailFormSchema`
- **Hooks:** Implementar `useLogin` que bifurque entre `/auth/login/dni` y `/auth/login/email`

### Register — Copiar UI, reconstruir lógica

- **UI:** Formulario completo con campos de persona + validación de documentos
- **Lógica:** GenericForm con `RegisterFormSchema` usando `superRefine` para validación por tipo de documento (DNI=8 dígitos, CE=9 dígitos, PAS=mínimo 4 alfanuméricos)
- **Endpoints:** `POST /auth/register`

### Wizard Inscripción — Reconstruir completamente

- **UI:** Los 4 pasos se pueden copiar parcialmente (layout, estilos)
- **Lógica:** Reconstruir con GenericForm Mode 4 (`formMethods` prop para wizard)
- **Payload:** `InscripcionPayloadSchema` alineado a `InscripcionCreateIn` del backend

### Dashboard — UI copiable

- Lista de inscripciones del responsable
- Conexión a `GET /inscripciones/`

---

## 3. Anti-patrones a Evitar

| ❌ NO HACER | ✅ CORRECTO |
|-------------|-------------|
| Copiar lógica de formularios del mockup | Usar GenericForm + Zod schemas |
| Usar `fields` array mode en producción | Usar Mode 1 (`children` prop) o Mode 4 (`formMethods`) |
| Poner `buildApiPayload` en `onSubmit` del form | `buildApiPayload` vive en el mutation hook |
| Usar `z.any()` en schemas | Todos los payloads tipados con Zod |
| Duplicar mensajes de error | `GenericInput` + `DefaultFieldWrapper` ya los renderiza |
| Mezclar lógica en `app/` | Toda la lógica va en `features/` |
| Poner `handleApiError` manualmente en cada componente | Fluye por GenericForm automáticamente |

---

## 4. Contrato Mandatory: `contract/smart.md`

> **IMPORTANTE:** `contract/smart.md` es el contrato más importante para preservar la UI del mockup en los formularios.

### Reglas de Formularios con Smart Fields

| Regla | Por qué |
|-------|---------|
| UI del mockup se copia visualmente, nunca la lógica | El mockup define intención UX, no arquitectura |
| Forms usan `GenericForm` + smart fields (`contract/smart.md`) | Desacopla UI de validación/Zod |
| Smart/custom field rendering para matchear cards/layout del mockup | No campos planos por defecto |
| `customFields` para casos domain-specific | Componentes hiper-específicos no van al registro global |
| `DefaultFieldWrapper` + `GenericInput` para errores estándar | Error messages centralizados, no duplicados |

### Patrón Smart Field

```
Mockup UI → Componente Dumb (FileDropzone, etc.) → Capa Adaptadora (InputXxx.tsx con useController)
→ GenericInput.tsx (despachador por type) → GenericForm.tsx (orquestador Zod)
```

**El mockup NO se copia tal cual para lógica.** Solo se usa como referencia visual para:
- Layout de cards y secciones
- Composición visual (estilos, espaciado, tipografía)
- Componentes dumb que pueden reutilizarse (no la lógica de formulario)

---

## 4b. Backend Gaps — Estado Actualizado

| Gap | Endpoint | Estado backend | Prioridad | Notas |
|-----|----------|---------------|-----------|-------|
| Lookup/creación de persona por documento | `POST /inscripciones/` | 🔴 Backend espera `persona_id` existente | Decidir: upsert por documento o lookup previo | Gap real de integración — **requerido antes de F5** |
| Admin: listar todas | `GET /inscripciones/admin/listar` | 🔴 **MISSING** | Solo si admin UI está en scope | Deferido si no es MVP |
| `GET /auth/me` | `/auth/me/` | ⚠️ **Opcional** | Solo si frontend necesita verificar sesión post-login | No requerido para MVP |
| `POST /auth/logout` | `/auth/logout/` | ⚠️ **Opcional** | Solo si backend requiere invalidación server-side | Cliente puede borrar JWT localmente |

### Promoaciones — NO es gap (confirmado 2026-09-19)
`GET /inscripciones/promociones/` **NO es requerido**. El flujo es package-first: el usuario selecciona paquete directamente en Step 1, sin catálogo de promociones intermedio.

### Gaps que YA NO son gaps (backend actualizado)

| Campo/Feature | Antes | Ahora | Fuente |
|---------------|-------|-------|--------|
| `fitnessDeclaration` + `imageConsent` | 🔴 Backend no los acepta | ✅ Backend los acepta en `POST /inscripciones/` | Clarificación 2026-09-19 |
| Login unificado | ⚠️ "¿Se necesita?" | ✅ No requerido — endpoints separados `/auth/login/dni`, `/auth/login/email` existen y el frontend bifurca | Decisión confirmada |
| `GET /bases` como endpoint | 🔴 "MISSING" | ✅ No requerido — aceptaciones van en payload como campos (`acceptedBases`, `fitnessDeclaration`, `imageConsent`) | Decisión confirmada |

---

## 5. Plan de SDD Apply Sugerido

### Batch 1: F-FRONT-SCAFFOLD + F-LANDING
- Crear estructura de features: `auth/`, `inscripciones/`, `catalogos/`
- Copiar `components/landing/` del mockup
- Conectar landing a endpoints reales (disciplinas, paquetes, eventos)
- Landing existente ya hace estas llamadas

### Batch 2: F-AUTH (Login + Register)
- Implementar `features/auth/` completo
- UI del mockup copiada visualmente
- GenericForm con validación Zod
- Login tabs: DNI + Email

### Batch 3: F-CATALOGS + F-INSCRIPCION-WIZARD
- API wrappers para catálogos
- Wizard de inscripción con GenericForm (package-first, sin catálogo promociones)
- **Requiere: participant lookup/create en backend**

### Batch 4: F-DASHBOARD + Admin
- Dashboard del responsable
- Panel del Comité (requiere `GET /inscripciones/admin/listar`)

---

## 6. Archivos a Copiar vs Reconstruir

### Copiar visualmente (UI/styling)

| Mockup | Destino real | Qué copiar |
|--------|-------------|-----------|
| `frontend-mokup/src/components/landing/*` | `frontend/src/components/landing/*` | Todo — GSAP, layout, estilos |
| Login UI (tabs, gradients, cards) | `features/auth/components/LoginForm.tsx` | Estructura visual |
| Register UI | `features/auth/components/RegisterForm.tsx` | Estructura visual |
| Wizard steps UI | `features/inscripciones/components/steps/` | Layout y estilos |

### Reconstruir con GenericForm + hooks

| Feature | Por qué reconstruir |
|---------|---------------------|
| Login form logic | Debe usar GenericForm + hooks del frontend real |
| Register form logic | Debe usar GenericForm + `RegisterFormSchema` con `superRefine` |
| Wizard steps | GenericForm Mode 4 con `formMethods` prop |
| API calls | Deben usar `useApiCreate`, `useApiQuery` del frontend real |
| Auth hooks | Deben seguir el pattern de `useLogin` del frontend real |

---

## 7. Validación de Formularios — Pattern a Seguir

### DNI/CE/PAS con superRefine

```typescript
export const RegisterFormSchema = z.object({...})
  .superRefine((data, ctx) => {
    const { tipoDocumento, numeroDocumento } = data;
    if (tipoDocumento === "DNI") {
      if (!/^\d{8}$/.test(numeroDocumento)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "El DNI debe tener exactamente 8 dígitos numéricos",
          path: ["numeroDocumento"],
        });
      }
    }
    // ... CE y PAS
  });
```

### Checkbox obligatorio con refine

```typescript
acceptedBases: z.boolean().refine((val) => val === true, {
  message: "Debes aceptar las bases del evento",
})
```

---

## 8. Dependencias de Paquetes

El `package.json` del frontend real ya tiene todas las dependencias necesarias:
- `gsap` — para animaciones del Hero
- `@tanstack/react-query`, `react-hook-form`, `zod`, `axios`, `zustand`
- `sonner`, `lucide-react`
- shadcn/ui components

**No se requieren paquetes adicionales.**

---

## 9. Referencias Clave

- `frontend/src/components/genericForm/GenericForm.tsx` — Orchestrador de formularios
- `frontend/src/components/genericForm/GenericInput.tsx` — Tipos `FieldType`, `FormField`
- `frontend/src/hooks/callsApi/useApiCreate.ts` — Pattern de mutation hook
- `frontend/src/features-example-app/auth/` — Ejemplo funcional completo
- `frontend/src/errors/error-handler.ts` — `handleApiError` con parser chain
- **`contract/smart.md`** — **CONTRATO MANDATORY para Smart Fields y preservación de UI mockup**
- `contract/next-app-architecture-contract.md` — Contrato de arquitectura Next.js
- `contract/api-wrapper-presenter-contract.md` — Contrato de wrappers y presenters
- `doc/FRONTEND_IMPLEMENTATION_FLOW.md` — Flujo de implementación con gaps actualizados

---

*Documento generado como resultado de SDD explore phase para arquitectura frontend + mockup migration.*
