# Exploration: admin-user-management

**Status:** exploration complete — ready for proposal (1 blocking product question)
**Project:** salesianos · **Artifact store:** engram · **Topic key:** `sdd/admin-user-management/explore`
**Mode:** read-only exploration (no code modified). All 7 `contract/` files read before code.
**Memory validation:** observation #6646 (3 roles `responsable`/`admin_comite`/`admin_finanzas`, `proxy.ts`, Next server actions) describes a **pre-refactor system that no longer exists**. The current system is Django + Ninja-Extra backend / Next 16 + axios frontend with Django auth flags. That memory is stale and must NOT drive the design.

---

## Exploration: admin-user-management

### Current State

#### 1. Identity & role model (verified in code)

- `backend/modules/usuarios/domain/models/usuario.py` — `Usuario(AbstractBaseUser, PermissionsMixin, DjangoAuthMixin, BaseModel)`. Own fields: `persona_fk` (OneToOne, `PROTECT`, **non-nullable**), `email`, `username`, `dni` (legacy). Inherited: `is_staff` + `is_active` (from `core/models/__init__.py::DjangoAuthMixin`), `is_superuser`, `groups`, `user_permissions` (from `PermissionsMixin`), `password`, `last_login`. **There is NO `rol` field and NO role enum.**
- `backend/modules/usuarios/domain/models/persona.py` — `Persona` holds civil identity (`nombres`, `apellidos`, `tipo_documento`, `numero_documento`, `genero`, `telefono`, `whatsapp`, `contacto_emergencia_*`, `aseguradora_*`), `UniqueConstraint(tipo_documento, numero_documento)`.
- **Role is derived at runtime, in two inconsistent vocabularies:**
  - `presentation/controllers/me_controller.py:57-61` → `rol = "admin" if is_superuser else ("staff" if is_staff else "user")` → **3 values**.
  - `presentation/presenters/auth_presenter.py` / `registro_presenter.py` → raw `is_staff` / `is_superuser` booleans, **no `rol`**.
  - Frontend `features/auth/schemas/index.ts::MeResponse` has `rol?: string`; `features/auth/store/auth.store.ts::RegisterUser` has `is_staff`/`is_superuser`. Login responses never populate `rol`.
- **Django RBAC machinery exists but is EMPTY:** `django.contrib.auth` is installed (`auth_group`, `auth_permission` tables exist), but `core/permissions.py::SystemPermissions.all()` returns `[]`, `core/models/permissions.py::SystemPermissions` is an unmanaged proxy anchor with `permissions = []`, **no groups are seeded**, and `core/security.py::verify_user_permissions` / `CheckPermission` / `core/decorators.py` are used by **zero controllers**. `PermissionsMixin` gives the tables; nobody populates or reads them.
- **Django auth flags are already the de-facto admin concept:** `modules/salesianos_fest/presentation/ownership.py::check_ownership_or_admin` treats `is_staff OR is_superuser` as "admin" (the only centralized authorization helper in the codebase). `modules/usuarios` has **no** equivalent.
- **JWT carries no role claim.** `domain/services/core/auth_core_service.py::_create_jwt_tokens` uses `RefreshToken.for_user(usuario)` → claims are only `user_id` + `token_type`. **Consequence: server-side role changes take effect on the next request — no stale role inside the token.** The staleness risk lives entirely in the frontend (see §3).
- **Token revocation does not exist.** `ninja_jwt.token_blacklist` is installed but unused. `NINJA_JWT.ACCESS_TOKEN_LIFETIME` = 1h (prod) / **30 days (dev)**, refresh 7d / 90d. Deactivating a user therefore does **not** revoke live tokens, and the refresh token keeps working.
- **Login blocks inactive users** (`domain/services/flujos/auth_flujo.py:44-45, 84-85, 124-125` → 403 "Usuario inactivo"), but only for *new* logins.
- **Registration cannot escalate:** `registro_flujo.py:142-148` creates `Usuario(username=..., email=..., persona_fk=...)` with `is_staff`/`is_superuser` defaulting to False. `POST /auth/register` is `AllowAny` and safe.
- **Seeds / admin creation:** `core/management/commands/create_admin.py` and `modules/usuarios/management/commands/seed_admin.py` both upsert a fixed superuser (`admin` / `admin`, DNI `00000000`) with `is_staff=True, is_superuser=True`. Hardcoded weak password in both. `Django admin` (`modules/usuarios/admin/usuario_admin.py`, Persona + PerfilIngeniero admins) is already live and nginx proxies `/admin/` → Django.

#### 2. Endpoint authorization matrix (all controllers read; verified in source)

| Endpoint | Declared auth | Real enforcement | Verdict |
|---|---|---|---|
| `POST /auth/login/{username,dni,email}` | AllowAny | public by design | OK |
| `POST /auth/register` | AllowAny | public by design; no role fields | OK |
| `GET /auth/me` | JWT | returns own session | OK |
| `GET /personas/busqueda/{documento}` | AllowAny | public document lookup | ⚠️ PII enumeration surface |
| `GET /ingenieros/habilitados/{cip}` | AllowAny | public | — |
| `GET /catalogo/**` (5 reads) | AllowAny | public catalog | OK |
| `POST /cotizaciones` | AllowAny | public quote | OK (business decision) |
| `POST /pagos/notificacion` | AllowAny | Izipay webhook | ⚠️ no signature verification visible at controller |
| **`GET /inscripciones/{id}`** | `auth=None` | none | 🚨 **public PII read** (roster + participant data) |
| **`GET /inscripciones/{id}/detalle`** | `auth=None` | none | 🚨 **public PII read** (full roster) |
| **`PATCH /inscripciones/{id}`** | `auth=None` | none ("delegado a middleware" — no such middleware exists) | 🚨 **unauthenticated mutation** of `estado` / `observacion` / `delegado_id` |
| **`POST /equipos/`** | `auth=None` | none | 🚨 **unauthenticated creation** of a team inside any `inscripcion_id` |
| `GET /equipos/{id}`, `GET /equipos/inscripcion/{id}` | `auth=None` | none | 🚨 public read |
| `GET /participaciones/{id}`, `GET /participaciones/equipo/{id}` | `auth=None` | none | 🚨 public read |
| `POST /inscripciones/`, `/completa/`, `GET /inscripciones/` | JWT | owner derived server-side from `request.user.persona_fk_id` | OK |
| `POST /inscripciones/{id}/personas`, `.../retirar`, `GET .../pool`, `GET .../elegibles`, `POST .../pool/asignar` | JWT | `check_ownership_or_admin` | OK |
| `PATCH /participaciones/{id}`, `/retirar`, `/mover` | JWT | `_check_participacion_ownership` | OK |
| `POST /asignaciones/`, `POST /asignaciones/liberar` | JWT | `check_ownership_or_admin` (added in a prior fix) | OK |
| `POST /compras/*`, `POST /compras/{id}/...`, `GET /compras/{id}` | JWT | `_validate_compra_ownership` / `_is_admin` | OK |
| `GET /pagos/transaccion`, `/pagos/orden` | JWT | `_actor` (owner or admin) | OK |
| **`PATCH /acreditaciones/{evento_id}/{persona_id}/override-fiesta`** | JWT | **none** | 🚨 any authenticated user can authorize/block anyone's fiesta access |
| **`POST /acreditaciones/{evento_id}/{persona_id}/generar-qr`** | JWT | **none** | 🚨 any authenticated user can regenerate anyone's QR |
| `GET /acreditaciones/{evento_id}/{persona_id}` | JWT | none | ⚠️ cross-user read |
| `GET /asignaciones/{id}`, `GET /asignaciones/inscripciones/{id}/asignaciones` | JWT | none | ⚠️ cross-user read (writes are guarded) |
| `POST /acceso/registrar` | JWT | none | ⚠️ operator-role-agnostic QR scan |

**Summary:** the admin area will be the first *role-gated* surface in the system. There is currently **no endpoint in the whole API that requires an administrator role** — admin-ness is only ever checked as an *alternative* inside ownership checks.

#### 3. Frontend auth, session, routing (verified)

- Stack: Next 16 App Router, React 19, TanStack Query v5, Zustand v5, RHF 7 + Zod 4, axios, `@tanstack/react-table` v8 **already installed**.
- `lib/api.ts` — axios instance; injects `Authorization: Bearer` from cookie; proactive refresh when access token expires in <5 min; response interceptor refreshes once on 401 and retries.
- `lib/auth/cookies.ts` — **all four cookies are `httpOnly: false`** (`ACCESS_TOKEN`, `REFRESH_TOKEN`, `EXPIRES_AT`, `USER_SESSION`), with an explicit comment saying so; `useLogin` also writes them from the browser. `USER_SESSION` holds the JSON user **including `rol`**.
- `lib/auth/actions.ts::getUserSession()` — server-side helper that simply `JSON.parse`s the `USER_SESSION` cookie. **It never revalidates the JWT against the backend.** Therefore the client-side role is (a) tamperable and (b) **stale** after a role change until re-login (cookie maxAge 7 days; zustand `persist` in localStorage `"salesianos-auth-user"`).
- Route guard today: `app/(app)/layout.tsx` — redirects to `/` when there is no session cookie. **There is no `middleware.ts`, no `proxy.ts`, and no role check anywhere in the frontend.**
- `components/AppSidebar.tsx` — nav: Mis Inscripciones / Crear Inscripción / Historial / Evento. No admin entry. `components-app/sidebar/ProtectedSidebar.tsx` is a **CAM-derived leftover** (mentions "CAM Liquidaciones", links to `/liquidaciones/*`) imported only by `_legacy-app-routes`, and it imports a **non-existent** `@/features/auth/schemas/auth.types` → it does not compile as-is.
- **No `/administracion` route and no admin page exist.** Nginx: `/admin/` → Django admin, `/backend/` → Django `/api/`, everything else → Next. `/administracion` is free (no collision with Django admin).
- Reusable building blocks already available: `components-app/tables/AppDataTable.tsx` (TanStack Table + skeleton loading + error/retry + empty state + pagination + row actions; **currently used by no live route**), `components/ui/table.tsx`, `components/genericPagination/Pagination.tsx` (page numbers, page-size select), `components/genericForm/*` + `components-app/forms/AppFormModal.tsx` (**already used** by `features/inscripciones`), `components/genericModal/*`, `components/confirmationDialog/*`, `components/emptyState/*`, `components-app/pages/{PageHeader,RichEmptyState,StatsArea,MemberCardSkeleton}`, `hooks/callsApi/useApiQuery|useApiCreate|useApiUpdate|useApiDelete`, `hooks/system/usePagination` (1-based `page`/`page_size`), `hooks/system/useDebounce`, `errors/error-handler.ts` + toast adapter, `components/ui/*` (sheet, dropdown-menu, badge, skeleton, tabs).
- **Response-contract mismatch to settle:** frontend `types/api.types.ts::PaginatedResponse<T>` = `{data, count, page, pageSize, totalPages}`; backend `core/responses.py::PaginatedApiResponse` = `{success,data,error,message,meta{page,page_size,total,total_pages}}`; backend `core/pagination.py::PaginatedData` = `{items,total,page,page_size,total_pages}`. No endpoint is paginated today (`GET /inscripciones/` returns a bare list) — the admin list will be the first, so the contract must be picked and mirrored in Zod.
- **Frontend↔backend login type mismatch:** `useLogin` types the response as `user: MeResponse` (`{id,email,nombres,apellidos,rol?,persona_id?}`) but the backend returns `AuthUserOut` (`{id,username,email,is_staff,is_superuser,persona_id,dni_legacy}`) → `rol` is never populated by login, and `nombres`/`apellidos` never arrive.
- **No password-management endpoint exists anywhere** (grep of all controllers: zero hits for `password`). There is no "change my password", no reset, no `must_change_password` field.
- **No email-sending code exists** although email is configured (`EMAIL_BACKEND=smtp` in production, console in dev) — there is no notification module and no `send_mail` usage.

#### 4. Test infrastructure state

- `backend/pytest.ini` → `DJANGO_SETTINGS_MODULE=config.settings.test`, `asyncio_mode=auto`, `--nomigrations`.
- `modules/usuarios/tests/fixtures/usuarios_fixtures.py` provides `api_client` (`ninja.testing.TestClient(api)`), `auth_client` (`AccessToken.for_user`), `create_user` — but **`create_user` is broken against the current model**: it calls `User.objects.create_user(username=..., email=..., password=...)` with **no `persona_fk`**, which is non-nullable → IntegrityError. Any new admin tests must build `Persona` + `Usuario` (this is the exact fixture the SDD tasks must fix).
- Test layout must follow `contract/TEST_ARCHITECTURE_CONTRACT.md`: `tests/{fixtures,integration,e2e}`, pure-dict `factories.py`, no `factory_boy`, no `unittest.mock.patch`.

---

### Affected Areas

**Backend (new)**
- `backend/modules/usuarios/presentation/controllers/administracion_controller.py` — NEW: admin-only endpoints (thin, delegate to orchestrator).
- `backend/modules/usuarios/domain/services/orchestrators/administracion_orchestrator.py` — NEW: thin async facade.
- `backend/modules/usuarios/domain/services/flujos/administracion_flujo.py` — NEW: async use-cases + `transaction.atomic()` (role/status changes, user creation).
- `backend/modules/usuarios/domain/services/core/usuario_admin_core_service.py` — NEW: sync ORM ops (list with filters, get, create, update role/status, set password).
- `backend/modules/usuarios/presentation/schemas/administracion_schemas.py` — NEW: `*In` / `*Out` HTTP schemas (composed: General / Specific / Identity blocks per `contract/SCHEMA_DRY_INTENTION.md`).
- `backend/modules/usuarios/presentation/presenters/administracion_presenter.py` — NEW: result → HTTP schema, no DB access.
- `backend/core/permissions.py` (or `backend/modules/usuarios/presentation/dependencies.py`) — NEW `require_admin` permission (replaces unused `CheckPermission`/`verify_user_permissions` machinery, or reuses it).
- `backend/modules/usuarios/di.py` — register the new core/flujo/orchestrator bindings (singleton).
- `backend/config/api.py` — register `AdministracionController`.
- `backend/modules/usuarios/presentation/controllers/me_controller.py` — align the `rol` vocabulary (3 values → 2) and add `username`/`is_active` to `MeOut`.
- `backend/modules/usuarios/presentation/presenters/{auth_presenter,registro_presenter}.py` — stop exposing raw `is_staff`/`is_superuser`; expose the same `rol` vocabulary as `/auth/me`.
- `backend/modules/usuarios/tests/fixtures/usuarios_fixtures.py` — fix `create_user` (create Persona) and add `usuario_admin`, `usuario_normal`, `usuario_inactivo` fixtures.
- `backend/modules/usuarios/tests/integration/test_administracion_usuarios.py` + `tests/e2e/test_e2e_administracion.py` — NEW.
- `backend/modules/usuarios/models.py` (re-export) — only if a new field is added (e.g. `must_change_password`).

**Backend (existing — hardening, separable change)**
- `backend/modules/salesianos_fest/presentation/controllers/inscripcion_controller.py` — `PATCH /{id}` (add JWT + `check_ownership_or_admin`), `GET /{id}` and `GET /{id}/detalle` (add JWT + ownership), `POST /equipos/` (add JWT + ownership), `GET /equipos/*`, `GET /participaciones/*`.
- `backend/modules/salesianos_fest/presentation/controllers/acreditacion_controller.py` — `override-fiesta` and `generar-qr` must require admin (or owner).
- `backend/modules/salesianos_fest/presentation/controllers/asignacion_controller.py` — add ownership to the two GETs.
- `backend/modules/usuarios/presentation/controllers/persona_busqueda_controller.py` — public document lookup (PII enumeration).
- `backend/modules/pagos/presentation/controllers/pagos_controller.py` — webhook signature verification.

**Frontend (new)**
- `frontend/src/app/(app)/administracion/layout.tsx` — NEW: server-side role guard (revalidate JWT against `/auth/me`), redirect non-admins.
- `frontend/src/app/(app)/administracion/page.tsx` — NEW: users list page (thin, delegates to `features/`).
- `frontend/src/app/(app)/administracion/usuarios/[id]/page.tsx` — NEW: user detail (optional).
- `frontend/src/features/admin/usuarios/{schemas,services,hooks,components}/` — NEW feature slice (Option A namespaced, per `contract/next-app-architecture-contract.md` §10).
- `frontend/src/components/AppSidebar.tsx` — add "Administración" entry, visible only when the session `rol === "admin"` (UX only; backend is authoritative).
- `frontend/src/features/auth/schemas/index.ts` — align `MeResponse` with the backend (`rol` values, `username`, `is_active`).
- `frontend/src/features/auth/store/auth.store.ts` — role revalidation on 403 from admin endpoints; re-hydrate from `/auth/me`.
- `frontend/src/types/api.types.ts` — align `PaginatedResponse` with the chosen backend pagination wrapper.

---

### Approaches

**A. Django flags as the single source of truth (recommended)** — admin = `is_staff OR is_superuser`, matching the existing `check_ownership_or_admin` semantics; expose a 2-value `rol` (`admin` | `user`) computed server-side in one shared helper; no new model, no migration, no RBAC tables.
- Pros: zero migration risk; consistent with the only existing authorization helper; Django admin site access and API admin rights stay in sync; JWT stays role-free (no stale claims); smallest surface for a 2-role product.
- Cons: `is_staff` also grants Django-admin login, so "staff" and "app administrator" are the same concept — acceptable only if that is intended; `is_superuser` remains a hidden third tier (superuser bypasses everything, including Django admin).
- Effort: **Low–Medium**.

**B. Explicit `rol` enum field on `Usuario` (`ADMIN` | `USER`) + `is_active`** — a real domain field, admin UI edits the enum.
- Pros: explicit, self-documenting, independent of Django semantics, easy to extend to 3+ roles later; frontend contract is unambiguous.
- Cons: **two sources of truth** with `is_staff`/`is_superuser` (must keep them in sync or pick one as derived); requires a migration + backfill + `is_staff`/`is_superuser` reconciliation rules; the existing `check_ownership_or_admin` would have to be migrated to read `rol`, touching `salesianos_fest`; risk of a partial migration where an admin is `rol=ADMIN` but `is_staff=False` and loses access to the Django admin.
- Effort: **Medium**.

**C. Django groups + permissions (full RBAC)** — seed `auth_group` rows and business codenames, wire the already-present `CheckPermission` / `verify_user_permissions` machinery.
- Pros: future-proof for many roles; the machinery already exists in `core/security.py`; granular per-action control (view users / create users / change roles / reset passwords).
- Cons: **overbuilt for USER/ADMIN**; requires a permission-catalogue design, a seeding command, group↔role mapping, UI for group assignment, and migration of existing `is_staff` checks; the `core.`-anchored `SystemPermissions` design (empty today) is unproven in this project.
- Effort: **High**.

**D. Backend module placement: `modules/usuarios` vs new `modules/administracion`** — the wrapper/presenter contract (§1) says contextual endpoints live in their business module; user administration *is* the `usuarios` domain. A separate module pays the ceremony cost (apps.py, di.py, models.py re-exports, tests tree) for one controller.
- Pros of staying in `usuarios`: reuses `Usuario`/`Persona` services, no cross-module presenter coupling, cheapest path to a working admin area; extraction later is cheap if the controller stays isolated.
- Cons: `usuarios` grows a second, differently-permissioned surface; if the admin area later covers roles/permissions/audit/settings, the module will need splitting anyway.
- Effort of a dedicated module: **Medium** (mostly ceremony).

---

### Recommendation

**Adopt Approach A + D: Django flags as the single source of truth, admin controller inside `modules/usuarios`, no RBAC tables, no new role field.** Rationale: the product has two roles; the codebase already treats `is_staff OR is_superuser` as "admin" in the single centralized helper; Django's RBAC tables are present but unpopulated and unused, so activating them now would be speculative ceremony. If a third role is ever needed, `rol` can be introduced then with a migration, and the admin UI would not change shape.

**Concrete backend design**

1. One shared helper `core/permissions.py::es_admin(user) -> bool` (`is_staff or is_superuser`) + a Ninja-Extra permission `RequireAdmin` (or reuse the existing `CheckPermission`/`verify_user_permissions` machinery, which is currently dead code) → every admin endpoint returns **403 `ACTION_NOT_ALLOWED`** for non-admins, **401** for anonymous.
2. **Normalize the role vocabulary to exactly two values (`admin` | `user`)** and compute it in ONE place (a shared presenter/helper), used by `/auth/me`, the login response, and the register response. Remove the intermediate `"staff"` value and stop leaking raw `is_staff`/`is_superuser` booleans in public payloads (they are an implementation detail, and `is_superuser` in a response is needless privilege disclosure).
3. **Recommended endpoints** (base path `/administracion`, all JWT + admin):

| Method & path | Purpose | Notes |
|---|---|---|
| `GET /administracion/usuarios` | list + filters | `q` (username / email / document / name), `rol` (`admin`\|`user`), `estado` (`activo`\|`inactivo`), `page`, `page_size`, `ordering` (whitelist: `username`, `email`, `created_at`, `last_login`) |
| `GET /administracion/usuarios/{id}` | detail | no password/hash/token fields ever |
| `POST /administracion/usuarios` | create | creates `Persona` + `Usuario` atomically, optional `rol`, optional `is_active`; returns the created user **without** the password |
| `PATCH /administracion/usuarios/{id}` | update profile | email, phone, etc. — **not** role, **not** status (separate endpoints below) |
| `PATCH /administracion/usuarios/{id}/rol` | change role | `admin`\|`user`; guard: cannot demote the **last active admin** → 409 |
| `PATCH /administracion/usuarios/{id}/estado` | activate / deactivate | guard: cannot deactivate self; cannot deactivate the last active admin → 409; **must revoke outstanding tokens** (token blacklist or a `token_version` column) so deactivation takes effect immediately instead of after 1h (prod) / 30d (dev) |
| `POST /administracion/usuarios/{id}/password-reset` | reset password | see the blocking question below; response must **never** contain a hash, token or secret |
| `GET /administracion/usuarios/{id}/historial` | read-only audit | **`Usuario.history` already exists** (`HistoricalRecords`) → free audit trail for role/status/profile changes; no new audit table needed for MVP |

4. **Pagination/filter contract** — use `core/pagination.py::PaginatedData` inside `ApiResponse` → `data = {items, total, page, page_size, total_pages}`; `page` is 1-based (matches `hooks/system/usePagination`); `page_size` default 10, max 100; `ordering` is whitelisted server-side (never interpolated raw into `order_by`). **Mirror it 1:1 in Zod** and fix the stale `PaginatedResponse` in `frontend/src/types/api.types.ts`.
5. **Audit/security requirements (non-negotiable)**
   - Never return `password`, `password` hash, JWT, refresh token, or `last_login` token material in any admin response or log.
   - Server-side checks are authoritative; the frontend `rol` (cookie + localStorage, both client-writable) is **advisory UX only**.
   - Guard "last active admin": count `Usuario.objects.filter(is_staff=True, is_active=True)` before any demotion/deactivation → 409 `LAST_ADMIN_PROTECTED`.
   - Guard self-demotion / self-deactivation (at minimum when you are the last active admin; recommended: block self-demotion/self-deactivation outright).
   - **Role claims cannot go stale server-side** (JWT carries no role) — but the *client* cache can, so after any role/status change affecting the current user, force `GET /auth/me` and rewrite the session cookie; on a 403 from an admin endpoint, invalidate the session and redirect.
   - Deactivation must invalidate existing access/refresh tokens (today it does not).
   - Audit: leverage `simple_history` (`Usuario.history`) rather than inventing an audit table; expose it read-only.
   - Errors: use the existing `core/exceptions.py` catalog pattern — domain exceptions with stable codes, public messages in Spanish without IDs/UUIDs/secrets.
6. **Test matrix** (per `contract/TEST_ARCHITECTURE_CONTRACT.md`): `tests/integration/test_administracion_usuarios.py` + `tests/e2e/test_e2e_administracion.py`, with fixed fixtures `usuario_admin`, `usuario_normal`, `usuario_inactivo`, `create_user` (**fixed** to create a `Persona`). Cases: list filters/pagination/sorting/empty page; detail 404; create (success, duplicate email/document → 409, invalid payload → 422); role change (promote, demote, demote last admin → 409, self-demote → 403/409); status change (deactivate, deactivate self → 403, deactivate last admin → 409, token invalidation after deactivation); password reset (no hash in response, old password no longer works, new password works); **every admin endpoint: anonymous → 401, normal user → 403**.

**Concrete frontend design**

7. **Information architecture**
   - `app/(app)/administracion/` — route group inside the existing `(app)` group. `layout.tsx` performs the **server-side** guard: read the access token from the cookie and call the backend `/auth/me` (or a new `GET /auth/me` variant) — **not** the tampered `USER_SESSION` JSON — and `redirect("/dashboard")` if the role is not admin. `page.tsx` = users list. Optional `usuarios/[id]/page.tsx` = detail drawer/page.
   - `features/admin/usuarios/` — Option A namespaced feature (admin endpoints differ from public ones → per the Next contract §10): `schemas/`, `services/`, `hooks/`, `components/`. `app/` stays routing-only; no logic in pages.
8. **Table columns**: Usuario (avatar + full name), Username, Email, Documento, Rol (badge), Estado (badge), Último acceso (`last_login`), Acciones (row dropdown). No password columns. Sortable: username, created_at, last_login. `AppDataTable` already provides TanStack columns, skeleton loading, error+retry, empty state and pagination controls → reuse it rather than building a new table.
9. **Filters**: search input (debounced via `useDebounce`) + role select + status select + "clear filters"; filter state in the URL query string so it is shareable and survives reload.
10. **Actions / dialogs**: "Crear usuario" (`AppFormModal` + `GenericForm` Mode 1 children + Zod schema), "Cambiar rol" (confirm dialog), "Activar/Desactivar" (`ConfirmationDialog` with an explicit consequence message), "Restablecer contraseña" (dialog), "Ver historial" (read-only sheet). Reuse `components/confirmationDialog`, `components/genericModal`, `components/emptyState`, `components-app/pages/RichEmptyState`, `components/genericPagination/Pagination`.
11. **States**: loading → `AppDataTable` skeleton rows; error → inline error + retry (never a bare toast only); empty → "No hay usuarios" + CTA to create; filtered-empty → "Sin resultados para los filtros" + clear-filters action; 403 → session invalidation + redirect; 409 (last admin) → toast with the backend's public message.
12. **Responsive**: `AppDataTable` already scrolls horizontally; on mobile collapse to a card list (avatar + name + rol + estado) and hide secondary columns; filters collapse into a `Sheet`; dialogs go full-width; actions move from a row dropdown to a card action bar.
13. **Navigation**: add "Administración" to `components/AppSidebar.tsx`, rendered only when the session role is admin (UX only).
14. **Scope separation (recommended)**: the admin UI + admin endpoints are one change; **hardening the pre-existing public endpoints** (`PATCH /inscripciones/{id}`, `POST /equipos/`, the public PII reads, `acreditacion` admin semantics, `persona_busqueda`) is a **separate change** — it alters existing frontend flows and should not be coupled to the admin UI. The user's request to "review/validate all existing endpoints for permission enforcement" is answered by §2 of this report.

**MVP vs later**

- **MVP (this change)**: admin-only user list + filters + pagination; create user; change role; activate/deactivate; reset password (per the blocking question); read-only history; role normalization; admin area + nav + guards.
- **Later (explicitly out)**: full RBAC/groups, multi-role permissions, bulk actions (activate/deactivate many), invitation/import (CSV), export to CSV/XLSX, admin dashboard KPIs/activity charts, in-app notification of role changes, delegation of admin rights, user merge/deactivate-with-data-cleanup, audit log across the whole app (not just `Usuario`).

---

### Risks

1. **Unauthenticated mutations already exist in production code** — `PATCH /inscripciones/{id}` and `POST /equipos/` are `auth=None` with no ownership check, and `GET /inscripciones/{id}/detalle` exposes full rosters (names, documents, phones) to anyone with a UUID. Building an admin area on top of this codebase without fixing these first leaves the highest-severity holes open.
2. **Any authenticated user can currently flip fiesta access and regenerate anyone's QR** (`acreditacion_controller` has no admin/owner check) — the same trust model the admin area will formalize.
3. **Deactivation does not revoke tokens** — `ninja_jwt.token_blacklist` is installed but unused; in development the access token lives 30 days and the refresh token 90 days, so a "disabled" account stays usable unless tokens are invalidated explicitly.
4. **The client-side role is untrusted and stale** — `USER_SESSION` is a non-httpOnly cookie plus a zustand-persisted localStorage copy; `getUserSession()` never revalidates the token. Any frontend-only role gate is bypassable, and role changes will not reflect in the UI until re-login unless a revalidation path is added.
5. **Inconsistent role vocabulary** — `/auth/me` returns a 3-value `rol` string while login/register return `is_staff`/`is_superuser` booleans, and the frontend types the login payload as `MeResponse` (which the backend never returns). Building the admin UI on top of this produces silent `undefined` roles.
6. **A third, invisible admin tier** — `is_superuser` bypasses every check (including `check_ownership_or_admin` and Django admin). If the product only wants USER/ADMIN, `is_superuser` must be deliberately reserved for a break-glass account and never assignable from the admin UI.
7. **The existing `create_user` test fixture is broken** (missing the now-mandatory `persona_fk`) → any new admin test suite will fail until it is fixed; it also must never be used as an "admin" fixture without explicitly setting `is_staff=True`.
8. **No password-change endpoint exists at all**, so a reset password cannot be rotated by the end user afterwards; adding "change my password" may become a de-facto requirement of the admin area.
9. **Pagination contract mismatch** across backend (`PaginatedApiResponse` vs `PaginatedData`) and frontend (`PaginatedResponse`) — no endpoint is paginated today, so the admin list will set the precedent; picking the wrong wrapper now creates a second migration later.
10. **Django admin overlaps the new area** — `/admin/` already provides user management (staff-only) with the same hardcoded `admin/admin` credentials present in two seed commands; the custom area and the Django admin can drift. Decide explicitly whether the Django admin stays in scope (recommend: keep it, restrict to superusers, and rotate the seeded password).

---

### Ready for Proposal

**Yes — with one blocking product question.**

Everything else (backend boundary, endpoints, pagination contract, authorization model, frontend IA, test matrix, MVP split) is decided from verified code and can go straight into `sdd-propose`. The single blocking question is the **credential-delivery model for the admin "reset password" action**, because the project has SMTP configured but no email-sending code, no notification module, no reset-token model and no "change my password" endpoint — so the endpoint contract, the response body and whether a `must_change_password` field (migration) is needed cannot be fixed without the user's answer.

**Blocking question for the orchestrator to ask the user:**

> For the admin "reset password" action, which credential-delivery model should the admin area implement?
> **(a)** The admin sets a temporary password that is communicated out-of-band (UI shows it once, never stored) and the user changes it via a new "change my password" endpoint — requires adding that endpoint and (optionally) a `must_change_password` flag.
> **(b)** The backend generates a one-time reset token/link with an expiry that the user redeems via a new public endpoint — requires a token model/table and a delivery mechanism (email is configured but not implemented).
> **(c)** The backend sends the temporary password by email (SMTP is configured in production; a minimal email service + template would have to be built).
