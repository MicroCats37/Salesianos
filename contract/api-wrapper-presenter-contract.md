# API Wrapper & Presenter Contract

> **Version:** 1.1
> **Date:** 2026-10-17
> **Scope:** General contextual wrapper and presenter architecture — applies to all modules (notifications, solicitudes, reclamaciones, liquidaciones, etc.)
> **Reference:** Motivation from notification module; principles are module-agnostic.

---

## Decision

Establish general rules for contextual API wrappers and presenters so each module can define typed, module-specific response shapes without leaking unrelated fields across module boundaries.

---

## 1. Endpoint Ownership

### Contextual endpoints live in their business module

| Endpoint type | Where it lives | Why |
|---------------|---------------|-----|
| Module-specific (e.g., `/notificaciones/`, `/solicitudes/`, `/reclamaciones/`) | `modules/<module>/presentation/controllers/` | Business logic stays with the module |
| Generic/shared (e.g., `/ubigeo/`, `/tarifas/vigentes`, `/usuarios/me`) | `modules/<core_or_shared>/` | Reusable across multiple callers |

**Rule:** A module's controller must NOT import presenters or schemas from a different business module. Cross-module data access goes through selectors, not direct presenter coupling.

---

## 2. Wrapper Shape

### Contextual endpoints return typed business wrappers — not flat mixed fields

```python
# ✅ CORRECT — typed contextual wrapper per module
class NotificacionDetalleOut(Schema):
    id: UUID
    titulo: str
    mensaje: str
    tipo: NotificacionTipo
    usuario_id: UUID
    leida: bool
    fecha_envio: datetime

# ❌ WRONG — flat mixed fields from unrelated domains
class NotificacionOut(Schema):
    id: UUID
    titulo: str
    leida: bool
    expediente_numero: str        # from Tramite — unrelated
    municipalidad_nombre: str     # from another module
    anything_else: z.any()
```

### Global list endpoints return minimal/common fields only

List endpoints that aggregate across modules return only the fields common to all items:

```python
# ✅ CORRECT — minimal fields for a global notification list
class NotificacionListOut(Schema):
    id: UUID
    titulo: str
    leida: bool
    fecha_envio: datetime

# ✅ Module-specific list endpoints may return richer wrappers
# GET /notificaciones/mis-notificaciones → NotificacionDetalleOut with all fields
```

---

## 3. Presenter Responsibilities

### Selector: loads relations. Presenter: transforms only.

```
Selector (domain/infrastructure)     → loads data from DB
                                       ↓
Presenter (presentation)            → transforms domain result → HTTP schema
                                       ↓
Controller                         → returns Presenter output
```

| Layer | Must | Must NOT |
|-------|------|----------|
| Selector | Query DB, return domain result DTO | Transform to HTTP schema, know about HTTP layer |
| Presenter | Receive domain result, return typed HTTP schema | Query DB, call selectors |

**Rule:** A presenter that calls a selector has crossed the layer boundary. Extract data loading to the orchestrator; keep the presenter as a pure transformer.

---

## 4. Registry / Discriminator Pattern

### Wrapper type may be selected by a discriminator field — presenter stays typed

When a single endpoint must return different wrapper types (e.g., `NotificacionEmailOut`, `NotificacionSMSOut`), use a discriminator:

```python
class NotificacionOut(Schema):
    id: UUID
    tipo: NotificacionTipo          # discriminator
    # Common fields only here

class NotificacionEmailOut(Schema):
    id: UUID
    tipo: Literal["email"]
    email_destino: str
    asunto: str
    cuerpo_html: str

class NotificacionSMSOut(Schema):
    id: UUID
    tipo: Literal["sms"]
    telefono_destino: str
    mensaje: str
```

**Rule:** The registry/discriminator selects the wrapper type. The presenter still returns a typed, module-specific schema. No `z.any()` anywhere.

---

## 5. Explicit Module Wrapper Fields Over Generic Envelope

### Avoid generic `contexto` or `data` envelope if it conflicts with project style

This project uses **explicit named wrappers** per module:

```python
# ✅ CORRECT — explicit module fields, no generic envelope
class LiquidacionDetalleOut(Schema):
    liquidacion_general: LiquidacionGeneralOut
    liquidacion_tipo: LiquidacionTipoOut
    liquidacion_especifica: LiquidacionEspecificaOut

# ❌ WRONG — generic `contexto` envelope mixing unrelated domains
class SomethingOut(Schema):
    contexto: dict[str, Any]
    data: Any
```

---

## 6. Field Isolation Between Modules

### Do not leak unrelated module fields into global presenters

| Presenter | May include | Must NOT include |
|-----------|-------------|-----------------|
| `NotificacionPresenter` | notification fields + usuario_id | expediente, municipalidad, any Tramite fields |
| `SolicitudPresenter` | solicitud fields + related persona | unrelated module fields |
| Global `SaludOAuthPresenter` | common health/metadata fields | module-specific business data |

**Rule:** If an endpoint needs data from two modules, the orchestrator loads both via selectors and the presenter maps both — but the presenter stays module-specific for each mapped output. The HTTP response may contain multiple wrappers; each wrapper is typed to its own module.

---

## 7. Frontend Schema Mirror

### Backend wrappers map 1:1 to frontend typed schemas — no `z.any()`

```typescript
// Backend: LiquidacionDetalleOut
// Frontend: z.object({ ... }) matching exactly

const LiquidacionDetalleOutSchema = z.object({
  liquidacion_general: LiquidacionGeneralSchema,
  liquidacion_tipo: LiquidacionTipoSchema,
  liquidacion_especifica: LiquidacionEspecificaSchema,
});

// ❌ WRONG — frontend using z.any() defeats the type contract
const UnknownOutSchema = z.object({
  data: z.any(),
});
```

**Rule:** Backend schemas and frontend schemas are generated from the same contract. If the backend adds a field, the frontend must update the schema too.

---

## 8. Public Message Contract

### Public messages are part of the HTTP boundary

Controllers may declare a short, fixed success message that describes the completed action. They must not build error messages, interpolate user input, or expose internal identifiers.

```python
# Correct: fixed, user-facing success message at the HTTP boundary.
return success_response(
    InscripcionPresenter.present(result),
    message="La inscripción se registró correctamente.",
)
```

Presenters only transform result objects into typed response schemas. They do not select success messages or translate errors.

### Error ownership

Domain services and flows raise typed domain exceptions with a stable machine-readable `code`. `core/exceptions.py` owns the public error catalog and maps that code to a safe Spanish message and HTTP status.

```python
# Domain/flow: no public prose and no interpolated identifiers.
class InscripcionNotFoundError(NotFoundError):
    code = "INSCRIPCION_NOT_FOUND"

    def __init__(self):
        super().__init__(resource="Inscripción", code=self.code)


raise InscripcionNotFoundError()

# core/exceptions.py: the only HTTP error translation point.
PUBLIC_ERROR_MESSAGES = {
    "INSCRIPCION_NOT_FOUND": "No se encontró la inscripción solicitada.",
}
```

The public message must never contain UUIDs, database primary keys, request identifiers, SQL constraints, stack traces, filesystem paths, provider payloads, credentials, or raw exception text. Technical context belongs only in structured server logs.

Unknown codes and unexpected exceptions return a generic message such as `"Ocurrió un error inesperado. Inténtalo nuevamente."` while the handler records the technical cause internally.

### Error response categories

| Category | HTTP status | Example code | Public message rule |
|----------|-------------|--------------|---------------------|
| Validation | 422 | `INVALID_REQUEST` | State what the user must correct without echoing sensitive values. |
| Authentication | 401 | `AUTHENTICATION_REQUIRED` | Explain that authentication is required. |
| Authorization | 403 | `ACTION_NOT_ALLOWED` | Explain that the action is not permitted. |
| Not found | 404 | `INSCRIPCION_NOT_FOUND` | Name the resource, never its internal identifier. |
| Business conflict | 409 | `CUPO_NOT_AVAILABLE` | Explain the business condition and next safe action. |
| Payment | 409 or 422 | `PAYMENT_NOT_CONFIRMED` | Explain the payment state without provider internals. |
| Concurrency | 409 | `RESOURCE_CHANGED` | Ask the user to refresh and retry. |
| Unexpected | 500 | `INTERNAL_ERROR` | Use a generic message only. |

### Logging and support correlation

Exception handlers log the stable error code, technical details, and a server-side correlation identifier. The correlation identifier is not returned in the public response unless a separate, approved support-facing contract defines a safe reference format.

---

## 9. Checklist for Future Endpoints / Presenters

Before merging a new endpoint or presenter, verify:

- [ ] Contextual endpoint lives in its own module, not in a shared/core module
- [ ] Response uses typed module-specific wrappers, not flat mixed fields
- [ ] Global list endpoints return only minimal/common fields
- [ ] Module-specific list/detail endpoints may return rich wrappers
- [ ] Selector loads relations; presenter transforms only — presenter does NOT query DB
- [ ] Registry/discriminator pattern uses typed discriminators, not `z.any()`
- [ ] No generic `contexto` or `data` envelope — explicit named module fields
- [ ] No leakage of unrelated module fields into another module's presenter
- [ ] Frontend schema mirrors the backend wrapper with exact field match (no `z.any()`)
- [ ] Presenter is module-specific; cross-module data flows through orchestrator selectors
- [ ] Controller success messages are fixed, contextual, and user-facing
- [ ] Error messages come only from the global exception-handler catalog
- [ ] No public response exposes UUIDs, internal IDs, raw exception text, SQL details, traces, paths, or secrets

---

## 10. Reference: Notification Use Case (Motivation)

The notification module (`modules/notificaciones/`) motivated these rules:

- `NotificacionDetalleOut` returns notification-specific fields only
- `NotificacionListOut` returns minimal fields for list views
- Email vs SMS variants use a `tipo` discriminator — each variant is a typed schema
- The presenter does not query DB; it only transforms the domain result passed from the orchestrator

These same principles apply to future modules: `solicitudes`, `reclamaciones`, `tramites`, etc.

---

## 11. Relationship to Existing Contracts

| Contract | What it covers | Relationship |
|----------|---------------|-------------|
| `django-app-architecture-contract.md` | Full Django module structure, services, selectors, presenters | This contract extends presenter rules specifically |
| `next-app-architecture-contract.md` | Frontend folder structure, schema naming, TanStack Query | Frontend schemas must mirror backend wrappers |
| `TEST_ARCHITECTURE_CONTRACT.md` | Test structure, factories, fixtures | Tests verify wrapper contracts |
| `docs-dev/dep_ref/Wrappers_Semantica_*.md` | Liquidacion-specific wrapper semantics | Superseded by this contract for general rules |
