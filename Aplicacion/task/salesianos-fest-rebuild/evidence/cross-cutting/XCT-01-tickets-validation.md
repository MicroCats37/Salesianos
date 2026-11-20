# XCT-01 — Ticket preview and atomic validation (shared credential console)

**Packet:** `XCT-01` · **Original tasks:** `T-080`, `T-081` · **Owner:** A8 + A4 + A5
**Change:** `salesianos-fest-rebuild` · **Freeze:** `FREEZE-RT-1.0.0` (`FR-05`)
**Mode:** apply · **Artifact store:** engram + physical evidence

---

## 1. What this packet delivered

The module `validaciones` **did not exist** in the target when this packet
started (`evidence/ui/UI-05-competition-validation-shells.md` and
`evidence/api/API-05-competition-admin-integration.md` both record it as
missing). The packet OWNS that module (`Aplicacion/backend/modules/validaciones/**`
is in its allowed edit roots), so it was implemented **exactly** — no route,
payload or business rule was invented outside the frozen contracts.

The delivered surface is:

| Piece | Where | What it does |
|---|---|---|
| `Ticket` | `modules/validaciones/domain/models/ticket.py` | The CREDENTIAL: a reference to a right that already exists in its owner module. It never duplicates it (`FR-05` §1) |
| `ValidacionTicket` | same file | The ACTA of every attempt: actor, instant, operation, quantity, result, reason, idempotency key |
| `IVerificadorDerecho` | `modules/validaciones/domain/ports/verificador_derecho.py` | The frozen `VerificarDerecho` interface (`FR-05` §5): the consumer declares it, the owners implement it |
| `PaseVerificadorDerecho` | `modules/salesianos_fest/domain/services/core/verificador_derecho_pase.py` | The owner adapter of the RIGHTS OF ENTRY (`PaseBeneficiario`) |
| `PedidoVerificadorDerecho` | `modules/marketplace/domain/services/core/verificador_derecho_pedido.py` | The owner adapter of the DELIVERIES (a paid `Pedido`) |
| `RegistroVerificadoresDerecho` | `modules/validaciones/infrastructure/services.py` | The directory: one owner per `tipo_derecho` |
| `PreviewTicketFlujo` | `modules/validaciones/domain/services/flujos/preview_ticket_flujo.py` | The READ-ONLY check (`FR-05` §2.1, `RN-P06`) |
| `ConfirmarTicketFlujo` | `modules/validaciones/domain/services/flujos/confirmar_ticket_flujo.py` | The ATOMIC, IDEMPOTENT exchange (`FR-05` §2.2) |
| `ValidacionController` | `modules/validaciones/presentation/controllers/validacion_controller.py` | `RT-RT-01` and `RT-RT-02` |

**ONE RIGHT LIFECYCLE.** The consumption counter lives on the RIGHT
(`PaseBeneficiario.cantidad_consumida`), not on the credential. The
credential only points at it. `validaciones` never grants, never modifies and
never re-implements a right: it asks the owner (`FR-05` §1).

**TWO OPERATIONS, ONE INFRASTRUCTURE.** The ENTRY and the DELIVERY share the
credential, the ports, the audit and the envelopes. They do NOT share the
decision: the entry is resolved by `salesianos_fest` and the delivery by
`marketplace`. The frontend keeps two SCREENS (`ADM-16` and `ADM-20`) and two
containers.

**NEUTRAL DENIALS.** The owner publishes `puede_canjear`, `motivo_codigo` and
`motivo_mensaje`. The browser never decides that a credential can be redeemed:
the container only offers the confirmation when the SERVER said so.

---

## 2. Contracts and evidence read

| Source | What it fixed |
|---|---|
| `contract/django-app-architecture-contract.md` | The module layout, the async chain, the sync core service, `transaction.atomic` in the flow, the presenter rule, the test client |
| `contract/api-wrapper-presenter-contract.md` | The wrapper shape, the 3-block composition, the public error catalog, the fixed success message |
| `contract/SCHEMA_DRY_INTENTION.md` | The composition of the wrappers (no monolithic schema) |
| `contract/TEST_ARCHITECTURE_CONTRACT.md` | The test layout (`fixtures/`, `integration/`, `e2e/`), no mocks, the factories rule |
| `contract/next-app-architecture-contract.md` | The frontend layers, the TanStack Query use, the barrel rules, the import order |
| `contract/smart.md` | The Zod-owns-validation rule and the dumb-UI rule |
| `evidence/contracts/FR-05-rights-lifecycle.md` | The three operations, the three frozen shapes, the `VerificarDerecho` interface |
| `evidence/contracts/FR-07-presenter-schema-versions.md` | The ledger of routes, presenters and wrappers, and the `SCHEMA_VERSION` registry |
| `evidence/contracts/route-to-wrapper-ledger.csv` | `RT-RT-01` and `RT-RT-02`: paths, wrappers, error codes and statuses |
| `evidence/domains/DOM-03-passes-beneficios-cortesia.md` | `PaseBeneficiario`, `cantidad_consumida`, the revocation lifecycle, and the explicit statement that the canje is XCT-01's |
| `evidence/domains/DOM-06-inventory-reservation-delivery.md` | The delivery contract, `RT-MK-11`, the acta and the `PD-03` question |
| `evidence/domains/DOM-03-05-07-08-runtime-verification.md` | The runtime truth of the owners at the moment of the packet |
| `evidence/ui/UI-05-competition-validation-shells.md` | The two screens, the manual code fallback and the honest "not connected" state |
| `evidence/api/API-05-competition-admin-integration.md` | The reconciled evidence of the validation area and its open requests |
| `evidence/api/API-03-commercial-integration.md` | The commercial owners' interfaces |
| `evidence/baseline/BL-04-failure-classification.md` | The known baseline failures that are NOT regressions |
| `Aplicacion/plan/salesianos-fest-rebuild/funcional/04-flujos-end-to-end.md` | `FL-10`, step by step |
| `Aplicacion/plan/salesianos-fest-rebuild/funcional/01-modulos-y-responsabilidades.md` | The responsibility of `validaciones` and the `VerificarDerecho` table |
| `Aplicacion/plan/salesianos-fest-rebuild/funcional/02-reglas-de-negocio.md` | `RN-P06`, `RN-P07`, `RN-P08` |
| `Aplicacion/plan/salesianos-fest-rebuild/funcional/03-modelo-de-datos.md` | The `Ticket` and `ValidacionTicket` entities |
| `Aplicacion/plan/salesianos-fest-rebuild/implementacion/03-pruebas-y-aceptacion.md` | `QA-V01` and `QA-V02` |

---

## 3. The ledger of adapters, presenters and schemas

### 3.1 The adapters (the owners of the rules)

| Adapter | Owner module | `tipo_derecho` | Rules it owns |
|---|---|---|---|
| `PaseVerificadorDerecho` | `salesianos_fest` | `PASE`, `ENTRADA_CORTESIA` | A revoked right is not redeemable (`RN-P08`); a `PENDIENTE` purchase enables nothing (`RN-P02`); no more units than granted (`RN-P07`); the revocation is permanent (`FR-05` §2.3) |
| `PedidoVerificadorDerecho` | `marketplace` | `PRODUCTO` | Paid and delivered are DIFFERENT states (`RN-M07`); a cancelled order is not delivered; the delivery is idempotent (`DOM-06`); the partial delivery is not ratified (`PD-03` OPEN) |

Neither adapter re-implements a rule of the other module, and `validaciones`
never reads a right table directly.

### 3.2 The presenters and the wrappers

| Route | Presenter | Wrapper | Input | Errors |
|---|---|---|---|---|
| `RT-RT-01` `POST /validaciones/preview` | `TicketPreviewPresenter` | `TicketPreviewOut` | `PreviewTicketIn` | `TICKET_NO_ENCONTRADO` (404) · `ACTION_NOT_ALLOWED` (403) |
| `RT-RT-02` `POST /validaciones/confirmar` | `TicketConfirmPresenter` | `TicketConfirmadoOut` | `ConfirmarTicketIn` (with `idempotency_key`) | `TICKET_YA_CONSUMIDO` · `CANTIDAD_EXCEDIDA` · `DERECHO_REVOCADO` · `IDEMPOTENCY_KEY_REUTILIZADA` (409) |

The wrappers reproduce the FROZEN shapes of `FR-05` §3.1 and §3.2 field by
field. They are composed with the three blocks of
`contract/SCHEMA_DRY_INTENTION.md`:

- `TicketPreviewOut` = `TicketGeneralOut` (`edicion_id`) + `TicketEspecificoOut`
  (`tipo_derecho`, `codigo`, `estado`, the three quantities, `puede_canjear`,
  `motivo_codigo`, `motivo_mensaje`) + `TicketTitularOut` (`persona_id`,
  `nombre`).
- `TicketConfirmadoOut` = `TicketIdentidadOut` (`validacion_id`,
  `consumido_en`) + the specific block + `TicketActorOut` (`usuario_id`,
  `persona_id`).

`SCHEMA_VERSION = "1.0.0"` is declared by the module
(`modules/validaciones/presentation/schemas/__init__.py`) and by the frontend
mirror (`features/validaciones/schemas/validacion.schema.ts`). The global
registry `core/contract_versions.py` ALREADY froze `validaciones` in `1.0.0`:
**no A0 edit is needed for the version**.

### 3.3 The ownership of each concern

| Concern | Owner | Where |
|---|---|---|
| HTTP envelope | `core/responses.py` (A0) | `success_response` |
| Public error prose | `core/exceptions.py` (A0) | `PUBLIC_ERROR_MESSAGES` |
| Capability of the operator | `core/permissions.py` (A0) | `RequireAcreditacionesEscribir` |
| The credential | `modules/validaciones` | `Ticket` |
| The audit | `modules/validaciones` | `ValidacionTicket` |
| The rules of the entry | `modules/salesianos_fest` | `PaseVerificadorDerecho` |
| The rules of the delivery | `modules/marketplace` | `PedidoVerificadorDerecho` |
| The idempotency of the exchange | `modules/validaciones` | `ValidacionCoreService` |
| The HTTP client (frontend) | `src/lib/api.ts` (A0) | `apiSend` |
| The Zod mirror (frontend) | `features/validaciones/schemas` | `ticketPreviewSchema`, `ticketConfirmadoSchema` |
| The query keys / cache | — | **NONE**: the check and the exchange are MUTATIONS. The credential is a secret and a cache would keep it in memory and could publish it in a later request |
| The payload builder | `features/validaciones/services/validacion.service.ts` | `previewTicketSchema.parse`, `confirmarTicketSchema.parse` |

---

## 4. Files and migrations

### 4.1 Created — backend (52 files)

`Aplicacion/backend/modules/validaciones/`: `__init__.py`, `apps.py`,
`models.py`, `di.py`, `admin.py`, `domain/{constants,exceptions}.py`,
`domain/models/{__init__,ticket}.py`, `domain/ports/{__init__,verificador_derecho}.py`,
`domain/results/{__init__,validacion_results}.py`,
`domain/schemas/{__init__,validacion_schemas}.py`,
`domain/selectors/{__init__,ticket_selector}.py`,
`domain/services/core/validacion_core_service.py`,
`domain/services/flujos/{preview_ticket_flujo,confirmar_ticket_flujo}.py`,
`domain/services/orchestrators/validacion_orchestrator.py`,
`infrastructure/services.py`, `migrations/0001_initial.py`,
`presentation/schemas/validacion_schemas.py`,
`presentation/presenters/ticket_presenter.py`,
`presentation/controllers/validacion_controller.py`,
`management/commands/emitir_ticket.py`, `tests/**` (8 files).

### 4.2 Created — owner adapters (2 files, narrow)

- `Aplicacion/backend/modules/salesianos_fest/domain/services/core/verificador_derecho_pase.py`
- `Aplicacion/backend/modules/marketplace/domain/services/core/verificador_derecho_pedido.py`

No existing file of `salesianos_fest` or `marketplace` was modified: the
adapters are NEW files that only read their own models and call their own
core services.

### 4.3 Created — frontend (8 files)

`features/validaciones/services/{validacion.service.ts,index.ts}`,
`features/validaciones/hooks/{useValidacion.ts,index.ts}`,
`features/validaciones/utils/validaciones.preview.utils.ts`,
`features/validaciones/views/{ValidarPaseRuta.tsx,ValidarEntregaRuta.tsx}`,
`features/validaciones/__tests__/validacion-contrato.test.ts`.

### 4.4 Modified — frontend (4 files)

- `features/validaciones/schemas/validacion.schema.ts` — the real mirrors.
- `features/validaciones/views/index.ts` — the new containers.
- `app/(administracion)/administracion/pases/validar/page.tsx` — the container.
- `app/(administracion)/administracion/marketplace/entregas/page.tsx` — the container.

### 4.5 The migration

`modules/validaciones/migrations/0001_initial.py` creates `validaciones_ticket`
and `validaciones_acta`, with three CHECK constraints that are the AUTHORITY
of the rules:

| Constraint | Rule |
|---|---|
| `validaciones_ticket_referencia_coherente` | The credential points to ONE right and the operation is derived from the type of the right |
| `validaciones_acta_actor_obligatorio` | A validation without an actor is not auditable (`RN-P07`) |
| `validaciones_acta_cantidad_coherente` | A permission consumes units and a refusal consumes NONE |

---

## 5. The behaviour that was implemented

### 5.1 The preview never consumes

`PreviewTicketFlujo` opens NO transaction and writes NOTHING. The test
`test_la_vista_previa_no_escribe_nada` asserts that neither the right nor the
audit changes after a check (`RN-P06`).

### 5.2 The confirmation revalidates under a lock

`ConfirmarTicketFlujo` opens ONE transaction that contains:

1. the idempotency lookup (the act of the key, if it exists);
2. the read of the credential WITH `select_for_update`;
3. the revalidation and the consumption in the OWNER, under ITS OWN row lock;
4. the act of the audit.

The owner is asked again at the moment of the confirmation: the preview is
never trusted (`FR-05` §2.2).

### 5.3 The idempotency

The key identifies ONE intention. The act stores the `huella` of the intent
(the digest of the code and the quantity):

- the SAME key with the SAME intent → the FIRST execution is returned with
  `repetido = true` and NOTHING is consumed twice (`FR-04` §2.2);
- the SAME key with ANOTHER intent → `IDEMPOTENCY_KEY_REUTILIZADA` (409);
- a denial is also remembered under its key: repeating a REFUSED exchange is
  the SAME refusal, and the refusal stays in the history (`RN-P07`).

### 5.4 The audit keeps the failures

A refusal is written in the SAME transaction that produced it and the error is
raised AFTER, so the attempt survives the rollback of the consumption. The act
records the actor, the instant, the operation, the quantity, the result and
the SAFE reason (`motivo_codigo` + `motivo_mensaje`).

### 5.5 The concurrency

Two operators that confirm the SAME credential at the same time serialize on
the lock of the owner's row: only the authorised quantity is consumed, and
only ONE act is permitted (`QA-V02`). A second confirmation with ANOTHER key
against an already consumed credential is REFUSED and audited (`QA-V01`).

---

## 6. The tests that were written

**Backend** (`modules/validaciones/tests/`), WRITTEN but NOT EXECUTED (see §7):

| File | Cases |
|---|---|
| `integration/test_validacion_ticket.py` | The preview writes nothing · an unknown credential is 404 · a revoked credential is not redeemable · the exchange consumes and audits · the repetition with the same key returns the same act · the second use with another key is refused AND audited · a reused key with another load is refused · a revoked right is refused · an excessive quantity is refused |
| `integration/test_concurrencia_validacion.py` | Two simultaneous scans consume ONCE (`QA-V02`) |
| `integration/test_entrega_validacion.py` | The delivery consumes the order and leaves its acta · the partial delivery is refused · a non-paid order is refused |
| `e2e/test_e2e_validacion.py` | 401 without a session · 403 without the capability · the frozen envelope of the preview · the credential does NOT come back in the response · 404 for an unknown code · the exchange leaves the act · the repetition returns the same act · 409 for a second exchange with another key |

**Frontend** (`features/validaciones/__tests__/validacion-contrato.test.ts`),
WRITTEN but NOT EXECUTED: the mirror accepts the frozen shape of the preview
and of the exchange, rejects a preview without its holder and an exchange
without its instant, and declares the frozen `SCHEMA_VERSION`.

---

## 7. Commands and their exit codes

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| V1 | `python -c "ast.parse(...)"` over the 54 new/changed Python files | `Aplicacion/backend` | **0** | `AST OK 54` — every new file parses (re-run at the CLOSE of the packet, after the tests were added) |
| V2 | `python manage.py makemigrations --check --dry-run --settings=modules.validaciones.tests.settings_overlay` | `Aplicacion/backend` | **0** | `No changes detected` — the hand-written migration matches the models exactly |
| V3 | `python manage.py check --settings=modules.validaciones.tests.settings_overlay` | `Aplicacion/backend` | **0** | `System check identified no issues (0 silenced)` |
| V4 | `python -c "django.setup(); import modules.validaciones.tests.conftest; RegistroVerificadoresDerecho()"` | `Aplicacion/backend` | **0** | `IMPORTS OK` — the conftest, the fixtures and BOTH owner adapters import |
| V5 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | The project-wide type gate is GREEN (no errors) |

**V2 was run TWICE.** The first run reported drift: the hand-written
migration had the wrong `to=` for the self-reference and the wrong order and
shape of the `Q` children of the constraints. The drift was CORRECTED (the
migration now reproduces exactly what Django generates) and the second run
reported `No changes detected`. The intermediate `0002_*.py` that Django
generated during the diagnosis was DELETED: it is not part of the packet.

### 7.1 Verification that was DEFERRED (and why)

The standing apply restriction of this run forbids executing `pytest`,
`vitest`, `next build`, Biome, the server and the browser. Therefore:

| Deferred | Command | Why it matters |
|---|---|---|
| Backend suite | `python -m pytest modules/validaciones/tests -q` | The 13 behaviour cases, the concurrency case and the 7 e2e cases are WRITTEN but NOT EXECUTED. **No test result is claimed.** |
| Frontend suite | `npx vitest run src/features/validaciones src/app` | The contract mirror suite is WRITTEN but NOT EXECUTED |
| Lint | `npx biome check src/features/validaciones src/app` | NOT RUN |
| Responsive / a11y | The five widths `360`, `390`, `768`, `1024`, `1440` | NOT RUN — the audit is still OPEN for this area |
| Migrations on a real DB | `migrate` / `migrate validaciones zero` / replay | NOT RUN — the overlay supports it with `VALIDACIONES_SQLITE_PATH` |

**KNOWN RISK.** The concurrency case (`test_dos_escaneos_simultaneos_consumen_una_sola_vez`)
asserts the invariant of `QA-V02` against SQLite. `select_for_update` is a
NO-OP in SQLite, so the serialization there comes from the write lock of the
database, not from the row lock. The test is written against the SPEC, and
`VER-01` has to run it on a database with real row locks before the packet
can be signed off.

### 7.2 The baseline

No baseline failure was touched. The 13 known backend failures and the
documented frontend reds of `BL-04` belong to other packages and were NOT
re-run (the whole suite is deferred). No regression was introduced in the
roots of this packet: `npx tsc --noEmit` is GREEN project-wide.

---

## 8. The requests to A0

The shared files are A0's (`00-contrato-global-de-apply.md`, "Shared Files")
and this packet did NOT edit them. These are the requests:

| Id | What A0 has to do | Why |
|---|---|---|
| **A0-XCT01-01** | Add `"modules.validaciones"` to `INSTALLED_APPS` (`config/settings/base.py`) | The app does not exist for the runtime: the tables and the models are not loaded |
| **A0-XCT01-02** | Add `"modules.validaciones.di.ValidacionesModule"` to `NINJA_EXTRA["INJECTOR_MODULES"]` | The controller resolves its orchestrator through the injector |
| **A0-XCT01-03** | Register `ValidacionController` in `config/api.py` (`registrar_controladores(...)`) | **Until this happens, `RT-RT-01` and `RT-RT-02` DO NOT EXIST**: a route that is not registered is dead code (`FR-07` §3.1). The frontend container calls them, so it will answer `404` until the registration happens |
| **A0-XCT01-04** | Add FOUR public messages to `PUBLIC_ERROR_MESSAGES` (`core/exceptions.py`) | `TICKET_NO_ENCONTRADO` (404), `TICKET_YA_CONSUMIDO` (409), `CANTIDAD_EXCEDIDA` (409), `DERECHO_REVOCADO` (409). **While they are missing, the answer uses the GENERIC message of the status** — safe, but not specific. The proposed prose: "No se encontró la credencial indicada." · "Esta credencial ya se canjeó." · "La cantidad solicitada no se puede confirmar." · "El derecho no está vigente para esta operación." |
| **A0-XCT01-05** | Decide the EMISSION of the credential | The credential is emitted by the `emitir_ticket` command of this package. Automating it at the moment the right is granted would touch the flows of `salesianos_fest` and `marketplace`, which are FORBIDDEN roots for this packet |
| **A0-XCT01-06** | Ratify `PD-03` (partial delivery) and `PD-04` (the scope of an entry) | Both stay OPEN. The package implements the CONSERVATIVE reading: the delivery consumes the whole order and the entry consumes the units that were granted |
| **A0-XCT01-07** | Decide the group of the validation operators (`GOV-01-OPEN-04`) | The package uses the existing capability `admin.acreditaciones.escribir`. No parallel permission system was invented (`core/capacidades.py` is the single map) |

**The honest state of the area:** the module exists, it is verified statically
and it has its tests, but **its two routes do not exist at runtime** until
`A0-XCT01-03` is applied. The frontend containers already call them and will
show the error state until then. This is the same situation as `DOM-05`,
`DOM-06`, `DOM-07` and `DOM-08`.

---

## 9. Deviations and decisions

| Id | Decision | Why |
|---|---|---|
| `D-XCT01-01` | The `Ticket` MODEL exists in `validaciones` and REFERENCES the right with two nullable foreign keys (`pase_beneficiario`, `pedido`) | `funcional/03` lists `Ticket` as an entity OF the module, and `FR-05` §1 forbids the ticket to DUPLICATE the right. A reference is not a duplication. The CHECK constraint makes the two cases exclusive |
| `D-XCT01-02` | The consumption counter lives on the RIGHT, not on the credential | One right lifecycle (`RN-P07`). `DOM-03` declared `cantidad_consumida` for exactly this: "la escribe el módulo que valida (`XCT-01`)" |
| `D-XCT01-03` | The port `IVerificadorDerecho` lives in `validaciones/domain/ports` and the OWNERS import it | The inversion of dependencies: the consumer declares the contract it needs. The alternative (a shared port in `core/`) would have touched an A0 root |
| `D-XCT01-04` | The delivery consumes the WHOLE order and a partial delivery is refused | `PD-03` is OPEN and `marketplace` has no counter of delivered units. Supporting a partial delivery would have meant inventing one: a business rule that is not ratified |
| `D-XCT01-05` | `cantidad` is optional in `ConfirmarTicketIn` and `None` means "everything available" | `FR-05` §2.2 forbids a PARTIAL consumption that the operator did not ask for. `None` is the explicit "all", and a number is the explicit "this many" |
| `D-XCT01-06` | The credential has its own state (`VIGENTE` / `REVOCADO`) and the revoked credential is refused with `DERECHO_REVOCADO` | The frozen code set has no "credential revoked" code. The state of the RIGHT is the owner's; the state of the CREDENTIAL is this module's own, and the preview publishes it as `CREDENCIAL_REVOCADA` |
| `D-XCT01-07` | The frontend keeps the PROVISIONAL view models of `UI-05` and adapts the frozen wire into them | The components of `UI-05` were reviewed and are not rewritten. The adapter (`utils/validaciones.preview.utils.ts`) only renames fields and picks the bucket that paints a verdict: it decides NOTHING |
| `D-XCT01-08` | The point of control and the operator of the PREVIEW come from the device, not from the server | The frozen preview does not publish them. They are labelled as the CONTEXT of the device and they are never presented as a fact of the credential |
| `D-XCT01-09` | The check and the exchange are MUTATIONS, not queries | The credential is a secret. A cache would keep it in memory and could publish it in a later request (`salesianos-api-data`: one dataset, one owner) |
| `D-XCT01-10` | The `Ticket` and the `ValidacionTicket` are READ-ONLY in the Django admin | An act is a fact: it is registered, not edited (`contract/django-app-architecture-contract.md` §10) |

### 9.1 What was NOT touched

No frozen root (`contract/**`, `Aplicacion/plan/**`, `Aplicacion/documentacion/**`),
no source reference tree (`backend/**`, `frontend/**`, `worker/**`, `proxy/**`),
no skill, no agent, no shared configuration, no secret and no database was
read-modified. No git operation of any kind was performed: **no commit, no
stash, no reset**. The only shared file that this packet TOUCHED is its own
evidence and the `STATE.md` of the plan.

---

## 10. The rollback

The rollback of this packet is a revert of ITS work unit:

1. delete `Aplicacion/backend/modules/validaciones/**`;
2. delete the two owner adapters
   (`modules/salesianos_fest/domain/services/core/verificador_derecho_pase.py`
   and `modules/marketplace/domain/services/core/verificador_derecho_pedido.py`);
3. revert the five frontend files of §4.4 and delete the seven of §4.3;
4. revert `STATE.md` and this evidence file;
5. restore the Engram observations `sdd/salesianos-fest-rebuild/apply-progress`
   and `sdd/salesianos-fest-rebuild/state`.

**The history of the validations is NEVER deleted in a live rollback.** The
acts are facts: `RN-P08` keeps the consumptions that already happened. A
rollback of the CODE does not undo a consumption that the database already
recorded.

**The migration is reversible:** `migrate validaciones zero` removes the two
tables. It must be run ONLY before the area is in production use, because it
drops the audit with them.

---

## 11. The readiness for XCT-02

`XCT-02` (`wave-04-cross-cutting/XCT-02-transversal-admin.md`) is the
transversal administration. What this packet leaves ready:

- the audit of the validations EXISTS and is READ-ONLY in the admin: the
  transversal administration can read `ValidacionTicket` for the audit
  (`ADM-22`) without this package having to grow a listing;
- the ENTRY and the DELIVERY are already two distinct screens with two
  distinct containers, so the transversal area does not have to merge them;
- the capability of the operator is the existing `admin.acreditaciones.escribir`
  and the transversal administration can reuse it;
- **the A0 requests of §8 are the gate**: until `A0-XCT01-01`, `A0-XCT01-02` and
  `A0-XCT01-03` are applied, neither the module nor its routes exist at
  runtime.

`XCT-02` also has to know that the audit listing route (`RT-VA-01`) **is not
in the frozen ledger**: it was already an open request of `UI-05` and `API-05`
and it is still open. This package did NOT invent it.
