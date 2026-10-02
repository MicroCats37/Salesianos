# Exploration: izipay-backend-payments

**Date:** 2026-09-21
**Change:** `izipay-backend-payments`
**Project:** Salesianos FEST
**Artifact store:** engram
**Topic key:** `sdd/izipay-backend-payments/explore`

---

## 1. Current State

### What exists today

- `backend/modules/inscripciones/domain/models/inscripcion.py` — `Inscripcion` model with no payment fields. Has `estado` field using `EstadoInscripcionChoices` (RECIBIDA, EN_REVISION, OBSERVADA, VALIDADA, PAGO_PENDIENTE, PAGADA, CONFIRMADA, RECHAZADA).
- `backend/modules/inscripciones/domain/constants.py` — `EstadoInscripcionChoices` already has `PAGADA`.
- `backend/modules/inscripciones/domain/services/flujos/cambiar_estado_inscripcion_flujo.py` — existing flow for state transitions using `CambiarEstadoInscripcionFlujo._cambiar_estado_sync`.
- `backend/config/settings/base.py` — `LOCAL_APPS = ["modules.usuarios", "modules.inscripciones"]` (finanzas and liquidaciones are commented-out). `NINJA_EXTRA.INJECTOR_MODULES` includes `InscripcionesModule`.
- `backend/config/api.py` — registers `InscripcionController`, `DisciplinaController`, `PaqueteController`, etc. Uses `JWTAuth()` globally.
- Backend module structure under `backend/modules/<name>/` follows `domain/`, `presentation/`, `infrastructure/` layout with `models.py` re-export at root.
- `backend/core/models/__init__.py` — `UUIDModel`, `TimestampedModel`, `BaseModel`.
- No existing payment module exists. No `modules/pagos/` exists.

### Reference implementation (context only)

The project at `C:\Users\Usuario\Desktop\my-apps\centro-de-esparcimiento\ninja\domains\finanzas\` is used only to understand a previously working Izipay flow. It is not a rule, contract, template, or source of truth for Salesianos. Every adopted element must be justified against the Salesianos domain, the files under `contract/`, and the current official Izipay documentation. The implementation will intentionally improve or replace reference decisions when they do not fit this project:
- `models/pago.py` — generic `Pago` model with `cajero` (cashier), `tipo=INGRESO/EGRESO`, `metodo`, `referencia`, `metadatos`, `tipo_comprobante`, `serie_correlativo`. Uses `OrdenDeCobro` as the mother account.
- `services/izipay_service.py` — `generar_token_sesion()` (calls Izipay API, generates 14-digit timestamp transactionId, returns token+config), `verificar_y_registrar()` (checks code=="00", idempotency via `referencia=transaction_id`, calls `PagoService.registrar_pago()`, updates order saldo).
- `services/pago_service.py` — `registrar_pago()`, `actualizar_saldo_orden()`, `anular_pago()`.
- `api/pagos.py` — 3 endpoints: `POST /confirmar-manual`, `GET /izipay/preparar/{orden_id}`, `POST /izipay/confirmar`.

### Engram prior observations

- **#7299**: Plan summary — `Inscripcion` as mother account, `/api/pagos/*` routing, 4 SDD phases.
- **#7303**: **Critical correction** — `proveedor=IZIPAY` ≠ `metodo` (TARJETA/YAPE/PLIN/PUSH). `monto_pagado` on `Inscripcion` is **redundant** for v1. Multiple attempts need FK to `Inscripcion`. `transaction_id` is the idempotency key. Never store PAN, CVV, or secrets.
- **#7302**: Existing dev data can be replaced — no backward compatibility required.
- **#7297**: Prior implementation observed — `code="00"`=success, idempotency via `referencia=transaction_id`, pop-up SDK pattern. These are inputs for analysis, not mandatory design decisions.

---

## 2. Affected Areas

### Backend files (read-only inspection)
- `backend/modules/inscripciones/domain/models/inscripcion.py` — **no changes needed for v1**; `PAGADA` state already exists in `EstadoInscripcionChoices`
- `backend/modules/inscripciones/domain/constants.py` — `EstadoInscripcionChoices` already has `PAGADA`
- `backend/config/settings/base.py` — will need `IZIPAY_SHOP_ID`, `IZIPAY_KEY` env vars (future apply)
- `backend/config/api.py` — will register `PagosController` (future apply)
- `backend/config/settings/base.py` — `NINJA_EXTRA.INJECTOR_MODULES` will add `PagosModule` (future apply)

### New files to create (future apply)
- `backend/modules/pagos/` — new Django module following `django-app-architecture-contract.md`
- `backend/modules/pagos/domain/models/pago.py` — **`IzipayTransaccion` model** (NOT the generic `Pago` from reference)
- `backend/modules/pagos/domain/services/izipay_service.py` — token generation + verification
- `backend/modules/pagos/presentation/controllers/pagos_controller.py` — 3 endpoints
- `backend/modules/pagos/presentation/schemas/pago_schema.py` — request/response schemas
- `backend/modules/pagos/di.py` — DI wiring
- `backend/modules/pagos/apps.py` — Django AppConfig
- `backend/modules/pagos/admin.py` — admin registration
- `backend/modules/pagos/migrations/0001_initial.py` — initial migration

### Frontend (out of scope for backend-first apply phases)
- Not inspected — backend phases only

---

## 3. Critical Architectural Decisions

### 3.1 Single-table design: `IzipayTransaccion`

**One table is sufficient for v1.** No separate event/attempt table is needed.

The table models **each Izipay transaction attempt**, linked to `Inscripcion`:

```python
class IzipayTransaccion(BaseModel):
    """
    Registro de cada intento de pago Izipay para una inscripción.
    Un intento por fila. Idempotencia via transaction_id único.
    """
    inscripcion = ForeignKey("inscripciones.Inscripcion", PROTECT, related_name="izipay_transacciones")

    # ── Proveedor ────────────────────────────────────────────
    proveedor = CharField(max_length=20, default="IZIPAY")
    # Siempre "IZIPAY" en v1 — reservado para futuro (e.g. "CULQI", "MERCADO_PAGO")

    # ── Idempotency & gateway keys ──────────────────────────
    transaction_id = CharField(max_length=100, unique=True)
    # ID único del gateway. Generado por el backend como timestamp (14 dígitos).
    # Izipay lo devuelve en kr_answer.transactionId.
    # Es el idempotency key — previene duplicados.

    order_number = CharField(max_length=100, blank=True)
    # Número de orden generado por backend (timestamp 10 dígitos).
    #可比 inIzipay como "orderNumber".

    # ── Amount snapshot ──────────────────────────────────────
    amount = DecimalField(max_digits=10, decimal_places=2)
    currency = CharField(max_length=3, default="PEN")

    # ── Status ───────────────────────────────────────────────
    status = CharField(max_length=20, choices=IzipayStatus.choices)
    # IzipayStatus: PENDIENTE | EXITO | FALLIDO | CANCELADO

    response_code = CharField(max_length=10, blank=True)
    # Código de respuesta del gateway. "00" = éxito.

    response_message = CharField(max_length=500, blank=True)
    # Mensaje legible del gateway.

    # ── Metadata ─────────────────────────────────────────────
    # SOLO datos sanitizados. NUNCA: PAN, CVV, secrets, raw RSA keys.
    # Izipay kr_answer es un dict que puede contener datos sensibles.
    # sanitizar_kr_answer() debe filtrar antes de guardar.
    metadata = JSONField(default=dict, blank=True)

    # ── Payment method (from Izipay response) ───────────────
    metodo_pago = CharField(max_length=30, blank=True)
    # Método real usado: TARJETA, YAPE, PLIN, PAGO_PUSH, etc.
    # Extraído de kr_answer.paymentMethodType o similar.
    # NO confundir con proveedor (IZIPAY).

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["inscripcion", "status"]),
            Index(fields=["transaction_id"]),
            Index(fields=["inscripcion", "created_at"]),
        ]
```

**Indexes explained:**
- `["inscripcion", "status"]` — listar transacciones por estado de una inscripción
- `["transaction_id"]` — lookup idempotency check (unique constraint handles this)
- `["inscripcion", "created_at"]` — historial cronológico de intentos

### 3.2 Why NOT the reference `Pago` model

The reference `Pago` model (with `cajero`, `tipo=INGRESO/EGRESO`, `referencia`, `tipo_comprobante`, `serie_correlativo`) is designed for **cash register accounting**. It does NOT fit Izipay v1 because:

| Reference field | Why it doesn't fit |
|---|---|
| `cajero = ForeignKey(AUTH_USER_MODEL)` | Cashier who records payment. Izipay has no cashier — the payer completes payment in the popup. There is no staff member "receiving" money. |
| `tipo = INGRESO/EGRESO` | Accounting concept for cash management. Not applicable to a payment gateway. Izipay v1 has no refunds/reversals planned. |
| `referencia` (POS lot, phone for Yape) | Cash payment reference field. Not relevant to gateway. |
| `tipo_comprobante`, `serie_correlativo` | Fiscal receipts. Not in scope for v1. |
| `orden = ForeignKey(OrdenDeCobro)` | The "mother account" concept. `Inscripcion` plays this role already. |

**The plan in `doc_dev/IZIPAY_SALESIANOS_PLAN.md` inherits this wrong model.** This must be replaced with `IzipayTransaccion`.

### 3.3 `proveedor=IZIPAY` vs `metodo_pago`

These are two different concepts:

- **`proveedor`** (provider/gateway): Who processes the payment. Always `"IZIPAY"` in v1. Future: `"CULQI"`, `"MERCADO_PAGO"`, etc.
- **`metodo_pago`** (payment method): How the customer paid. From Izipay response: `"TARJETA"`, `"YAPE"`, `"PLIN"`, `"PAGO_PUSH"`, etc.

The plan correctly distinguishes them in the frontend section but incorrectly uses the reference's `metodo` (which is actually an enum of payment methods, not distinguishing from provider). The backend model must track both.

### 3.4 Multiple attempts per inscription

The `Inscripcion.estado` transitions for Izipay:

```
RECIBIDA → PAGO_PENDIENTE → PAGADA
              ↑
              └─ (intentos fallidos mantienen PAGO_PENDIENTE)
```

Each Izipay attempt gets its own `IzipayTransaccion` row. The `Inscripcion.estado` only advances to `PAGADA` when a transaction with `code="00"` is confirmed. Failed attempts keep it in `PAGO_PENDIENTE`.

**No separate "attempt" table needed** — the `IzipayTransaccion` table IS the attempt table. Its `status` field captures the lifecycle of each attempt.

### 3.5 `transaction_id` idempotency

- Generated by backend as `str(int(time.time() * 1000)).rjust(14, "0")[:14]` (14-digit timestamp).
- Sent to Izipay API as `transactionId` header.
- Izipay returns it in `kr_answer.transactionId`.
- Before creating a new `IzipayTransaccion`, check `.objects.filter(transaction_id=...).exists()`.
- If exists with `status=EXITO`: return success (already processed).
- If exists with `status=PENDIENTE`: may be in-progress; return error or wait.

### 3.6 `order_number`

- Generated as `str(int(time.time() * 1000000))[:10]` (10-digit microtimestamp).
- Different from `transaction_id` — `transaction_id` is for idempotency, `order_number` is for Izipay's order tracking.
- Stored for audit/debugging.

### 3.7 Amount snapshot

- `amount` and `currency` are stored as a **snapshot at token generation time**.
- The amount comes from `inscripcion.paquete.precio_total`.
- Stored on `IzipayTransaccion` to preserve what was actually charged, even if the package price changes later.
- Never trust `kr_answer.order.amount` alone — use the DB snapshot.

### 3.8 Statuses and response codes

```
IzipayStatus (TextChoices):
    PENDIENTE  = "PENDIENTE",  "Pendiente — token generado, esperando pop-up"
    EXITO      = "EXITO",      "Éxito — código 00 confirmado"
    FALLIDO    = "FALLIDO",    "Fallido — código distinto de 00"
    CANCELADO  = "CANCELADO",  "Cancelado — usuario cerró el pop-up"
```

Response code is stored in `response_code` as a string. `"00"` is success.

### 3.9 Sanitized metadata — what to NEVER store

**CRITICAL:** `kr_answer` from Izipay can contain sensitive data. The `metadata` JSONField must be **sanitized before storage**.

Never store in `metadata`:
- PAN (card numbers) — even masked
- CVV/CVC
- Izipay `privateKey`, `encryptionKey`, `secret` fields
- Full card data objects
- Raw RSA keys

What IS safe to store (after sanitization):
- `transactionId`
- `orderNumber`
- `amount`, `currency`
- `paymentMethodType` (the payment method used)
- `cardScheme` (Visa/Mastercard brand, no card number)
- `installmentNumber` (cuotas)
- `invoiceHeader`, `transactionDate`
- `clientData` (email only — already provided by customer)

A `sanitizar_kr_answer(kr_answer: dict) -> dict` function is required in `IzipayService`.

### 3.10 `monto_pagado`, `cajero`, `ingreso/egreso` — what belongs in v1

| Concept | Belongs in v1? | Reason |
|---|---|---|
| `IzipayTransaccion` (one per attempt) | ✅ YES | Core of the payment module |
| `proveedor = "IZIPAY"` | ✅ YES | Distinguishes Izipay from future providers |
| `metodo_pago` (TARJETA/YAPE/etc.) | ✅ YES | Real payment method from Izipay |
| `transaction_id` (idempotency) | ✅ YES | Prevents duplicate charges |
| `order_number` | ✅ YES | Audit trail |
| `amount` snapshot | ✅ YES | Preserves what was charged |
| `status` / `response_code` | ✅ YES | Tracks attempt outcome |
| `metadata` (sanitized) | ✅ YES | Full response for debugging |
| `Inscripcion.monto_pagado` | ❌ NO | **Redundant** — `IzipayTransaccion.amount` + `status=EXITO` is the source of truth |
| `Inscripcion.saldo_pendiente` | ❌ NO | No partial payments in v1; amount is fixed |
| `cajero` (ForeignKey to User) | ❌ NO | No cashier for Izipay payments |
| `tipo` (INGRESO/EGRESO) | ❌ NO | No accounting/journal entries in v1 |
| `tipo_comprobante`, `serie_correlativo` | ❌ NO | No fiscal receipts in v1 |

### 3.11 `Inscripcion.estado = PAGADA` consistency

Rule: `Inscripcion.estado` advances to `PAGADA` **only** when:
1. `IzipayService.verificar_y_registrar()` receives `code == "00"` from Izipay
2. A new `IzipayTransaccion` row with `status=EXITO` is created (or existing one confirmed)

No `monto_pagado` accumulation needed. The existence of a successful transaction is the signal.

The `InscripcionOrchestrator` should **not** be modified to call payment logic. Payment confirmation flow is isolated in `IzipayService.verificar_y_registrar()`, which directly calls `InscripcionService.actualizar_estado()`.

### 3.12 `Inscripcion.monto_pagado` — not needed

The `IzipayTransaccion.amount` field of the **successful** transaction IS the amount paid. There is no partial payment in v1. The `Inscripcion` model should **not** get a `monto_pagado` field — it would be derived data that's redundant and risks desync.

**Contradiction in the plan:** Section 4.1 adds `monto_pagado` to `Inscripcion`, but this conflicts with observation #7303 which correctly states it's redundant. The plan must be corrected to remove this field.

---

## 4. Contradictions in Current Plan

| Plan section | Problem | Correction |
|---|---|---|
| Section 4.1 — `Inscripcion.monto_pagado` | Redundant; desyncs with `IzipayTransaccion` | Remove; derive from successful transaction |
| Section 4.1 — `cajero` ForeignKey on `Pago` | No cashier for Izipay; wrong model | Replace with `IzipayTransaccion` (no cajero field) |
| Section 4.1 — `tipo=INGRESO/EGRESO` on `Pago` | Accounting concept not applicable to gateway | Not needed in v1; remove |
| Section 4.1 — `referencia` as POS lot/Yape number | Cash reference; not gateway concept | `transaction_id` is the reference for idempotency |
| Section 4.3 — Phase 1 includes "register controller in api.py" | Controllers don't exist yet | Split: Phase 1 is migrations/models only |
| Section 4.3 — Phase 1 includes "add Izipay settings" | Settings are for later phase | Move to Phase 2 |
| Section 4.3 — Phase 1 includes "register PagosModule in NINJA_EXTRA" | DI is for later phase | Move to Phase 2 |
| Section 4.6 — `PagoOut` uses `cajero_nombre` | Cajero doesn't exist for Izipay | `IzipayTransaccionOut` has no cajero field |
| Section 4.7 — `EstadoPago` TextChoices | Not needed for v1; `IzipayTransaccion.status` suffices | Remove; use `IzipayStatus` instead |
| Section 4.8 — `PermisosPagos` | Permissions layer not needed for v1 | Defer to future phase |
| Section 4.9 — migration "add monto_pagado to Inscripcion" | Redundant field | Remove migration |
| Section 4.10 — tests for `registrar_pago`, `calcular_monto_pago_inscripcion` | These methods don't match the Izipay model | Rewrite for `IzipayTransaccion` flow |
| Section 7 risks — "monto_pagado desync" | Only a risk because the plan introduces it | Remove field to eliminate risk |

---

## 5. Recommended Apply Phases (Backend)

### Apply Phase 1: Database Foundation — `IzipayTransaccion` model + migration
**Scope:** Model + migration only. No controllers, no services, no settings, no DI.

**Files created:**
- `backend/modules/pagos/__init__.py`
- `backend/modules/pagos/apps.py`
- `backend/modules/pagos/domain/__init__.py`
- `backend/modules/pagos/domain/constants.py` — `IzipayStatus` TextChoices only
- `backend/modules/pagos/domain/models/__init__.py`
- `backend/modules/pagos/domain/models/pago.py` — `IzipayTransaccion` model (NOT generic `Pago`)
- `backend/modules/pagos/domain/exceptions.py` — `IzipayError`, `TransaccionDuplicadaError`
- `backend/modules/pagos/migrations/__init__.py`
- `backend/modules/pagos/migrations/0001_initial.py`

**Files modified:**
- `backend/config/settings/base.py` — **add `modules.pagos` to `LOCAL_APPS`**
- `backend/config/settings/base.py` — **add `IZIPAY_SHOP_ID`, `IZIPAY_KEY`, `IZIPAY_API_URL` to env vars**

**Files NOT modified (deferred to later phases):**
- `config/api.py` — controller not registered yet
- `NINJA_EXTRA.INJECTOR_MODULES` — DI not wired yet
- `Inscripcion` model — no changes needed for v1

**Exclusions:**
- No controller, no orchestrator, no service, no schemas
- No frontend changes
- No `PagosModule` DI wiring
- No `PermisosPagos`

**Invariants:**
- `IzipayTransaccion.transaction_id` is unique (DB constraint)
- `IzipayTransaccion.inscripcion` FK to `Inscripcion` with PROTECT
- `IzipayTransaccion` has `proveedor`, `transaction_id`, `order_number`, `amount`, `currency`, `status`, `response_code`, `response_message`, `metadata`, `metodo_pago`
- `IzipayStatus` TextChoices with PENDIENTE, EXITO, FALLIDO, CANCELADO
- `Inscripcion` model unchanged

**Verification commands:**
```bash
# Migration exists and can be applied
cd backend && python manage.py makemigrations pagos --dry-run

# Model imports without error
cd backend && python -c "from modules.pagos.domain.models import IzipayTransaccion, IzipayStatus; print('OK')"

# Showmigration output
cd backend && python manage.py showmigrations pagos
```

**Tests for Phase 1:** None — model creation only. Tests belong to the phase that implements services.

---

### Apply Phase 2: IzipayService + Schemas + Orchestrator
**Scope:** Business logic, HTTP schemas, orchestrator. No controller registration yet.

**Files created:**
- `backend/modules/pagos/domain/services/core/izipay_core_service.py` — `IzipayCoreService` (sync core: create_transaccion, update_status, get_by_transaction_id)
- `backend/modules/pagos/domain/services/flujos/registrar_pago_izipay_flujo.py` — `RegistrarPagoIzipayFlujo` (async, transaction.atomic)
- `backend/modules/pagos/domain/services/orchestrators/pagos_orchestrator.py` — `PagosOrchestrator` (async, thin)
- `backend/modules/pagos/presentation/schemas/pago_schema.py` — `IzipayTokenIn`, `IzipayConfirmIn`, `IzipayTransaccionOut`
- `backend/modules/pagos/domain/schemas/__init__.py`
- `backend/modules/pagos/domain/schemas/result.py` — `PagoIzipayResult`
- `backend/modules/pagos/presentation/presenters/pago_presenter.py` — `IzipayPresenter`

**Files modified:**
- None for this phase (phase 1 did settings + installed app)

**Files NOT modified:**
- `config/api.py` — controller not registered yet
- `NINJA_EXTRA.INJECTOR_MODULES` — DI wiring deferred

**Exclusions:**
- No controller, no API endpoint registration
- No manual payment endpoint

**Invariants:**
- `IzipayCoreService` has `crear_transaccion()` (generates transaction_id, order_number), `actualizar_estado()`, `obtener_por_transaction_id()`, `es_duplicada()`
- `RegistrarPagoIzipayFlujo._registrar_sync()` wraps `IzipayCoreService` in `transaction.atomic`
- `_registrar_sync()` calls `InscripcionService.actualizar_estado()` when code=="00"
- `IzipayService._sanitizar_kr_answer()` strips PAN, CVV, secrets from metadata
- `IzipayPresenter` transforms `IzipayTransaccion` → `IzipayTransaccionOut`

**Verification commands:**
```bash
cd backend && python -c "
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
from modules.pagos.domain.services.orchestrators.pagos_orchestrator import PagosOrchestrator
from modules.pagos.presentation.schemas.pago_schema import IzipayTransaccionOut
print('All imports OK')
"
```

**Tests for Phase 2:**
```python
# modules/pagos/tests/integration/test_izipay_core_service.py
# - test_crear_transaccion_genera_transaction_id_unico
# - test_crear_transaccion_guarda_amount_snapshot
# - test_actualizar_estado_exito_cambia_status
# - test_actualizar_estado_fallido_cambia_status
# - test_es_duplicada_retorna_true_cuando_existe
# - test_es_duplicada_retorna_false_cuando_no_existe
```

---

### Apply Phase 3: Controller + DI Wiring + API Registration
**Scope:** Thin controller, DI wiring, API registration. This is the "wiring" phase that connects phases 1+2 to the HTTP layer.

**Files created:**
- `backend/modules/pagos/presentation/controllers/pagos_controller.py` — `PagosController` (3 endpoints)
- `backend/modules/pagos/di.py` — `PagosModule` with injector bindings

**Files modified:**
- `backend/config/api.py` — `api.register_controllers(PagosController)`
- `backend/config/settings/base.py` — add `'modules.pagos.di.PagosModule'` to `NINJA_EXTRA.INJECTOR_MODULES`

**Exclusions:**
- No new models, no new services
- No manual payment endpoint (deferred to future)

**Invariants:**
- `PagosController` is thin — only delegates to `PagosOrchestrator`
- Three endpoints registered:
  1. `GET /pagos/izipay/preparar/{inscripcion_id}` → `IzipayTokenOut`
  2. `POST /pagos/izipay/confirmar` → dict (success/error)
  3. `POST /pagos/manual` → deferred to future phase (not in scope for v1)
- Controller uses `JWTAuth()`
- All exceptions raised via `HttpError` from orchestrator/service, not caught in controller

**Verification commands:**
```bash
# API docs accessible
curl http://localhost:8000/api/pagos/docs

# OpenAPI schema contains our endpoints
curl http://localhost:8000/api/pagos/openapi.json | python -c "import sys,json; d=json.load(sys.stdin); print(list(d.get('paths',{}).keys()))"
```

**Tests for Phase 3:**
```python
# modules/pagos/tests/integration/test_pagos_controller.py
# Use TestAsyncClient or django.test.Client (NOT ninja.testing.TestClient for async)
# - test_preparar_endpoint_returns_token_success
# - test_preparar_endpoint_returns_error_cuando_inscripcion_ya_pagada
# - test_confirmar_endpoint_crea_transaccion_y_actualiza_estado
# - test_confirmar_endpoint_retorna_error_cuando_code_no_es_00
# - test_confirmar_endpoint_ignora_duplicado_por_transaction_id
```

---

### Apply Phase 4: Tests + Verification
**Scope:** Full test suite, manual E2E verification steps.

**Files created:**
- `backend/modules/pagos/tests/__init__.py`
- `backend/modules/pagos/tests/conftest.py`
- `backend/modules/pagos/tests/factories.py`
- `backend/modules/pagos/tests/fixtures/__init__.py`
- `backend/modules/pagos/tests/fixtures/inscripciones_fixtures.py`
- `backend/modules/pagos/tests/fixtures/usuarios_fixtures.py`
- `backend/modules/pagos/tests/integration/test_izipay_core_service.py`
- `backend/modules/pagos/tests/integration/test_registrar_pago_izipay_flujo.py`
- `backend/modules/pagos/tests/integration/test_pagos_controller.py`

**Verification commands:**
```bash
# All tests pass
pytest backend/modules/pagos/tests/ -v

# Showmigrations confirms all applied
python manage.py showmigrations pagos

# No unappliedInscripcion migrations
python manage.py showmigrations inscripciones
```

---

## 6. Summary of Corrections to Plan Document

The following sections of `doc_dev/IZIPAY_SALESIANOS_PLAN.md` must be **replaced** in the documentation edit:

1. **Section 4.1** — Replace entire `Pago` model design with `IzipayTransaccion` (provider field, no cajero, no tipo INGRESO/EGRESO, metodo_pago separate from proveedor)
2. **Section 4.1** — Remove `Inscripcion.monto_pagado` field addition
3. **Section 4.2** — Replace file tree with correct architecture (no `pago_service.py`, new `izipay_core_service.py`, `registrar_pago_izipay_flujo.py`, `pagos_orchestrator.py`)
4. **Section 4.3** — Rewrite as 4 modular apply phases (Phase 1 = migrations only, no controller registration)
5. **Section 4.4** — Replace `PagoService` with `IzipayCoreService` + `RegistrarPagoIzipayFlujo`
6. **Section 4.5** — Update controller to reflect only Izipay endpoints (manual endpoint deferred)
7. **Section 4.6** — Replace `PagoOut` with `IzipayTransaccionOut` (no cajero_nombre)
8. **Section 4.7** — Remove `EstadoPago` (use `IzipayStatus`)
9. **Section 4.8** — Remove `PermisosPagos` (defer)
10. **Section 4.9** — Remove `monto_pagado` migration for Inscripcion
11. **Section 4.10** — Replace test file list with `IzipayCoreService` + `Flujo` tests
12. **Section 6** — Rewrite phases as backend-first modular applies (Phase 1 = model+migration only)
13. **Section 7** — Remove "monto_pagado desync" risk (field removed)

---

## 7. Risks

1. **Wrong model design inherited from reference** — The reference `Pago` model is for cash register accounting, not payment gateways. Applying it would introduce `cajero`, accounting `tipo`, fiscal fields that don't make sense for Izipay. **Resolved** by defining `IzipayTransaccion` correctly.
2. **Sensitive data in metadata** — `kr_answer` from Izipay may contain PAN/CVV/secrets. Must sanitize before storing in `metadata` JSONField. **Mitigation:** `sanitizar_kr_answer()` function strips sensitive keys.
3. **No partial payments in v1** — The plan assumes fixed amount. If partial payments are needed later, the schema would need revision. **Mitigation:** Document as v1 scope limitation.
4. **`Inscripcion.estado = PAGADA` must not be set by multiple code paths** — If any other part of the codebase can set `PAGADA` independently, the Izipay flow might not trigger. **Mitigation:** `IzipayService` is the sole setter of `PAGADA`; no other code path should set it.
5. **Izipay credentials not configured** — If `IZIPAY_SHOP_ID`/`IZIPAY_KEY` are empty strings, `generar_token_sesion` returns `{"success": False, "error": "Credenciales..."}`. Frontend handles this gracefully.
6. **`Inscripcion` model has no payment fields** — The plan added `monto_pagado` but this is redundant. Since no such field exists currently, no migration is needed. **Resolved** by not adding it.
