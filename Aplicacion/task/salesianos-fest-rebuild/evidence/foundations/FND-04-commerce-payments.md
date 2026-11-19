# FND-04 — Shared commerce and payment attempts

**Artifact:** `evidence/foundations/FND-04-commerce-payments.md` · **Packet:** FND-04 (`wave-01-foundations`) · **Owner:** A2
**Original task IDs:** `T-013`, `T-014` (2 of the 54 source-defined IDs; cumulative with GOV-00/01/02, FND-01, FND-02, FND-03: **14 of 54**)
**Freeze:** `FREEZE-CM-1.0.0` (`FR-04`) · `FREEZE-ENV-1.0.0` (`FR-01` §5) · `FREEZE-PS-1.0.0` (`FR-07`) · `FREEZE-TC-1.0.0`
**Date:** 2026-11-19

---

## 1. What was delivered

Two Django modules in the target root `Aplicacion/backend`:

| Module | Owner | Delivered |
|---|---|---|
| `modules/commerce/` | A2 | `Compra` (aggregate), the frozen money snapshot, the create-or-reuse purchase flow, the port adapters for `pagos` |
| `modules/pagos/` | A2 | `OrdenPago`, `TransaccionPago`, `RegistroIdempotencia`, the provider-attempt lifecycle, the server-side signature verification, the idempotent confirmation flow, the single owner of the operational verdict, and three frozen HTTP routes |

**95 new files** (40 in `commerce`, 55 in `pagos`), 7 232 lines including docstrings and generated migrations.
**79 behaviour tests** (15 in `commerce`, 64 in `pagos`), all green.

**No shared A0 file was edited.** `config/settings/base.py`, `config/api.py` and `core/exceptions.py` are
requested by evidence (A0-01…A0-08) and are NOT touched by this packet.

---

## 2. The three aggregates (FR-04 §1)

### 2.1 `Compra` — owner `commerce`

| Attribute | Frozen rule | Implementation |
|---|---|---|
| `id` | UUID (pk) | `core.models.BaseModel` |
| `persona_id` | FK → `Persona`, **obligatoria** | `on_delete=PROTECT`, `related_name="compras"`, `null=False` |
| `origen` | `INSCRIPCION` \| `PASE` \| `MARKETPLACE` | `OrigenCompra` (closed `TextChoices`, 3 values) |
| `estado` | `PENDIENTE` \| `PAGADA` \| `CANCELADA` | `EstadoCompra` |
| `total` | `Decimal` congelado | `DecimalField(12, 2)` + `CheckConstraint(total >= 0)` |
| `moneda` | ISO-4217 | `CharField(3)`, default `PEN` |
| `lineas_snapshot` | snapshot inmutable | `JSONField(list)` — written **once** |
| `orden_pago_id` | FK → `OrdenPago`, nullable | `OneToOneField("pagos.OrdenPago", null=True, on_delete=PROTECT, related_name="+")` |
| `referencia` | referencia de la intención | `CharField(200)` |
| timestamps | `creada_en` / `actualizada_en` | `created_at` / `updated_at` (`BaseModel`) |

**Divergence from FR-04 §1.1, declared and traceable.** The freeze lists BOTH `Compra.orden_pago_id` (FK →
`OrdenPago`) and `OrdenPago.compra_id` (FK → `Compra`). Two physical FKs between the same two tables are a
**circular migration dependency** and Django refuses to build them. The frozen backend resolved the same
problem the same way (`backend/modules/commerce/migrations/0003_remove_compra_from_ordenpago.py`): the
physical column lives on ONE side. This package keeps the literal `Compra.orden_pago_id` of FR-04 §1.1 and
materialises `OrdenPago.compra_id` as the **reverse** of that relation, which `pagos` reaches through the
port `IEstadoCompraOrdenPagoService` instead of through an import. The dependency direction stays
`commerce → pagos` and the module graph stays acyclic.

### 2.2 `OrdenPago` — owner `pagos`

`referencia` (visible, unique) · `estado` (`PENDIENTE` \| `EN_VERIFICACION` \| `CONFIRMADA` \| `FALLIDA` \|
`VENCIDA`) · `monto` (frozen `Decimal`) · `moneda` · `pagada_en` · `vence_en` · `metadata` (sanitised,
non-authoritative).

### 2.3 `TransaccionPago` — owner `pagos`

`orden_pago` (FK) · `intento` (ordinal, growing per order) · `referencia_proveedor` (technical) · `estado`
(`PENDIENTE` \| `EXITO` \| `FALLIDO` \| `CANCELADO`) · `verificada` (bool) · `evidencia` · `metadata`
(sanitised provider payload).

**Provider-attempt history.** Attempts are never deleted. Re-opening the checkout retires the live attempt
(marked `CANCELADO`) and opens a new one with its own ordinal and its own provider identity; the whole trail
stays (`RN-C04`). Two database constraints make it true:

| Constraint | Kind | Meaning |
|---|---|---|
| `transaccion_intento_unico_por_orden` | UNIQUE `(orden_pago_id, intento)` | the ordinal is unique per order |
| `transaccion_intento_vivo_unico_por_orden` | **partial** UNIQUE `(orden_pago_id) WHERE estado = 'PENDIENTE'` | at most ONE live attempt per order |
| `compra_pendiente_unica_por_comprador` | **partial** UNIQUE `(persona_id, referencia) WHERE estado = 'PENDIENTE'` | at most ONE pending purchase per intent |
| `idempotencia_clave_unica_por_ambito` | UNIQUE `(ambito, clave)` | one execution per idempotency key |
| `ordenpago_monto_no_negativo` / `compra_total_no_negativo` | CHECK | money is never negative |

### 2.4 `RegistroIdempotencia` — owner `pagos`

The idempotency key of the HTTP edge (FR-04 §2.2): `ambito` (endpoint + actor) · `clave` (opaque, ≤ 128) ·
`huella` (SHA-256 of the request — **never the payload**) · `respuesta` (the result of the first execution) ·
`codigo_estado`.

---

## 3. The money is the server's (RN-C02)

`CompraFlujo.crear_o_reutilizar_compra()` **derives** the total from the frozen lines
(`Σ cantidad × precio_aplicado`, `Decimal`, two decimals) and never takes it on faith:

- A declared total that **matches** the derived one is accepted.
- A declared total that **differs** is rejected with `COMPRA_TOTAL_INCOHERENTE` (422) — an arbitrary amount is
  never accepted, it is *refused*.

The browser never sends an amount: the amount is resolved by the origin domain against the server-side
catalogue and arrives as a snapshot. The model also refuses a negative total at the database level.

`OrdenPago.monto` / `OrdenPago.moneda` are created from the same derived total, so the order always matches
the purchase **exactly** (FR-04 §1.2).

---

## 4. Re-opening the checkout does not duplicate (I-4, I-5)

`Compra.referencia` identifies the **business intent** of a purchase (supplied by the origin domain). The
flow, before creating anything:

1. looks for a `PENDIENTE` purchase with the same `(persona, referencia)`;
2. if it exists → **reuses** it, with its SAME `compra_id` and its SAME `orden_pago_id`;
3. if it does not exist → creates the purchase and its order in ONE transaction.

The database enforces the same rule under concurrency (partial unique index), and the flow catches the
`IntegrityError` **outside** the atomic block and converges on the winner.

**Closing the modal does not cancel.** This package exposes **no** cancellation operation at all: the
purchase stays `PENDIENTE` and recoverable, and the order stays `PENDIENTE` (`RN-C03`). The cancellation /
refund policy remains OPEN (`PD-06` / `GOV-01-OPEN-06`).

**Re-opening the checkout does not create another attempt on the same order either** — it creates a new
*attempt* on the SAME order (`PagoIntentoFlujo.abrir_intento`), retiring the previous live attempt.

---

## 5. Provider trust (FR-04 §3, `RN-C05`)

Two channels, two rules, **no fallback**:

| Channel | Rule |
|---|---|
| `NOTIFICACION` (server to server, `RT-PG-02`) | The merchant key MUST be configured AND the signature MUST verify. Otherwise: `PAGO_NOTIFICACION_NO_VERIFICABLE` (400). **Nothing is mutated.** |
| `BROWSER` (SDK relay, `RT-PG-01`) | The actor MUST be authenticated and MUST own the order (`PAGO_NO_AUTORIZADO`, 403). The signature is verified whenever the key is configured: an invalid signature is always refused (`PAGO_FIRMA_INVALIDA`, 400), and a **successful** payment without a verifiable signature is refused too. Without the key the provider cannot be authenticated: the order goes to `EN_VERIFICACION` ("estamos verificando tu pago", `RN-C07`) and is **never** declared paid. |

The signature is **HMAC-SHA256 over the raw payload**, Base64-encoded, compared in constant time
(`hmac.compare_digest`). The merchant key is read from `settings.IZIPAY_KEY_HASH` **on every access** (it is
never captured in a stale instance) and it is a secret that never leaves the server.

The browser is **not** a source of trust: `FR-04` §3 forbids declaring a payment confirmed from browser
state, and the implementation refuses to do so.

---

## 6. Idempotency (FR-04 I-1, §2.2)

| Guarantee | Mechanism | Test |
|---|---|---|
| **I-1** one effective confirmation per order | signature verified **before** any mutation; `CONFIRMADA` is reached once; a repeated or late callback converges | `test_la_confirmacion_repetida_no_duplica_el_pago`, `test_la_notificacion_tardia_no_duplica_el_pago` |
| **I-4** re-opening the checkout does not create another purchase | pending purchase reused by `(persona, referencia)`; partial unique index | `test_reabrir_el_checkout_reutiliza_la_compra_pendiente`, `test_reabrir_el_checkout_no_crea_otra_orden_de_pago` |
| **I-5** closing the modal does not cancel | no cancellation operation exists; the purchase stays `PENDIENTE` | `test_cerrar_el_checkout_no_cancela_la_compra` |
| §2.2 explicit key at the HTTP edge | `Idempotency-Key` header → `RegistroIdempotencia` (ambito = endpoint + actor) | `test_la_misma_clave_con_el_mismo_payload_devuelve_el_mismo_resultado`, `test_la_misma_clave_con_otro_payload_es_un_conflicto` |
| §2.2 conflict | same key + different payload → 409 `IDEMPOTENCY_KEY_REUTILIZADA` | idem |

A repeated operation returns **the same result** with the status of the first execution. It is never a 500.

---

## 7. Operational state without activating rights (FR-01 §5, `RN-C07`, `RN-C08`)

`EstadoOperativoPagoService` is the **single owner** of the operator verdict. The vocabulary
`EstadoOperativoPago` is reproduced **without renumbering** (FR-01 §5.2): `SIN_ORDEN` · `PAGADA` ·
`PAGADA_SIN_LIQUIDAR` · `PAGADA_SIN_EVIDENCIA` · `PAGADA_SIN_FECHA` · `PENDIENTE` · `CANCELADA` · `VENCIDA`.

Precedence (first match wins): a paid order NEVER reads as cancelled or expired.

The verdict crosses the three facts in **one** place; no other surface recomputes it and the frontend never
crosses them (`contratos/01` §1.4).

**Payment confirmation and right activation are separate states.** Confirming a payment marks the `Compra` as
`PAGADA` (a commercial fact, idempotent) and enables **no** right: no cupo, no entry, no stock. That is
FND-05's job. If the commercial marking fails, the confirmed payment is **kept** and the verdict stays
`PAGADA_SIN_LIQUIDAR`: a visible, recoverable incidence — never a silent reversal of the charge (`RN-C08`).

---

## 8. Secret-redaction proof

| Proof | Where |
|---|---|
| The merchant key never appears in the evidence, the metadata or the logs | `test_la_clave_del_comercio_no_aparece_en_la_evidencia_del_pago` |
| The provider payload is sanitised before persistence: no card data, no session/auth tokens, no 3-DS material, no signature, no signed payload, no raw payload | `test_el_payload_saneado_no_conserva_datos_de_tarjeta`, `test_el_payload_saneado_no_conserva_la_firma_ni_el_payload_firmado`, `test_el_payload_saneado_recorre_las_estructuras_anidadas` |
| The idempotency registry stores a **hash**, never the request payload | `test_la_huella_no_guarda_el_payload`, `test_el_registro_de_idempotencia_no_guarda_el_payload` |
| The technical provider reference is **not** published in any public wrapper | `test_la_lectura_no_expone_la_referencia_tecnica_del_proveedor` |
| The public envelope leaks neither secrets nor traces | `test_la_respuesta_no_expone_secretos_ni_trazas` |
| `OrdenPago.metadata` accepts only an allow-list and rejects a deny-list of secret keys | `METADATA_ALLOWED_KEYS` / `METADATA_FORBIDDEN_KEYS` + `sanitizar_metadata()` |

**No secret value was read, printed, copied or committed.** The tests use a public constant
(`CLAVE_COMERCIO_PRUEBA`) that exists only inside the test process; the real `IZIPAY_KEY_HASH` was never
read. No provider credential was invented and no live integration was created.

---

## 9. Files

### 9.1 `Aplicacion/backend/modules/commerce/**` (40 files, new)

```
__init__.py  admin.py  apps.py  di.py  models.py
domain/__init__.py  domain/constants.py  domain/exceptions.py
domain/models/__init__.py  domain/models/compra.py
domain/results/__init__.py  domain/results/compra_result.py
domain/schemas/__init__.py  domain/schemas/compra_schemas.py
domain/selectors/__init__.py  domain/selectors/compra_selector.py
domain/services/core/compra_core_service.py
domain/services/flujos/compra_flujo.py
domain/services/orchestrators/compra_orchestrator.py
infrastructure/__init__.py
infrastructure/services/__init__.py
infrastructure/services/estado_compra_orden_pago.py
infrastructure/services/propietario_orden_pago.py
migrations/__init__.py  migrations/0001_initial.py
presentation/__init__.py  presentation/schemas/__init__.py
tests/__init__.py  tests/conftest.py  tests/settings_overlay.py
tests/fixtures/__init__.py  tests/fixtures/commerce_fixtures.py
tests/integration/__init__.py
tests/integration/test_compra_reutilizacion.py
tests/integration/test_compra_dinero_confiable.py
```

### 9.2 `Aplicacion/backend/modules/pagos/**` (55 files, new)

```
__init__.py  admin.py  apps.py  di.py  models.py
domain/__init__.py  domain/constants.py  domain/exceptions.py
domain/models/__init__.py  domain/models/pago.py
domain/ports/__init__.py
domain/results/__init__.py  domain/results/pago_result.py
domain/schemas/__init__.py  domain/schemas/pago_schemas.py
domain/selectors/__init__.py  domain/selectors/pago_selector.py
domain/services/core/estado_operativo_pago_service.py
domain/services/core/idempotencia_pago_service.py
domain/services/core/orden_pago_core_service.py
domain/services/core/transaccion_pago_core_service.py
domain/services/core/verificacion_pago_service.py
domain/services/flujos/pago_confirmacion_flujo.py
domain/services/flujos/pago_intento_flujo.py
domain/services/orchestrators/pagos_orchestrator.py
infrastructure/__init__.py  infrastructure/services.py
migrations/__init__.py  migrations/0001_initial.py
presentation/__init__.py  presentation/schemas/__init__.py
presentation/schemas/pago_schemas.py
presentation/presenters/__init__.py  presentation/presenters/pago_presenter.py
presentation/controllers/__init__.py  presentation/controllers/pagos_controller.py
presentation/parsers.py
tests/__init__.py  tests/conftest.py  tests/settings_overlay.py  tests/urls_pagos.py
tests/fixtures/__init__.py  tests/fixtures/pagos_fixtures.py
tests/integration/__init__.py
tests/integration/test_pago_confirmacion.py
tests/integration/test_pago_intentos.py
tests/integration/test_estado_operativo_pago.py
tests/integration/test_idempotencia_pago.py
tests/integration/test_secreto_y_redaccion.py
tests/e2e/__init__.py  tests/e2e/test_pagos_controller.py
```

### 9.3 Outside the module roots

| File | Action |
|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/evidence/foundations/FND-04-commerce-payments.md` | created (this file) |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | modified (FND-04 row + transition only) |

**No shared A0 file was edited.** `config/settings/base.py`, `config/api.py`, `core/exceptions.py`,
`core/responses.py`, `core/permissions.py`, `core/contract_versions.py`, `core/**` and every frozen root
(`backend/`, `frontend/`, `worker/`, `proxy/`, `.opencode/`), `contract/**`, `Aplicacion/plan/**` and
`Aplicacion/documentacion/**` are untouched.

---

## 10. Migrations

| App | Migration | Dependencies |
|---|---|---|
| `pagos` | `0001_initial` | `swappable_dependency(AUTH_USER_MODEL)` |
| `commerce` | `0001_initial` | `("pagos", "0001_initial")`, `("usuarios", "0002_grupos_funcionales")`, `swappable_dependency(AUTH_USER_MODEL)` |

Chain: `usuarios` → `pagos` → `commerce`. Both are reversible (verified: apply → unapply → replay).

Physical schema verified on a real SQLite file (partial UNIQUE indexes present as expected):

```
CREATE UNIQUE INDEX "compra_pendiente_unica_por_comprador"
  ON "commerce_compra" ("persona_id", "referencia") WHERE "estado" = 'PENDIENTE'
CREATE UNIQUE INDEX "transaccion_intento_vivo_unico_por_orden"
  ON "pagos_transaccionpago" ("orden_pago_id") WHERE "estado" = 'PENDIENTE'
CREATE UNIQUE INDEX "transaccion_intento_unico_por_orden"
  UNIQUE ("orden_pago_id", "intento")
CREATE UNIQUE INDEX "idempotencia_clave_unica_por_ambito" UNIQUE ("ambito", "clave")
CHECK ("compra_total_no_negativo" CHECK ("total" >= '0'))
CHECK ("ordenpago_monto_no_negativo" CHECK ("monto" >= '0'))
```

---

## 11. Routes implemented (ledger FR-07 §3.3)

| Route | Method | Presenter | Wrapper | Input | Errors |
|---|---|---|---|---|---|
| `RT-PG-01` `/pagos/ordenes/{orden_id}/confirmar` | POST | `PagoConfirmadoPresenter` | `PagoConfirmadoOut` | `ConfirmarPagoIn` + header `Idempotency-Key` | `PAGO_FIRMA_INVALIDA` 400 · `PAGO_DATOS_INCONSISTENTES` 409 · `MONTO_NO_COINCIDE` 409 · `ORDEN_YA_PAGADA_CON_IZIPAY` 409 · `PAGO_NO_AUTORIZADO` 403 |
| `RT-PG-02` `/pagos/izipay/notificacion` | POST | `PagoNotificacionPresenter` | `PagoConfirmadoOut` | raw signed payload + signature | `PAGO_FIRMA_INVALIDA` 400 · `PAGO_NOTIFICACION_NO_VERIFICABLE` 400 |
| `RT-PG-03` `/pagos/ordenes/{orden_id}` | GET | `OrdenPagoPresenter` | `OrdenPagoOut` | — | `ORDEN_PAGO_NO_ENCONTRADA` 404 · `PAGO_NO_AUTORIZADO` 403 |

`RT-PG-04` and `RT-PG-05` belong to the `administracion` module (owner A0 + A7 / A0) and are **out of this
packet's scope**.

`SCHEMA_VERSION = "1.0.0"` in both `modules/pagos/presentation/schemas/__init__.py` and
`modules/commerce/presentation/schemas/__init__.py`, matching
`core.contract_versions.SCHEMA_VERSIONS["pagos"]` / `["commerce"]`.

`commerce` has **no HTTP surface**: the ledger assigns it none, and each origin domain creates its own
purchase through its own endpoint (`RN-C01`, `DEC-10`).

**No route was registered in `config/api.py`** — registration is A0's (A0-03).

---

## 12. Commands and results

Workdir `Aplicacion/backend`. Interpreter `.\.venv\Scripts\python.exe` (Python 3.10.0, Django 5.2.11,
pytest-django 4.9.0, ninja 1.5.3, ninja-extra 0.31.0, injector 0.24.0).

**Exact environment for the package suites** (A0 registration pending → isolated settings overlay):

```powershell
$env:DJANGO_SETTINGS_MODULE = "modules.pagos.tests.settings_overlay"
```

The overlay registers `modules.usuarios` + `modules.commerce` + `modules.pagos`,
`AUTH_USER_MODEL = "usuarios.Usuario"` and the three DI modules. It is the single overlay for both suites
(`modules/commerce/tests/settings_overlay.py` re-exports it).

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `python -m pytest modules/commerce/tests modules/pagos/tests -q` (overlay) | **0** | **79 passed** (15 commerce + 64 pagos) |
| V2 | `python -m pytest modules/pagos/tests -q` (overlay) | **0** | **64 passed** |
| V3 | `python -m pytest modules/commerce/tests -q` (overlay) | **0** | **15 passed** |
| V4 | `python manage.py check --settings=modules.pagos.tests.settings_overlay` | **0** | `System check identified no issues (0 silenced)` |
| V5 | `python manage.py makemigrations --check --dry-run --settings=modules.pagos.tests.settings_overlay` | **0** | `No changes detected` — `0001_initial` matches the models exactly |
| V6 | `python manage.py check` (default settings) | **1** | `DB_NAME` — **identical to the FND-01/FND-02/FND-03 baseline** (environmental) |
| V7 | `python manage.py makemigrations --check --dry-run` (default settings) | **1** | same `DB_NAME` — identical baseline |
| V8 | `python manage.py check --settings=config.settings.development` | **0** | `no issues` |
| V9 | `python manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| V10 | `python manage.py migrate --settings=…overlay` (file SQLite) | **0** | `Applying pagos.0001_initial... OK` · `Applying commerce.0001_initial... OK` |
| V11 | `python manage.py migrate --settings=…overlay` (repeat) | **0** | idempotent — no output, exit 0 |
| V12 | `python manage.py showmigrations pagos commerce --settings=…overlay` | **0** | `[X] 0001_initial` on both apps |
| V13 | `python manage.py migrate commerce zero --settings=…overlay` | **0** | `Unapplying commerce.0001_initial... OK` — reversible |
| V14 | `python manage.py migrate pagos zero --settings=…overlay` | **0** | `Unapplying pagos.0001_initial... OK` — reversible |
| V15 | `python manage.py migrate --settings=…overlay` (replay) | **0** | `Applying pagos.0001_initial... OK` · `Applying commerce.0001_initial... OK` — second replay |
| V16 | SQLite schema inspection of the 4 tables | **0** | the 3 partial/unique indexes and the 2 CHECK constraints are present (see §10) |
| V17 | `python -m pytest core/tests -q` (default settings) | **0** | **89 passed** — FND-01 baseline intact |
| V18 | `python -m pytest modules/eventos/tests -q` (FND-02 overlay) | **0** | **63 passed** — FND-02 baseline intact |
| V19 | `python -m pytest modules/usuarios/tests -q` (FND-03 overlay) | **0** | **35 passed, 1 skipped** — FND-03 baseline intact |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **empty** |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | **empty** — frozen roots untouched |
| R3 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — unchanged, **no commit created** |
| R4 | `git stash` | — | **never invoked** |

**Byproduct removed:** `manage.py check --settings=config.settings.development` creates a 0-byte
`Aplicacion/backend/db.sqlite3` (FND-01 F-2); it was deleted after the verification runs.

**Stability:** the package suite was executed **5 consecutive times** after the last fix: `79 passed` on
every run.

**Known baseline failures:** unchanged — the two default-settings `manage.py` gates (V6/V7) remain
environmental and identical to FND-01/FND-02/FND-03.
**New (not a defect):** the two packages cannot be imported until A0 registers the apps in
`INSTALLED_APPS` (A0-02); with the local verification overlay everything passes.

---

## 13. A0 requests (shared files NOT edited by this packet)

| ID | Request |
|---|---|
| **A0-01** | Register the apps and the DI modules in `config/settings/base.py`: `INSTALLED_APPS += ["modules.commerce", "modules.pagos"]` and `NINJA_EXTRA["INJECTOR_MODULES"] += ["modules.commerce.di.CommerceModule", "modules.pagos.di.PagosModule"]`. The `usuarios` registration (FND-03 A0-01) is a prerequisite: `Compra.persona` is a FK to `usuarios.Persona`. |
| **A0-02** | Apply the migrations in the order `usuarios` → `pagos` → `commerce` **before** the first migration of the target. |
| **A0-03** | Register the controller: `registrar_controladores(PagosController)` in `config/api.py`. Until then the three routes are intentionally dead code (`FR-07` §3.1 rule 2). |
| **A0-04** | Extend `core/exceptions.py::PUBLIC_ERROR_MESSAGES` with the new codes: `IDEMPOTENCY_KEY_REUTILIZADA`, `IDEMPOTENCY_KEY_INVALIDA`, `ORDEN_PAGO_NO_PAGABLE`, `COMPRA_TOTAL_INCOHERENTE`, `COMPRA_REFERENCIA_INVALIDA`, `COMPRA_NO_ENCONTRADA`. All six already travel in `error.code`; only their public prose is missing (FND-03 F-21). |
| **A0-05** | Confirm the HTTP status of the new codes: 400 for `PAGO_FIRMA_INVALIDA` and `PAGO_NOTIFICACION_NO_VERIFICABLE` (the ledger's status, **not** the 409 of the frozen backend), 409 for the idempotency conflicts, 422 for `COMPRA_TOTAL_INCOHERENTE`. |
| **A0-06** | `*.sqlite3` in the target `.gitignore` (every `manage.py check --settings=config.settings.development` leaves a 0-byte `db.sqlite3`). |
| **A0-07** | Sync the physical task matrix `00-matriz-tareas.md` (rows `T-013`, `T-014`). |
| **A0-08** | Decide whether `IZIPAY_KEY_HASH` must be present in the target `.env` **before** the release. Without it the provider cannot be authenticated: the server-to-server notification fails closed and the browser relay can only leave the order in `EN_VERIFICACION` (`RN-C05`). The key is never read, printed or copied by this packet. |

---

## 14. Rollback

1. `python manage.py migrate commerce zero --settings=modules.pagos.tests.settings_overlay`
2. `python manage.py migrate pagos zero --settings=modules.pagos.tests.settings_overlay`
3. delete `Aplicacion/backend/modules/commerce/**` and `Aplicacion/backend/modules/pagos/**`
4. remove the A0 registrations of A0-01/A0-03 (if they were applied)
5. restore `STATE.md` and this file

**Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` — this packet created **NO commit**; do NOT
revert `f3df540`.

The rollback is safe **before** the right-activation consumers (FND-05, DOM-01/03/05) proceed: those packets
depend on `Compra`/`OrdenPago` and must not start before this one is accepted.

---

## 15. Open decisions carried forward

Unchanged: `PD-01`…`PD-10` · `GOV-01-OPEN-01`…`13` · GAP-1…GAP-4 · D-A…D-E · `GOV-02-UX-01`…`05` ·
`GOV-02-SH-01`…`08` · `GOV-02-BL-01`…`12` · `GOV-02-CM-01`…`05` · `P-01`…`P-12` · `GOV-01-OPEN-09` ·
`GOV-01-OPEN-10` · `NEW-FND03-01`…`04` · `D-FND-02-01`…`09`.

New from this packet:

| ID | Pending | Owner |
|---|---|---|
| `D-FND-04-01` | The **reference of the purchase intent** (`Compra.referencia`) is supplied by the origin domain. Its format (`INSCRIPCION:{id}:INICIAL`, `PASE:{id}:{n}`, …) is not frozen: the shape must be agreed before DOM-01/03/05 create purchases, or the same intent could be opened twice under two different references. | A2 + A3 + A4 + A5 |
| `D-FND-04-02` | The **provider order reference** that the provider echoes (`orderNumber`) is accepted if it matches EITHER `OrdenPago.referencia` OR `TransaccionPago.referencia_proveedor`. The concrete provider contract must confirm which one it uses. | A2 + A0 |
| `D-FND-04-03` | The **manual approval** channel (`OrigenPago.MANUAL`, `RT-PG-05`, `AprobacionPagoManual`) is NOT implemented: `RT-PG-05` belongs to the `administracion` module (owner A0). The verdict vocabulary already reserves `MANUAL`. | A0 |
| `D-FND-04-04` | Opening a **provider session** (the live `Token/Generate` call) is NOT implemented: it needs deployment credentials and a live integration, which are outside FND-04. The typed boundary is `IProveedorPagoService`; the attempt can be created and confirmed without it. | A2 + A0 |
| `D-FND-04-05` | The **activation incidence** (a visible, recoverable record of a payment confirmed whose right was not enabled) is FND-05's (`RN-C08`); FND-04 only guarantees that the verdict stays `PAGADA_SIN_LIQUIDAR` while it lasts. | A0 (FND-05) |
| `D-FND-04-06` | `Compra` has **no HTTP surface**: the domains create their purchases in-process through `CompraOrchestrator`. Whether the domains should call the orchestrator or a shared HTTP route is not ratified (`RT-CM-01`…`RT-CM-03` are per-domain). | A2 + A3 + A4 + A5 |

---

## 16. Consumers unblocked

**DOM-01 / DOM-03 / DOM-05** (`Compra` + `CompraOrchestrator` + the frozen snapshot, `RT-CM-01`…`RT-CM-03`
per domain) · **DOM-02 / DOM-06** (the purchase is paid before the right is granted) · **FND-05**
(`Compra.estado = PAGADA` is idempotent, the verdict exists, the payment is durable before any activation)
· **XCT-03** (payment reconciliation: the three states are separated and the incidence is visible) ·
**API-04** (`estado_operativo` is published by the backend, `RT-PG-04` belongs to A0 + A7) ·
**API-03** (the commercial wrappers) · **VER-01…VER-03**.

**Still blocked on A0:** any consumer that needs the three routes served by the project API.

---

## 17. Next packet

**FND-05** — *Coordinate Exactly-Once Rights Activation* (`wave-01-foundations/FND-05-rights-activation.md`,
`T-015`). It builds the coordinator that turns a verified payment into one
recoverable, idempotent domain activation, with the activation key/status/incidence
(`RN-C08`). Its allowed roots include `Aplicacion/backend/modules/commerce/**` and
`pagos/**`: **this packet's files are the ground it builds on and must not be
rewritten** — the coordinator adds `ActivacionCompra` (or equivalent) and the
origin-dispatched activation interface, and reuses `Compra.estado`, the
`IEstadoCompraOrdenPagoService` port and `EstadoOperativoPagoService`.
