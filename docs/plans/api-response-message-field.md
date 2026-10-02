# Plan: `api-response-message-field`

> Phase: exploration outcome → implementation plan (modular).
> Persistence: this file is the human-readable plan; the structured artifact lives in Engram at `sdd/api-response-message-field/explore`.

---

## 1. Intent

Add a human-readable `message` field to the generic API response envelope so it is populated on **both success and error responses**. The frontend consumes this field to drive `toast.success(...)` / `toast.error(...)` consistently instead of hardcoding strings per component.

Today:

```json
{ "success": true, "data": [...], "error": null }
```

After this change:

```json
{ "success": true, "data": [...], "error": null, "message": "Inscripción creada correctamente." }
```

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email ya registrado • La contraseña debe tener al menos 8 caracteres",
    "details": { "email": "Email ya registrado", "password": "..." }
  }
}
```

---

## 2. Decisions (locked — confirmed with user)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Origin of success message | **Ad-hoc per controller** — `success_response(data, message="...")` from the controller/orchestrator. No central mapping. |
| 2 | Error code (i18n) | **No** — keep only the human `message`. The existing `code` field is sufficient for now. |
| 3 | Hook auto-toast | **Yes** — `useApiCreate` / `useApiUpdate` / `useApiDelete` trigger `toast.success(response.message)` automatically when present. |
| 4 | `error.message` shape | **Single concatenated string** — NonFieldErrors first, then field errors in order, joined with `" • "`. `error.details` keeps the full structured dict. |

---

## 3. Affected Areas

### Backend
| File | Change |
|------|--------|
| `backend/core/responses.py` | Add `message: Optional[str]` to `ApiResponse` and `PaginatedApiResponse`. Extend `success_response(data, message=None)`. |
| `backend/core/exceptions.py` | Populate top-level `error.message` with concatenated human text (NonFieldErrors first, then field errors, joined with `" • "`). Replace generic strings (`"Error en la petición del API."`, `"Validation failed"`, `"Error de validación interna."`) with the real message. |
| `backend/modules/*/presentation/controllers/*.py` | Mutating actions pass `message=` to `success_response()`. Each route gets a docstring (class + per-method) describing what it does. |

### Frontend
| File | Change |
|------|--------|
| `frontend/src/types/api.types.ts` | Add `message?: string` to `ApiResponse<T>` and the `apiResponseSchema` factory. |
| `frontend/src/errors/error-handler.ts` | Confirm parser also surfaces `data.message` (currently falls through to `data.error.message`, which now carries the concatenated text). |
| `frontend/src/hooks/callsApi/useApiCreate.ts` | On success, if `response.data?.message`, call `notify.success(response.data.message)`. |
| `frontend/src/hooks/callsApi/useApiUpdate.ts` | Same auto-toast on success for both direct and classic modes. |
| `frontend/src/hooks/callsApi/useApiDelete.ts` | Same auto-toast on success. |

---

## 4. Controller Route Inventory

> Goal: complete map of every controller endpoint so the per-endpoint docstrings are added in one sweep and `message=` is plumbed into every mutating action.

### `modules/inscripciones/presentation/controllers/inscripcion_controller.py` — prefix `/inscripciones`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| POST | `/` | `crear_inscripcion` | yes | yes |
| GET | `/` | `list_inscripciones` | no (read) | yes |
| GET | `/{inscripcion_id}` | `detalle_inscripcion` | no (read) | yes |
| PATCH | `/{inscripcion_id}/estado` | `cambiar_estado` | yes | yes |
| POST | `/{inscripcion_id}/delegado` | `asignar_delegado` | **migrate** (currently embeds `data.mensaje`) | yes |
| POST | `/{inscripcion_id}/participantes` | `agregar_participante` | **migrate** (currently embeds `data.mensaje`) | yes |
| PATCH | `/{inscripcion_id}/equipos/{equipo_id}/participantes` | `agregar_participantes_equipo` | **migrate** (currently embeds `data.mensaje`) | yes |
| PATCH | `/{inscripcion_id}/participantes/{participante_id}` | `editar_participante` | yes | yes |
| DELETE | `/{inscripcion_id}/participantes/{participante_id}` | `remover_participante` | **migrate** (currently embeds `data.mensaje`) | yes |
| PATCH | `/{inscripcion_id}/participantes/{participante_id}/mover` | `mover_participante` | yes | yes |

> **"migrate"** = currently returns `success_response({"mensaje": "..."})` — change to `success_response(payload, message="...")` and drop the `mensaje` field from the payload.

### `modules/inscripciones/presentation/controllers/evento_controller.py` — prefix `/eventos`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| GET | `/` | `list_eventos` | no (read) | yes |

### `modules/inscripciones/presentation/controllers/disciplina_controller.py` — prefix `/disciplinas`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| GET | `/` | `list_disciplinas` | no (read) | yes |
| GET | `/{disciplina_id}/categorias` | `list_categorias` | no (read) | yes |

### `modules/inscripciones/presentation/controllers/promocion_controller.py` — prefix `/promociones`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| GET | `/` | `list_promociones` | no (read) | yes |

### `modules/inscripciones/presentation/controllers/paquete_controller.py` — prefix `/paquetes`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| GET | `/` | `list_paquetes` | no (read) | yes |
| GET | `/{paquete_id}/disciplinas` | `list_paquete_disciplinas` | no (read) | yes |

### `modules/usuarios/presentation/controllers/registro_controller.py` — prefix `/usuarios`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| POST | `/register` | `registro` | yes | yes |

### `modules/usuarios/presentation/controllers/persona_busqueda_controller.py` — prefix `/personas`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| GET | `/busqueda/{documento}` | `buscar_persona` | no (read) | yes |

### `modules/usuarios/presentation/controllers/me_controller.py` — prefix `/auth`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| GET | `/me` | `me` | no (read) | yes |

### `modules/usuarios/presentation/controllers/ingeniero_habilitado_controller.py` — prefix `/ingenieros`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| GET | `/habilitados/{cip}` | `buscar_ingeniero` | no (read) | yes |

### `modules/usuarios/presentation/controllers/auth_controller.py` — prefix `/auth`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| POST | `/username` | `login_username` | yes ("Inicio de sesión exitoso") | yes |
| POST | `/dni` | `login_dni` | yes | yes |
| POST | `/email` | `login_email` | yes | yes |

### `modules/pagos/presentation/controllers/pagos_controller.py` — prefix `/pagos`

| Method | Route | Action | Add `message=` | Add docstring |
|--------|-------|--------|----------------|---------------|
| GET | `/izipay/preparar/{inscripcion_id}` | `preparar_pago` | yes ("Pago preparado") | yes (already has rich docstring) |
| POST | `/izipay/confirmar` | `confirmar_pago` | yes ("Pago confirmado") | yes |

### Per-Endpoint Docstring Standard

Each route method gets a Python docstring describing:
- HTTP method and full route path (e.g., `Route: POST /api/inscripciones/`)
- Auth requirement (public / JWT / role)
- What the endpoint does, in 1–3 sentences
- Notable side effects (e.g., "creates Persona + Usuario in a single transaction")
- Errors it raises (linking to `core/exceptions.py` codes)

Class docstrings should describe the controller's responsibility and list the routes it owns (a one-liner each, or a small table).

---

## 5. Modular Apply Units

Each unit is independently committable. Run them in this order; each unit verifies itself.

### Unit 1 — Backend envelope + exception handlers
**Files:** `backend/core/responses.py`, `backend/core/exceptions.py`

- Add `message: Optional[str]` to `ApiResponse` and `PaginatedApiResponse`.
- Extend `success_response(data: Any = None, message: str | None = None) -> dict`.
- Rewrite exception handlers so `error.message` is the real text. The new helper lives next to `format_errors` in `backend/core/utils.py`:

```python
def humanize_validation_errors(details: dict | list | None) -> str:
    """Join NonFieldErrors first, then field errors, with ' • '."""
```

- `on_pydantic_validation_error`, `on_ninja_validation_error`, `on_django_validation_error` build the joined string and pass it as the `message` arg.
- `on_http_error` passes `exc.message` (string form) when present.
- `on_value_error`, `on_integrity_error`, `on_object_not_found`, `on_permission_denied` keep their specific messages.

**Verify:** run `python manage.py check` + targeted unit test in `backend/tests/core/test_responses.py` (create if missing).

### Unit 2 — Frontend envelope types + hooks
**Files:** `frontend/src/types/api.types.ts`, `frontend/src/hooks/callsApi/useApiCreate.ts`, `useApiUpdate.ts`, `useApiDelete.ts`, `frontend/src/errors/error-handler.ts`

- Add `message?: string` to `ApiResponse<T>` and to `apiResponseSchema`.
- In each generic hook, after a successful mutation, if `response.data?.message`, call `notify.success(response.data.message)`.
- Confirm `error-handler.ts` parser still works (it reads `data.error.details` first, falling back to `data.error.message` — no change required, but verify).

**Verify:** `pnpm tsc --noEmit` + manual smoke test of a mutation.

### Unit 3 — Inscripciones module
**Files:** `backend/modules/inscripciones/presentation/controllers/inscripcion_controller.py`

- Apply all 10 routes from the inventory above.
- Migrate the four `data.mensaje` workarounds to `success_response(payload, message="...")`.
- Add docstrings (class + per-method) using the standard.

**Verify:** manual hit to one POST + one PATCH + one DELETE; confirm frontend toast fires.

### Unit 4 — Auth + Registro + Me controllers
**Files:** `backend/modules/usuarios/presentation/controllers/auth_controller.py`, `registro_controller.py`, `me_controller.py`

- Add `message="..."` to login flows; docstrings per method.

**Verify:** login flow shows success toast on each variant.

### Unit 5 — Read-only controllers (catalogs + personas + ingenieros + pagos)
**Files:** `evento_controller.py`, `disciplina_controller.py`, `promocion_controller.py`, `paquete_controller.py`, `persona_busqueda_controller.py`, `ingeniero_habilitado_controller.py`, `pagos_controller.py`

- No `message=` on GET routes (no toast).
- For `pagos_controller`: add `message=` to `confirmar_pago` only.
- Add docstrings to every method.

**Verify:** `python manage.py check` + manual GET smoke.

### Unit 6 (optional) — Roll out message everywhere
If we decide later that GET endpoints should also emit messages (e.g., "Catálogo cargado"), the inventory above is the source of truth.

---

## 6. Success Criteria

- [ ] `ApiResponse.message` is present on every successful response from mutating endpoints.
- [ ] `error.message` contains the real concatenated human text on validation errors.
- [ ] `useApiCreate/Update/Delete` auto-trigger `toast.success` when `response.message` exists.
- [ ] No component still uses `toast.success("Inscripción creada")` hardcoded — replaced by reading the envelope.
- [ ] Every controller route has a docstring matching the standard.
- [ ] Frontend TypeScript compiles; backend `manage.py check` passes.
- [ ] Existing tests pass (no regressions).

---

## 7. Rollback Plan

- Remove `message: Optional[str]` from `ApiResponse` / `PaginatedApiResponse` and from frontend `ApiResponse<T>`. Frontend treats missing `message` as undefined → no toast (silent). Low-risk revert.
- Revert the four `data.mensaje` workarounds in `inscripcion_controller.py` to their previous shape if any caller depended on `data.mensaje`.

---

## 8. Risks

- **External consumers:** if any other client (mobile, scripts) consumes the envelope, they will see a new `message` field. Adding an optional field is non-breaking for any reasonable parser, but flag in release notes.
- **Hardcoded toasts left behind:** some components still call `toast.success("Inscripción creada")` directly. The apply must grep and clean those up.
- **Validation helper ordering:** NonFieldErrors must come first in the concatenated string; otherwise field-level errors dominate and obscure cross-field constraints.
