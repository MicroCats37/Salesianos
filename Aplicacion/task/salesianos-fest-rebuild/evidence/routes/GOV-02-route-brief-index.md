# GOV-02 — Route Brief Index And Route Inventory

**Artifact:** `evidence/routes/GOV-02-route-brief-index.md` · **Packet:** GOV-02 (`GOV-02-route-ux-baseline`) · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 (merged artifact owner per the packet's parallelism rule) · **Status:** DRAFT FOR REVIEW
**Date:** 2026-11-19
**Scope:** every page ID defined by the plan. **No UI code was produced.**

---

## 1. Coverage Ledger

| Dimension | Required | Delivered |
|---|---:|---:|
| Plan page IDs briefed | **38** | **38 / 38** |
| Public / account / identity routes | 10 | 10 (`RB-01`) |
| Commerce routes (passes, store, recovery) | 6 | 6 (`RB-02`) |
| Admin routes | 22 | 22 (`RB-03`…`RB-08`) |
| Routes with a visible state matrix | 38 | 38 |
| Routes with responsive intent at 360 / 390 / 768 / 1024 / 1440 | 38 | 38 |
| Routes with a semantic-token intent | 38 | 38 |
| Routes with the mandatory shadcn comparison recorded | 38 | 38 (family comparison in `SH-04`, per-route obligation `GOV-02-SH-01`) |
| Routes with a presenter/endpoint dependency | 38 | 38 (all marked provisional) |
| High-priority flows with mobile + desktop wireframe intent | 6 flows / 11 routes | 6 / 11 (`SH-06`) |
| Additional conceptual route without a page ID | 1 | 1 (`/competencias/[id]`, registered as `RT-CP-10`) |

### 1.1 Correction to a prior count

The exploration recorded **"40 page IDs"**. The plan's own tables define **38**:

| Plan section | Rows | Count |
|---|---|---:|
| `frontend/01` §2 — visitor, account, responsible | `PUB-01`, `PUB-02`, `AUTH-01`, `AUTH-02`, `ACCOUNT-01`…`ACCOUNT-05`, `SPORT-01`, `PASS-01`, `PASS-02`, `SHOP-01`…`SHOP-03`, `REC-01` | **16** |
| `frontend/01` §3 — administration | `ADM-01`…`ADM-22` | **22** |
| | **Total** | **38** |

Plus one conceptual route with **no page ID** — `/competencias/[id]`, the public bracket, proposed in `frontend/05` §2 (registered as `RT-CP-10`, marked `P-04`).

**⇒ 38 page IDs + 1 unnumbered proposal = 39 route proposals.** The "40" figure is corrected here and in the apply-progress artifact. The gap was already noted in GOV-01 as the *"ledger is partial — 19 proposed routes covering the plan's 12 use-case contracts; read routes extend in GOV-02"*.

---

## 2. Route Inventory

Every row: actor · primary action · states · flow · presenter/endpoint dependency · shadcn obligation.
**All endpoints are provisional** (`SH-05` §0). Responsive intent is in `SH-02`; token intent is in `SH-01`; the full fiche is in the referenced brief file.

### 2.1 Public, identity and account (16)

| ID | Route (provisional) | Actor | Primary action | Key states | Flow | Endpoint dependency (provisional) | Brief |
|---|---|---|---|---|---|---|---|
| `PUB-01` | `/` | visitante | Explorar / CTA inscribir | loading · error+retry · *not published* · *module off* | FL-01 | `RT-ED-01`, `RT-ED-02`, `RT-IN-12/13`, `RT-PS-01`, `RT-MK-02`, `RT-ED-07` | `RB-01` |
| `PUB-02` | `/informacion` | visitante | Conocer reglas | loading · error · *anchors resolve* | FL-01 | `RT-ED-01`, `RT-ED-02`, `RT-IN-13` | `RB-01` |
| `AUTH-01` | `/login` | anónimo | Autenticar | validation · in-progress · wrong credential · disabled | — | auth chain (no new endpoint) | `RB-01` |
| `AUTH-02` | `/registro` | anónimo | Resolver DNI y registrar | validation · not found · source unavailable · already linked · duplicate | FL-02 | `RT-ID-01/02/03` | `RB-01` |
| `ACCOUNT-01` | `/mi-cuenta` | cuenta | Ir a inscripción/compra | loading · empty · error · session expired | — | `RT-ID-04` | `RB-01` |
| `ACCOUNT-02` | `/mis-inscripciones` | responsable | Abrir / crear inscripción | empty · filtered-empty · payment verifying · window closed | FL-03 | `RT-IN-01` | `RB-01` |
| `ACCOUNT-03` | `/mis-inscripciones/[id]` | propietario | Asignar/mover/agregar cupos | 6 blocking states · partial · irreversible | FL-04, FL-05 | `RT-IN-02/03/04/05/06`, `RT-CM-01` | `RB-01` |
| `ACCOUNT-04` | `/mis-compras` | cuenta | Abrir comprobante | empty · filtered-empty · partial | — | `RT-ID-05` | `RB-01` |
| `ACCOUNT-05` | `/mis-compras/[id]` | titular | Consultar derecho | error · permission · partial (paid, not enabled) | FL-12 | `RT-ID-06` | `RB-01` |
| `SPORT-01` | `/inscripcion` | responsable | Confirmar y crear compra | validation · in-progress · 0 cupos before payment | FL-02, FL-03 | `RT-IN-12/13`, `RT-ID-02/03`, `RT-CM-01` | `RB-01` |
| `PASS-01` | `/pases` | visitante | Comprar pase | validation · gateway closed · pending · verifying · failed · pending assignment | FL-06 | `RT-PS-01/02`, `RT-CM-02` | `RB-02` |
| `PASS-02` | `/pases/gestionar/[token]` | invitado | Asignar personas | expired · wrong purchase · duplicate right · no cupo · revoked | FL-06 | `RT-PS-03/04/05`, `RT-RT-03` | `RB-02` |
| `SHOP-01` | `/tienda` | visitante | Elegir producto | empty · category empty · out of stock · image error · no store | FL-08 | `RT-MK-01/02` | `RB-02` |
| `SHOP-02` | `/tienda/[slug]` | visitante | Crear pedido | validation · price/stock revalidated · paid-not-delivered | FL-08 | `RT-MK-03`, `RT-CM-03` | `RB-02` |
| `SHOP-03` | `/tienda/pedidos/[token]` | invitado | Ver ticket/entrega | neutral denial · empty · paid-not-delivered | FL-08 | `RT-MK-04` | `RB-02` |
| `REC-01` | `/recuperar-compra` | visitante | Solicitar acceso | sent · rate-limited · temporary error · neutral | — | `RT-RC-01` | `RB-02` |

### 2.2 Administration (22)

| ID | Route (provisional) | Actor | Primary action | Key states | Flow | Endpoint dependency (provisional) | Brief |
|---|---|---|---|---|---|---|---|
| `ADM-01` | `/administracion` | administrador | Navegar a lista filtrada | empty ("Aún no hay inscripciones…") · no edition | FL-12 | `RT-ED-01` + list routes of the destinations | `RB-03` |
| `ADM-02` | `/administracion/ediciones` | administrador | Crear/publicar ediciones | empty · validation · in-progress · publish confirmation | FL-01 | `RT-ED-03/04/05/06` | `RB-03` |
| `ADM-03` | `/administracion/personas` | administrador | Buscar por documento | prompt · no results · error | FL-02 | `RT-ID-07/08`, `RT-ID-01/02` | `RB-03` |
| `ADM-04` | `/administracion/usuarios` | administrador | Gestionar cuentas/grupos | empty · validation · permission (no escalation) · deactivate confirmation | — | `RT-ID-09/10` | `RB-03` |
| `ADM-05` | `/administracion/inscripciones` | administrador | Gestionar inscripciones | empty · filtered-empty · error | FL-03 | `RT-IN-07` | `RB-03` |
| `ADM-06` | `/administracion/inscripcion/[id]` | administrador | Operar una inscripción | 5 per-tab empties · irreversible withdraw | FL-03, FL-05 | `RT-IN-08/03/04/07/09` | `RB-03` |
| `ADM-07` | `/administracion/equipos` | administrador | Buscar y gestionar equipos | empty · filtered-empty · error | FL-05 | `RT-IN-09` | `RB-04` |
| `ADM-08` | `/administracion/equipos/[id]` | administrador | Operar equipo individual | empty (no players) · ineligible · irreversible | FL-05 | `RT-IN-10`, `RT-IN-03`, `RT-ID-01/02` | `RB-04` |
| `ADM-09` | `/administracion/participantes` | administrador | Buscar personas/participaciones | prompt · no results · error | FL-05 | `RT-IN-11`, `RT-ID-07/08` | `RB-04` |
| `ADM-10` | `/administracion/competencias` | administrador | Crear/editar, agenda, cuadro | empty · filtered-empty · error | FL-11 | `RT-CP-01` | `RB-05` |
| `ADM-11` | `/administracion/competencias/[id]` | administrador | Equipos, rondas, encuentros | no rounds / no teams · version conflict · advance preview | FL-11 | `RT-CP-02`, `RT-CP-04` | `RB-05` |
| `ADM-12` | `/administracion/competencias/[id]/cuadro` | administrador | Registrar resultado / preview / corregir | no rounds · advance error · version conflict · correction reason | FL-11 | `RT-CP-03/04/06/07/08/09` | `RB-05` |
| `ADM-13` | `/administracion/competencias/agenda` | administrador | Consultar programación | empty day · filtered-empty · error | FL-11 | `RT-CP-05` | `RB-05` |
| `ADM-14` | `/administracion/pagos` | administrador | Investigar compras/pagos | empty · filtered-empty · 403 · partial · manual-approval confirmation | FL-12 | **`RT-PG-04`** (frozen) · **`RT-PG-05`** (frozen) · `RT-PG-07`, `RT-PG-06`, `RT-ID-06` | `RB-06` |
| `ADM-15` | `/administracion/pases` | administrador | Comprar/otorgar/cancelar/revisar | empty · policy refusal · revocation confirmation | FL-07 | `RT-PS-06/07/08/05`, **`RT-RT-03`** (frozen) | `RB-07` |
| `ADM-16` | `/administracion/pases/validar` | operador | Escanear / confirmar ingreso | camera denied → manual path · refused (4 reasons) · in-progress | FL-10 | **`RT-RT-01`**, **`RT-RT-02`** (frozen) | `RB-07` |
| `ADM-17` | `/administracion/marketplace` | administrador | Gestionar tienda | empty · filtered-empty · error | FL-08 | `RT-MK-05/07/08` | `RB-07` |
| `ADM-18` | `/administracion/marketplace/productos/[id]` | administrador | Editar producto | validation · upload in progress · media rejected (4 reasons) | FL-08 | **`RT-MD-01`** (frozen), `RT-MK-06` | `RB-07` |
| `ADM-19` | `/administracion/marketplace/inventario` | administrador | Registrar stock | empty · validation · insufficient · exit confirmation | FL-09 | `RT-MK-08/09` | `RB-07` |
| `ADM-20` | `/administracion/marketplace/entregas` | operador | Confirmar entrega | refused · partial delivery · double redemption | FL-10 | `RT-MK-10` + the shared validation service | `RB-07` |
| `ADM-21` | `/administracion/patrocinadores` | administrador | Logo, galería, edición | empty · validation · media rejected | — | **`RT-MD-02`** (frozen), `RT-PA-01/02`, `RT-ED-07` | `RB-08` |
| `ADM-22` | `/administracion/validaciones` | administrador | Auditoría transversal | empty · filtered-empty · error | FL-10 | `RT-VA-01` | `RB-08` |

**Legend:** **bold** endpoint ids are the routes frozen by GOV-01 (19 rows). All others are the 59 read/detail rows added by this packet (`SH-05` §2) — **78 of 78 are provisional**.

---

## 3. Flow Coverage

| Flow | Plan | Routes that carry it |
|---|---|---|
| `FL-01` | cambiar edición / consultar catálogo | `PUB-01`, `PUB-02`, `ADM-02` |
| `FL-02` | resolver persona por documento | `AUTH-02`, `SPORT-01`, `ADM-03`, `ADM-08` |
| `FL-03` | inscribir equipo y comprar cupos | `SPORT-01`, `ACCOUNT-02`, `ACCOUNT-03`, `ADM-05`, `ADM-06` |
| `FL-04` | ampliar cupos | `ACCOUNT-03` |
| `FL-05` | gestionar plantilla | `ACCOUNT-03`, `ADM-06`, `ADM-07`, `ADM-08`, `ADM-09` |
| `FL-06` | comprar pase sin cuenta | `PASS-01`, `PASS-02`, `ADM-15` |
| `FL-07` | otorgar cortesía | `ADM-15` |
| `FL-08` | comprar producto | `SHOP-01`, `SHOP-02`, `SHOP-03`, `ADM-17`, `ADM-18` |
| `FL-09` | ajuste/consumo de stock | `ADM-19` |
| `FL-10` | validar entrada o entrega | `ADM-16`, `ADM-20`, `ADM-22` |
| `FL-11` | administrar competencia | `ADM-10`…`ADM-13` |
| `FL-12` | investigar incidencia de pago | `ADM-14`, `ACCOUNT-05` |

**All 12 flows are covered.** Every plan `QA-*` acceptance case that binds to a route is referenced in that route's brief (`QA-E01`, `QA-U01`…`QA-U03`, `QA-I01`…`QA-I05`, `QA-P01`…`QA-P03`, `QA-C01`…`QA-C03`, `QA-M01`…`QA-M04`, `QA-V01`, `QA-V02`, `QA-K01`…`QA-K05`, `QA-A01`…`QA-A03`, `QA-MEDIA01`, `QA-N01`).

---

## 4. Mandatory Shadcn Comparison Obligation — Per Route Family

The full comparison is in `SH-04`. Every route brief names its candidate components and carries the obligation `GOV-02-SH-01`: **re-run the MCP comparison for that family before adding anything.**

| Family | Routes | Shortlisted basis |
|---|---|---|
| Marketing / hero | `PUB-01`, `PUB-02` | `card`, `accordion`, `carousel`, `badge`, `button` |
| Auth forms | `AUTH-01`, `AUTH-02` | `input`, `label`, `button`, `alert`, `checkbox`; **local brand composition preserved**, stock `login-*`/`signup-*` blocks rejected |
| Catalogue | `SHOP-01`, `SHOP-02` | `card`, `carousel`, `input`, `select`, `badge`, `empty` |
| Wizard | `SPORT-01`, `PASS-01`, `SHOP-02` | `progress`, `card`, `dialog`, `button`, `alert` |
| Account | `ACCOUNT-01`…`ACCOUNT-05` | `card`, `item`, `table`, `badge`, `button`, `empty` |
| Admin shell | all `ADM-*` | `sidebar` + `sidebar-01`/`sidebar-02`/`sidebar-13`/`sidebar-16` compared; `dashboard-01` **rejected** (2nd table lib, 2nd icon lib, dnd-kit) |
| Operational list | `ADM-05/07/09/14/17/19/22` | `table` + `data-table-demo` as a **behaviour reference only** (TanStack v9 ≠ project's v8) + `pagination` (server-driven) + `dropdown-menu` |
| Detail / tabs | `ADM-06`, `ADM-11` | `tabs`, `drawer` (**one** panel primitive, not `sheet`), `alert-dialog` |
| Confirmation | every destructive action | `dialog` (short) vs `alert-dialog` (irreversible) |
| Validation / QR | `ADM-16`, `ADM-20` | project scanner component + `input` + `card` + `button` + `alert` (no registry item provides a QR scanner) |
| Media | `ADM-18`, `ADM-21` | `carousel` + `input-group` + file input |
| Charts | `ADM-01` (conditional) | `chart` **only after** the `--chart-*` tokens exist |

---

## 5. Unresolved Decisions Carried Forward By This Packet

| ID | Question | Owner | Blocking scope |
|---|---|---|---|
| `GOV-02-UX-01` | The dark value of `--secondary` (`#3a43c9` proposed) | A7 + A0 | token file (FND-06) |
| `GOV-02-UX-02` | Whether the dark theme ships in the first cut (the legacy `.dark` block is incomplete) | A0 + A7 | FND-06 |
| `GOV-02-UX-03` | Whether the legacy marketing gradients survive on the new portada | A7 + product | `PUB-01` |
| `GOV-02-UX-04` | Font hosting: keep `next/font` (Plus Jakarta Sans + Geist Mono) or move to the registry `font-*` items | A7 | FND-06 |
| `GOV-02-UX-05` | Whether `--accent` (gold) is an interactive colour or strictly decorative | A7 + a11y | all routes using accent for text |
| `GOV-02-SH-01` | The per-route shadcn comparison is a **precondition** of every UI packet | A7 | UI-01…UI-05 |
| `GOV-02-SH-02` | Diff the local `components/ui/*` against the registry before replacing anything | A7 | FND-06 |
| `GOV-02-SH-03` | `field` must not enter the `GenericForm` wrapper path without proving there is no double render | A7 | FND-07, FND-08 |
| `GOV-02-SH-04` | TanStack Table v8 (project) vs v9 (registry example) | A7 | FND-08, ADM-05/07/09/14/17/19/22 |
| `GOV-02-SH-05` | `chart` requires the `--chart-*` tokens first | A7 + A0 | ADM-01, ADM-11, ADM-12 |
| `GOV-02-SH-06` | Choose exactly **one** panel primitive: `drawer` **or** `sheet` | A7 | FND-06 |
| `GOV-02-SH-07` | CLI fallback must use `-c Aplicacion/frontend` and `get_add_command_for_items` | A7 | FND-06+ |
| `GOV-02-SH-08` | `get_audit_checklist` before any UI packet is complete | A7 | every UI-0x |
| `GOV-02-BL-01` | The success envelope **includes `message`** — the frozen test that denies it is a baseline failure | A7 + A0 | DOM-*, API-* |
| `GOV-02-BL-02` | A PostgreSQL test lane is required | A0 + A9 | XCT-01…03 |
| `GOV-02-BL-03` | The target matrix must pin the settings module | A0 | `BL-05` |
| `GOV-02-BL-04` | The payment UNIQUE constraints vs the target commerce model | A2 + A0 | DOM-04/05/06 |
| `GOV-02-BL-05` | `SynchronousOnlyOperation` must be fixed, not carried | A0 | FND-01, XCT-01 |
| `GOV-02-BL-06` | Freeze one status-code convention per operation (409 family) | A0 + A2 | DOM-*, API-* |
| `GOV-02-BL-07` | The rebuilt payments list must not inherit the duplicate-key defect | A7 | ADM-14 |
| `GOV-02-BL-08` | The catalogue mirror must follow the frozen envelope; keep the "unknown verdict renders neutrally" test | A7 + A0 | FND-07, ADM-05/07/09/14 |
| `GOV-02-BL-09` | Biome ceiling 105 errors / 93 warnings | A7 + A9 | every UI-0x |
| `GOV-02-BL-10` | The order-dependent file must pass in isolation **and** in the full race | A9 | `BL-05`, VER-01 |
| `GOV-02-BL-11` | No tsconfig-excluded-but-imported tree in the target | A7 | FND-06, FND-08 |
| `GOV-02-BL-12` | The hardcoded-colour audit is a separate gate from Biome | A7 | every UI-0x |
| `GOV-02-CM-01`…`05` | The five target-matrix ratification questions | A0 | `BL-05` |

**Provisional route decisions** `P-01`…`P-12` live in `SH-05` §3.

---

## 6. Evidence File Index (this packet)

| File | Content |
|---|---|
| `evidence/routes/GOV-02-route-brief-index.md` | this file — the merged inventory |
| `evidence/routes/SH-01-visual-direction-and-semantic-tokens.md` | legacy identity → semantic roles, light/dark, chart tokens, motion, icons |
| `evidence/routes/SH-02-responsive-and-accessibility-matrix.md` | the 5 widths, the a11y contract, per-surface rules, residual gaps |
| `evidence/routes/SH-03-state-matrix-and-recovery-patterns.md` | the 10 states, HTTP→presentation, the 5 payment states, the recovery matrix |
| `evidence/routes/SH-04-shadcn-candidate-comparison.md` | the MCP execution record and every candidate table |
| `evidence/routes/SH-05-provisional-endpoint-and-presenter-register.md` | the extended ledger (78 rows, all provisional) + the provisional decisions |
| `evidence/routes/SH-06-wireframe-intent-high-priority.md` | mobile + desktop wireframes for the 6 Alta flows |
| `evidence/routes/RB-01-public-account-identity.md` | 10 briefs |
| `evidence/routes/RB-02-commerce-passes-store.md` | 6 briefs |
| `evidence/routes/RB-03-admin-editions-identity-inscriptions.md` | 6 briefs |
| `evidence/routes/RB-04-admin-teams-participants.md` | 3 briefs |
| `evidence/routes/RB-05-admin-competitions.md` | 4 briefs |
| `evidence/routes/RB-06-admin-payments.md` | 1 brief |
| `evidence/routes/RB-07-admin-passes-marketplace.md` | 6 briefs |
| `evidence/routes/RB-08-admin-sponsors-and-validation.md` | 2 briefs |
| `evidence/baseline/BL-01-baseline-summary.md` | the command table and headline numbers |
| `evidence/baseline/BL-02-backend-baseline.md` | the backend commands, the 13 failures, the environment analysis |
| `evidence/baseline/BL-03-frontend-baseline.md` | the frontend commands, the red file, the Biome figures, `git status` |
| `evidence/baseline/BL-04-failure-classification.md` | the classification and the regression oracle |
| `evidence/baseline/BL-05-target-command-matrix.md` | the **target** matrix, recorded separately |

---

## 7. Acceptance Criteria For This Document

- [x] Every proposed page ID has a reviewable route brief and a visible state matrix.
- [x] High-priority flows have mobile/desktop wireframe intent **without implementation code**.
- [x] Every route is explicitly marked provisional; no live URL is asserted.
- [x] Every route names its actor, actions, states, flows, presenter/endpoint dependency, responsive intent, semantic-token intent and the shadcn comparison obligation.
- [x] The page-ID count is corrected against the plan's own tables.
- [x] All 12 plan flows and all 29 `QA-*` cases are bound to routes.
- [x] Every unresolved decision has an owner and a blocking scope.
