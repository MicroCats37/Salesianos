# Exploration: Phase 8 — Salesianos FEST Seeds, Comprehensive Tests & Verifiable Cutover

## Status: COMPLETE

---

## 1. Contract Architecture Summary

### Key Contracts Read
- `contract/TEST_ARCHITECTURE_CONTRACT.md` — Gold-standard: `backend/modules/liquidaciones/tests/`
- `contract/django-app-architecture-contract.md` — 4-layer async pattern (controller → orchestrator → flujo → core)
- `contract/PLAN_REFACTORIZACION.md` — Strict controller/presenter/rules
- `contract/next-app-architecture-contract.md` — Frontend Next.js architecture

### Critical Test Architecture Rules (from TEST_ARCHITECTURE_CONTRACT)
| Aspect | Tool |
|--------|------|
| Test runner | pytest + `@pytest.mark.django_db` |
| HTTP test client | **`django.test.Client`** (handles async controllers) |
| Auth | `ninja_jwt.tokens.AccessToken.for_user(user)` |
| Database | Real Django DB via `@pytest.mark.django_db` |
| NO mocking | Fixture parameterization |
| NO `factory_boy` | `factories.py` pure dict functions |
| NO `unittest.mock.patch` | Fixture parameterization |
| NO `ninja.testing.TestClient` for async | Use `django.test.Client` or `ninja_extra.testing.TestAsyncClient` |

### Critical Async Rule (django-app-architecture-contract §2.1)
- **Controllers are async** — chain: `async controller` → `async orchestrator` → `async flujo` → `sync core`
- For async controllers: use `django.test.Client` (sync but handles async internally) or `ninja_extra.testing.TestAsyncClient` with `async def` tests + `asyncio_mode="auto"`
- **`ninja.testing.TestClient` is PROHIBITED** for async controllers — causes `AttributeError: 'coroutine' object has no attribute 'status_code'`

---

## 2. Seeds / Bootstrap Inventory

### Existing Seed Commands
| Command | Location | Scope |
|---------|----------|-------|
| `seed_catalogo_fest` | `backend/modules/salesianos_fest/management/commands/seed_catalogo_fest.py` | Creates Evento, Promociones, Categorías, Disciplinas, Paquetes, Precios, Beneficios |
| `seed_admin` | `backend/modules/usuarios/management/commands/seed_admin.py` | Creates admin user |
| `seed_perfiles_ingeniero_faltantes` | `backend/modules/usuarios/management/commands/` | Perfiles ingeniero |
| `seed_colegiados` | `backend/modules/usuarios/management/commands/` | Colegiados |

### seed_catalogo_fest Details
- **Idempotent**: uses `get_or_create`
- **Supports `--clear`**: deletes and recreates catalog
- Creates: 1 Evento ("Salesianos FEST 2026"), 4 Promociones, 7 Categorías, 4 Disciplinas, 8+ Paquetes
- No user/responsable seeding — only catalog data
- **Gap**: No seed creates Personas, Inscripciones, or transaction data

---

## 3. T01–T23 Coverage Inventory

### Test Files in `backend/modules/salesianos_fest/tests/integration/`

| File | Coverage | T-Numbers |
|------|----------|-----------|
| `test_catalogo.py` | Catalog endpoints (disciplinas, promociones, categorías, paquetes) | T01–T03 (catalog browsing) |
| `test_inscripcion.py` | Inscripcion CRUD, equipo creation, roster management, participacion, R11 conflict, fecha_limite | T04–T13, T17–T20 |
| `test_compra.py` | Compra creation, iniciar_pago (Izipay mock), confirmar_pago, idempotency | T14?, T16 |
| `test_asignacion.py` | AsignacionCupo, saldo calculation, T14 concurrent cupo, T15 concurrent QR scans | T14, T15 |
| `test_acreditacion.py` | AcreditacionEvento sync, admin override, QR single-use scan | T21–T23 |

### T-Number Mapping (from exploration artifacts and test comments)

| T-Number | Description | Location |
|----------|-------------|----------|
| T01 | Listar disciplinas | `test_catalogo.py` |
| T02 | Listar promociones | `test_catalogo.py` |
| T03 | Listar paquetes con precios | `test_catalogo.py` |
| T04 | Crear inscripción | `test_inscripcion.py:test_crear_inscripcion_http` |
| T05 | Obtener inscripción | `test_inscripcion.py:test_obtener_inscripcion` |
| T06 | Actualizar inscripción | `test_inscripcion.py:test_actualizar_inscripcion_http` |
| T07 | Agregar persona a roster | `test_inscripcion.py:test_agregar_y_retirar_persona_http` |
| T08 | Agregar persona con aceptaciones | `test_inscripcion.py:test_agregar_persona_con_aceptaciones` |
| T09 | Idempotencia aceptaciones | `test_inscripcion.py:test_agregar_persona_aceptaciones_idempotente` |
| T10 | Crear equipo | `test_inscripcion.py:test_crear_equipo_http` |
| T11 | Listar equipos por inscripción | `test_inscripcion.py:test_listar_equipos_por_inscripcion` |
| T12 | Crear participación | `test_inscripcion.py:test_crear_participacion_http` |
| T13 | R11 — duplicate active participation blocked | `test_inscripcion.py:test_r11_prevent_duplicate_active_participacion_same_evento_disciplina` |
| T14 | Concurrent last-quota allocation | `test_asignacion.py:test_t14_concurrent_ultimo_cupo_desde_dos_requests` |
| T15 | Concurrent QR scans (single-use) | `test_asignacion.py:test_t15_concurrent_qr_scans_simultaneos` |
| T16 | Ampliación no duplica beneficios | `test_compra.py:test_t16_ampliacion_no_duplica_beneficios` |
| T17 | Retirar persona retira cascade participaciones | `test_inscripcion.py:test_retirar_persona_retires_all_its_participaciones` |
| T18 | Roster máximo bloquea participación | `test_inscripcion.py:test_roster_maximo_blocks_participacion` |
| T19 | Fecha límite agregado bloqueado | `test_inscripcion.py:test_t20_agregar_persona_despues_de_fecha_limite_bloqueado` |
| T20 | Fecha límite removal permitido | `test_inscripcion.py:test_t20_agregar_persona_sin_fecha_limite_permitido` |
| T21 | Acreditación sync from pago | `test_acreditacion.py:test_acreditacion_sync_con_fiesta` |
| T22 | Admin override fiesta | `test_acreditacion.py:test_override_fiesta_bloquear` |
| T23 | QR scan single-use | `test_acreditacion.py:test_qr_scan_primer_intento_permitido`, `test_qr_scan_segundo_intento_denegado` |

### Coverage Gaps
- **No explicit T01–T03 tests** labeled as such (but catalog tests exist)
- **T14/T15**: Implemented via `threading` + `asyncio` — not true concurrency but sufficient for DB-level locking tests
- **No T16 test labeled "T16"** in catalog — `test_t16_ampliacion_no_duplica_beneficios` is in `test_compra.py`
- **T20 is actually T20 in test file** (not T20 for fecha límite, but tests exist)

---

## 4. Async HTTP / Security / Concurrency / Postgres / Izipay Testing Capability

### Async HTTP Testing
| Pattern | Status | Evidence |
|--------|--------|----------|
| `django.test.Client` for async controllers | ✅ WORKS | Used in all `salesianos_fest` tests |
| `ninja.testing.TestClient` for async | ❌ PROHIBITED | Causes coroutine AttributeError |
| `ninja_extra.testing.TestAsyncClient` | ⚠️ AVAILABLE but not used in salesianos_fest | Used in `pagos` module async tests |
| `async def` + `@pytest.mark.asyncio` | ✅ Available | Used in `pagos/test_izipay_core_service.py` |
| `AsyncMock` for patching async methods | ✅ Works | `test_compra.py` uses `AsyncMock` for Izipay |

### Security Testing
| Pattern | Status | Evidence |
|--------|--------|----------|
| JWT auth via `AccessToken.for_user()` | ✅ Implemented | `_auth_post()` helper in all test files |
| Owner-only endpoints (403 on non-owner) | ✅ Tested | `test_crear_compra_no_owner_denied`, `test_iniciar_pago_no_owner_denied` |
| Non-authenticated access | ✅ Public endpoints use `auth=None` | Controller decorator: `auth=None` |
| Admin-only override (is_staff) | ✅ Tested | `test_override_fiesta_bloquear` uses `admin_user` |

### Concurrency Testing
| Pattern | Status | Evidence |
|--------|--------|----------|
| `threading.Thread` + `asyncio.new_event_loop()` | ✅ Implemented | `test_t14_concurrent_ultimo_cupo`, `test_t15_concurrent_qr_scans` |
| DB-level locking verification | ✅ Works | Tests verify only 1 `AsignacionCupo` or 1 `PERMITIDO` ControlAcceso |
| Race condition on last-quota | ✅ Tested | T14 passes in CI |
| Double QR scan race | ✅ Tested | T15 passes in CI |

### Postgres Testing
| Aspect | Status | Evidence |
|--------|--------|----------|
| Real PostgreSQL via `@pytest.mark.django_db` | ✅ Used everywhere | All test files |
| `transaction=True` for true isolation | ✅ Used on T14/T15 | `@pytest.mark.django_db(transaction=True)` |
| Unique constraints enforced | ✅ Tested | `test_inscripcion_unique_constraint_same_evento_responsable_paquete` |

### Izipay Testing
| Pattern | Status | Evidence |
|--------|--------|----------|
| `AsyncMock` + `patch` for `generar_token_sesion` | ✅ Implemented | `test_iniciar_pago_success` |
| IzipayCoreService unit tests | ✅ Full suite | `pagos/tests/integration/test_izipay_core_service.py` (562 lines) |
| `confirmar_pago` idempotency | ✅ Tested | `test_confirmar_pago_idempotente`, `test_confirmar_pago_no_duplicate_callback_safety` |
| `sync_to_async` for ORM calls in async tests | ✅ Used | `test_izipay_core_service.py` uses `sync_to_async` |

---

## 5. Legacy Remnants Inventory

### From grep results — `legacy` keyword matches

| File | Legacy Item | Notes |
|------|------------|-------|
| `modules/usuarios/domain/models/usuario.py:80` | `dni` field with `verbose_name="DNI legacy"` | Kept for compatibility — identity now lives in `Persona` |
| `modules/usuarios/domain/schemas/auth_result_schemas.py:18` | `dni_legacy: str \| None` | Backward compatibility for old users |
| `modules/usuarios/domain/services/core/auth_core_service.py:38,51,60` | `dni_legacy` references | Fallback for legacy users with populated `Usuario.dni` |
| `modules/usuarios/presentation/schemas/auth_schemas.py:36` | `dni_legacy: str \| None` | Exposed in auth response |
| `modules/usuarios/presentation/presenters/auth_presenter.py:35` | `dni_legacy=result.user.dni_legacy` | Maps to output |
| `modules/usuarios/management/commands/seed_admin.py:47` | `help="DNI legacy del Usuario"` | Admin seed command |
| `modules/usuarios/migrations/0001_initial.py:97,108,488,498` | `dni` legacy fields in migrations | Historical |
| `core/decorators.py:16` | `requiere_permiso is deprecated` | Warning comment |
| `core/security.py:59` | `verificar_permisos_usuario is deprecated` | Warning comment |
| `core/utils.py:45` | `legacy / llaves separadas` comment | Internal comment |
| `salesianos_fest/presentation/schemas/__init__.py` | `# Phase 1 scaffold — no Phase 2 catalog schemas yet` | Placeholder comment |
| `salesianos_fest/presentation/presenters/__init__.py` | `# Phase 1 scaffold — no presenters yet` | Placeholder comment |

### Placeholder Infrastructure Files (not legacy, just empty)
| Path | Notes |
|------|-------|
| `modules/usuarios/views.py` | "Views placeholder — define views here when needed" |
| `modules/usuarios/infrastructure/*` | All are placeholder stubs |
| `modules/salesianos_fest/infrastructure/selectors/__init__.py` | "Phase 1 scaffold" |

### Phase 6 — Persona.acepto_* Removal (from exploration)
- `modules/usuarios/domain/models/persona.py` still has `acepto_bases`, `acepto_aptitud_fisica`, `acepto_imagen` booleans
- These are NOT YET removed — Phase 6 consentimientos not applied
- `AceptacionInscripcion` model already exists in `salesianos_fest/domain/models/aceptacion_inscripcion.py`
- Tests already cover `agregar_persona_con_aceptaciones` and idempotency

---

## 6. Exact Edit / Test Roots

### Edit Roots (for Phase 8 implementation)
| Area | Path | Notes |
|------|------|-------|
| Domain Models | `backend/modules/salesianos_fest/domain/models/` | 17 model files |
| Domain Services | `backend/modules/salesianos_fest/domain/services/` | Orchestrators + Flujos + Core |
| Presentation | `backend/modules/salesianos_fest/presentation/` | Controllers + Schemas + Presenters |
| Seeds | `backend/modules/salesianos_fest/management/commands/seed_catalogo_fest.py` | Already exists |
| Tests | `backend/modules/salesianos_fest/tests/` | `integration/` + `e2e/` + `factories.py` + `conftest.py` |

### Test Roots
| Path | Purpose |
|------|---------|
| `backend/modules/salesianos_fest/tests/integration/` | 5 test files covering T01–T23 |
| `backend/modules/salesianos_fest/tests/factories.py` | Pure dict builders for all models |
| `backend/modules/salesianos_fest/tests/conftest.py` | Root conftest with event/disciplina/promo/cat/paquete fixtures |
| `backend/modules/salesianos_fest/tests/integration/conftest.py` | Empty — imports happen at root level |
| `backend/modules/pagos/tests/integration/test_izipay_core_service.py` | Full Izipay async test suite |
| `backend/conftest.py` | Project-level fixtures including `test_async_client` |

### Key Fixtures Already Defined
- `api_client(db)` — returns `django.test.Client`
- `evento`, `disciplina_futbol/m`, `disciplina_futbol_f`, `disciplina_voley`, `disciplina_basquet`
- `promocion_junior`, `promocion_senior`
- `categoria_senior`
- `paquete_reencuentro`, `paquete_futbol`, `paquete_duo`
- `persona`, `persona_2`, `persona_3`
- `usuario_con_persona`, `usuario_otro`, `admin_user`
- `inscripcion_base`, `inscripcion_persona_base`, `equipo_base`

---

## 7. Blockers

### 🔴 CRITICAL (block Phase 8 apply)

1. **No SDD artifacts found for Phase 8** — `sdd/salesianos-fest-fase-8-release/` does not exist
   - No `proposal.md`, `spec.md`, `design.md`, or `tasks.md` found
   - Cannot proceed without explicit scope definition from user

2. **Phase 6 consentimientos NOT applied** — `Persona.acepto_*` fields still exist
   - `AceptacionInscripcion` model already exists in `salesianos_fest/domain/models/aceptacion_inscripcion.py`
   - Tests for aceptaciones pass but the legacy fields remain in `Persona`
   - This is a DATA SAFETY issue for Phase 8 — mixed state

3. **No spec document found** — Phase 8 scope undefined
   - User said "seeds, comprehensive tests, and verifiable cutover" but no artifact defines what Phase 8 IS
   - Need spec before design/tasks can be created

### 🟡 WARNINGS (non-blocking but notable)

4. **`django.test.Client` used instead of `TestAsyncClient`** — All `salesianos_fest` tests use sync `Client`
   - This WORKS for the current implementation because controllers delegate to sync orchestrators
   - But if controllers become truly async (with `sync_to_async` chains), this may hide async issues
   - The contract requires `django.test.Client` for sync-style tests — current usage is compliant

5. **No E2E tests found** — `tests/e2e/` directory exists but `conftest.py` is empty
   - No actual E2E tests in `salesianos_fest`
   - Only integration tests exist

6. **T14/T15 use threading, not true async concurrency** — Tests work via `asyncio.new_event_loop()` in threads
   - Sufficient for DB-level locking verification
   - Not a true load test

---

## 8. Phase 8 Scope Assessment

Based on user request: **"seeds, comprehensive tests, and verifiable cutover"**

### What Phase 8 Likely Means
1. **Seeds**: Expand `seed_catalogo_fest` to include Personas, Inscripciones, Compras mock data for demo/QA
2. **Comprehensive tests**: Fill T01–T23 gaps, add E2E tests, add true async tests
3. **Verifiable cutover**: Migration verification, data integrity checks, rollback plan

### What Needs to be Defined
- Exact Phase 8 deliverables
- Which phases are already completed vs. in-flight
- Whether Phase 6 consentimientos must be applied first
- Cutover criteria: what "verifiable" means in this context

---

## 9. Ready for Proposal

**NO** — Blocked by:
1. No Phase 8 SDD artifacts exist (no proposal/spec/design/tasks)
2. Phase 6 consentimientos not applied (legacy state)
3. Scope of "seeds, comprehensive tests, verifiable cutover" not formally defined

**The orchestrator should tell the user:**
- Phase 8 SDD artifacts must be created via `sdd-propose` before `sdd-explore` for Phase 8 can proceed
- Phase 6 (`AceptacionInscripcion` + Persona boolean removal) appears incomplete — confirm if Phase 6 apply is needed first
- If Phase 8 is about seeds + tests + cutover verification, the user needs to provide/confirm:
  - What seeds are needed beyond `seed_catalogo_fest`
  - Which T-numbers are actually missing from current coverage
  - What "verifiable cutover" means (migration? deployment? data validation?)
