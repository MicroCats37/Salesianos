# Exploration: register-unhandled-rejection

## Topic
Diagnóstico del error `unhandledRejection: Error: Error al crear la cuenta` al crear cuenta en el frontend.

## Current State

El flujo de registro es:
1. `RegisterForm` → `useRegister.mutateAsync(data)` (línea 492, `RegisterForm.tsx`)
2. `useRegister.mutationFn` → `registerUser(payload)` (línea 44, `useRegister.ts`)
3. `registerUser` → `api.post("/auth/register", payload)` (línea 14, `register.service.ts`)
4. Backend: `RegistroController.register` → `RegistroOrchestrator.registrar` → `RegistroFlujo._proceso_registro`
5. En caso de error (409 email duplicado, 409 documento ya registrado), backend lanza `HttpError` con mensaje apropiado

**El problema:** Cuando el backend retorna error, `api.post` rechaza con `AxiosError`. Esto se propaga así:
- `registerUser` rejects con `AxiosError`
- `mutationFn` no captura, el Error se escapa
- `GenericForm.handleFormSubmit` (línea 327-340) captura el error, muestra toast, y **re-lanza con `throw e`** (línea 340)
- `RegisterForm.onSubmit` hace `await registerMutation.mutateAsync(data)` **sin `.catch()`**
- El error se convierte en `unhandledRejection` en el browser

## Affected Areas

### Causa raíz (frontend/auth):
- **`frontend/src/components/genericForm/GenericForm.tsx:340`** — `throw e` después de capturar el error causa propagación
- **`frontend/src/features/auth/components/RegisterForm.tsx:492`** — `await registerMutation.mutateAsync(data)` sin manejo de errores
- **`frontend/src/lib/api.ts`** — Reescritura completa eliminó `unwrap()` y `ApiCallError`; el response interceptor actual solo maneja 401

### Middleware del error:
- **`frontend/src/features/auth/hooks/useRegister.ts:46`** — `throw new Error(response.error?.message ?? "Error al crear la cuenta")` lanza cuando `response.success === false`
- **`frontend/src/features/auth/services/register.service.ts:14`** — `api.post` retorna solo si hay 2xx; si no, rechaza con `AxiosError`

### Backend (NO es la causa):
- **`backend/modules/usuarios/domain/services/flujos/registro_flujo.py:191-193, 252-255`** — Manejo correcto de `IntegrityError` para email duplicado
- **`backend/modules/usuarios/presentation/controllers/registro_controller.py:55`** — `success_response(RegistroPresenter.present_registro(result))`

## Analysis: Why NOW

### Antes (git diff muestra):
```diff
# api.ts anterior tenía:
- unwrap<T>(response) que manejaba ApiResponse<T> y lanzaba ApiCallError
- Response interceptor tenía manejo específico para 401
# useRegister anterior:
- mutationFn original: throw new Error(response.error?.message ?? "Register failed")
```

### Ahora:
1. `api.ts` fue reescrito completamente — eliminó `unwrap()` que envolvía la respuesta
2. `registerUser` ahora retorna directamente `ApiResponse<RegisterResponse>` de `api.post()`
3. Cuando backend retorna 409, `api.post` **rechaza** con `AxiosError` (no retorna respuesta)
4. El `response.error?.message` en `useRegister.ts:46` **nunca se ejecuta** porque `registerUser` ya rechazó
5. El error se propaga como `AxiosError`, no como el mensaje esperado

### El problema específico del `throw e` en GenericForm:
- `GenericForm.tsx:340` hace `throw e` después de capturar el error
- Esto es intencional para que React Hook Form pueda manejar errores de validación
- Pero **no hay ErrorBoundary** en `(auth)` que capture el error relanzado de mutaciones

## Root Cause

**El error es UNHANDLED porque:**
1. `GenericForm` captura el error para mostrar toast, luego re-lanza (`throw e`)
2. `RegisterForm.onSubmit` no tiene `.catch()` para manejar el error relanzado
3. El error escapa como `unhandledRejection`

**El mensaje "Error al crear la cuenta" viene de:**
- `useRegister.ts:46`: `throw new Error(response.error?.message ?? "Error al crear la cuenta")`
- Pero este código **no debería ejecutarse** si `registerUser` rechaza con `AxiosError` antes
- El stack trace muestra línea 46 como origen, lo que indica que `registerUser` SÍ retornó (no rechazó)

**Teoría más probable:** El backend retorna HTTP 200 con `success: false` en el body (no HTTP 4xx). Esto hace que:
1. `api.post` NO rechace (axios solo rechaza en códigos 2xx si hay error config)
2. `registerUser` retorna `{ success: false, data: null, error: {...} }`
3. `mutationFn` hace `throw new Error(response.error?.message ?? "Error al crear la cuenta")`
4. React Query captura el throw pero algo lo escapa

Necesito verificar si el backend realmente retorna 200 con `success: false` para errores 409.

## Related to Worker/Scraper?

**NO RELACIONADO.** El working tree muestra cambios extensos en frontend/auth/api pero NO hay cambios en:
- `worker/` directory
- Scraping logic
- Backend registration flow (`registro_flujo.py`, `registro_controller.py`)

El error es puramente frontend: regresión causada por los cambios en `api.ts`, `useRegister.ts`, y cómo `GenericForm` propaga errores de mutaciones.

## Risks

- Error propagate as `unhandledRejection` suggests missing error boundary in auth routes
- `GenericForm` re-throws all caught errors — this pattern breaks for mutation errors
- No `QueryClientProvider` error boundary visible in auth layout (auth layout was deleted per git status)
- Working tree has massive frontend changes — multiple potential causes

## Ready for Proposal

**Sí — necesita SDD spec y design.** El fix requiere:
1. Modificar `GenericForm` para no re-lanzar errores de mutaciones (o crear variant para mutations)
2. O envolver `RegisterForm` con error boundary apropiado
3. O modificar `RegisterForm.onSubmit` para capturar el error con `.catch()`
4. O restaurar `unwrap()` en `api.ts` y mantener el patrón anterior

**El cambio más seguro:** Modificar `RegisterForm.onSubmit` para agregar `.catch()` que no relanze, ya que el toast ya se mostró en `GenericForm`.

## Contract

**Status:** success
**Summary:** Diagnosticado error `unhandledRejection` en registro. Causa: cambios en `api.ts` (eliminación de `unwrap()`), `GenericForm` re-lanza errores con `throw e`, y `RegisterForm.onSubmit` no captura errores. NO relacionado con worker/scraper —，纯前端问题。
**Artifacts:** `sdd/register-unhandled-rejection/exploration.md`
**Next:** sdd-spec
**Risks:** Working tree con muchos cambios frontend sin relación a scraper; patrón de error en GenericForm rompe con mutaciones
**Skill Resolution:** paths-injected — cargó `sdd-explore` y `_shared/sdd-phase-common.md`
