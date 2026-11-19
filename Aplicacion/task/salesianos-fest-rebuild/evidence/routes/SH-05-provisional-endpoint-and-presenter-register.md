# SH-05 — Provisional Endpoint And Presenter Register (extended ledger)

**Artifact:** `evidence/routes/SH-05-provisional-endpoint-and-presenter-register.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 (register) + A0 (contract authority) · **Status:** DRAFT FOR REVIEW — **every route in this document is provisional**
**Date:** 2026-11-19
**Authority:** `evidence/contracts/FR-07-presenter-schema-versions.md` §3.1–§3.4, §7 · `evidence/contracts/FR-09-open-decisions-register.md` · `Aplicacion/plan/salesianos-fest-rebuild/contratos/01-api-wrappers-presenters.md` §5, §9 · `Aplicacion/documentacion/02a-inventario-de-endpoints.md` (the 111 live routes)

---

## 0. Non-Negotiable Reading Rule

> **No URL in this document is live. No URL in this document may be presented to a user, cited in a test, or treated as an existing endpoint.**

The register exists because `FR-07` §3.1.2 makes **registration in `Aplicacion/backend/config/api.py` decisive**: *"A route of the ledger does not exist until its controller is registered there. Registered code that is not registered is dead code."*

Therefore, for every row below:

| Column | Value |
|---|---|
| `provisional` | **`sí` — in every single row of this document, without exception** |
| Existence condition | The controller is registered in `Aplicacion/backend/config/api.py`, the presenter exists with a `SCHEMA_VERSION`, and a drift test passes |
| Fixture use | A `PROVISIONAL_CONTRACT_FIXTURE` **may** feed a skeleton packet's typed fixture, and **may not** be consumed by an API integration packet as if it were a real response (`FREEZE-FX-1.0.0`, `FR-08`) |
| Authorisation | The owner named in the GOV-01 ledger keeps ownership. This document **does not** transfer ownership to anyone |

**The 111 live routes of the frozen backend are in `Aplicacion/documentacion/02a-inventario-de-endpoints.md`.** Nothing in this document is copied from them, because the plan rebuilds the API surface rather than copying it (`frontend/01` §5, `contratos/01` §5).

---

## 1. Extended Ledger — Read And Detail Routes

The GOV-01 ledger (`evidence/contracts/route-to-wrapper-ledger.csv`) froze **19 routes** covering the write/transactional core. `FR-07` §7 assigned A7 (this packet) the remaining **read** routes: *"Rutas de lectura restantes del ledger (catálogos, cuentas, equipos, competencias)"* (`GOV-01-OPEN-12`).

The table below extends that ledger. `RT-*` identifiers already used by GOV-01 are **not** renumbered.

### 1.1 `eventos` — editions and public catalogue

| id_ruta | método | ruta propuesta | presenter | wrapper | permiso | provisional |
|---|---|---|---|---|---|---|
| `RT-ED-03` | GET | `/ediciones` | `EdicionListaPresenter` | `PaginatedData[EdicionListItemOut]` | Administrador | sí |
| `RT-ED-04` | GET | `/ediciones/{edicion_id}` | `EdicionDetallePresenter` | `EdicionDetalleOut` | Administrador | sí |
| `RT-ED-05` | POST | `/ediciones` | `EdicionCrearPresenter` | `EdicionOut` | Administrador | sí |
| `RT-ED-06` | POST | `/ediciones/{edicion_id}/publicar` | `EdicionPublicarPresenter` | `EdicionOut` | Administrador | sí |
| `RT-ED-07` | GET | `/ediciones/{edicion_id}/patrocinadores` | `PatrocinadorEdicionPresenter` | `PatrocinadorListaOut` | público | sí |

`RT-ED-07` is the read side of `RT-MD-02` (create sponsor). Public visibility is filtered by edition and by the sponsor's own visibility flag — never by an ad-hoc query parameter.

### 1.2 `usuarios` — identity, accounts, titularities

| id_ruta | método | ruta propuesta | presenter | wrapper | permiso | provisional |
|---|---|---|---|---|---|---|
| `RT-ID-04` | GET | `/mi-cuenta/resumen` | `MiCuentaPresenter` | `MiCuentaOut` | Cuenta | sí |
| `RT-ID-05` | GET | `/mi-cuenta/compras` | `MisComprasPresenter` | `PaginatedData[MisComprasListItemOut]` | Cuenta | sí |
| `RT-ID-06` | GET | `/mi-cuenta/compras/{compra_id}` | `CompraDetallePresenter` | `CompraDetalleOut` | Titular o Administrador | sí |
| `RT-ID-07` | GET | `/administracion/personas` | `AdminPersonaListaPresenter` | `PaginatedData[AdminPersonaListItemOut]` | Administrador | sí |
| `RT-ID-08` | GET | `/administracion/personas/{persona_id}` | `AdminPersonaDetallePresenter` | `AdminPersonaDetalleOut` | Administrador | sí |
| `RT-ID-09` | GET | `/administracion/usuarios` | `AdminUsuarioListaPresenter` | `PaginatedData[AdminUsuarioListItemOut]` | Administrador | sí |
| `RT-ID-10` | POST | `/administracion/usuarios/{usuario_id}/estado` | `AdminUsuarioEstadoPresenter` | `AdminUsuarioOut` | Administrador + capability | sí |

### 1.3 `inscripciones` — sports registrations, pool, teams, participants

| id_ruta | método | ruta propuesta | presenter | wrapper | permiso | provisional |
|---|---|---|---|---|---|---|
| `RT-IN-01` | GET | `/inscripciones` | `InscripcionListaPresenter` | `PaginatedData[InscripcionListItemOut]` | Responsable (own) / Administrador (all) | sí |
| `RT-IN-02` | GET | `/inscripciones/{inscripcion_id}` | `InscripcionDetallePresenter` | `InscripcionDetalleOut` | Responsable o Administrador | sí |
| `RT-IN-03` | GET | `/inscripciones/{inscripcion_id}/pool` | `PoolPresenter` | `PoolOut` | Responsable o Administrador | sí |
| `RT-IN-04` | GET | `/inscripciones/{inscripcion_id}/equipos` | `EquiposInscripcionPresenter` | `EquiposInscripcionOut` | Responsable o Administrador | sí |
| `RT-IN-05` | POST | `/inscripciones/{inscripcion_id}/participantes` | `ParticipanteAsignarPresenter` | `PoolOut` | Responsable o Administrador | sí |
| `RT-IN-06` | DELETE | `/inscripciones/{inscripcion_id}/participantes/{participacion_id}` | `ParticipanteRetirarPresenter` | `PoolOut` | Responsable o Administrador | sí |
| `RT-IN-07` | GET | `/administracion/inscripciones` | `AdminInscripcionListaPresenter` | `PaginatedData[AdminInscripcionListItemOut]` | Administrador | sí |
| `RT-IN-08` | GET | `/administracion/inscripciones/{inscripcion_id}` | `AdminInscripcionDetallePresenter` | `AdminInscripcionDetalleOut` | Administrador | sí |
| `RT-IN-09` | GET | `/administracion/equipos` | `AdminEquipoListaPresenter` | `PaginatedData[AdminEquipoListItemOut]` | Administrador | sí |
| `RT-IN-10` | GET | `/administracion/equipos/{equipo_id}` | `AdminEquipoDetallePresenter` | `AdminEquipoDetalleOut` | Administrador | sí |
| `RT-IN-11` | GET | `/administracion/participantes` | `AdminParticipanteListaPresenter` | `PaginatedData[AdminParticipanteListItemOut]` | Administrador | sí |
| `RT-IN-12` | GET | `/catalogo/paquetes` | `CatalogoPaquetesPresenter` | `CatalogoPaquetesOut` | público (edition-scoped) | sí |
| `RT-IN-13` | GET | `/catalogo/disciplinas` | `CatalogoDisciplinasPresenter` | `CatalogoDisciplinasOut` | público (edition-scoped) | sí |

`RT-IN-03` (`PoolPresenter`) is the route behind the plan's required trio *pagados · asignados activos · disponibles* and the plan's warning *"do not confuse the maximum roster size with the balance of paid cupos"*. **The pool arithmetic is computed by the backend and returned as three numbers plus the impediment list; the client never subtracts.**

### 1.4 `pases` — party passes, beneficiaries, courtesy passes

| id_ruta | método | ruta propuesta | presenter | wrapper | permiso | provisional |
|---|---|---|---|---|---|---|
| `RT-PS-01` | GET | `/pases` | `PaseCatalogoPresenter` | `PaseCatalogoOut` | público (edition-scoped) | sí |
| `RT-PS-02` | GET | `/pases/{pase_id}` | `PaseDetallePresenter` | `PaseDetalleOut` | público | sí |
| `RT-PS-03` | GET | `/pases/compras/{compra_id}` | `PaseCompraDetallePresenter` | `PaseCompraDetalleOut` | Titular (vínculo) o Administrador | sí |
| `RT-PS-04` | GET | `/pases/compras/{compra_id}/beneficiarios` | `PaseBeneficiariosPresenter` | `PaseBeneficiariosOut` | Titular (vínculo) o Administrador | sí |
| `RT-PS-05` | POST | `/pases/compras/{compra_id}/beneficiarios` | `PaseBeneficiarioAsignarPresenter` | `PaseBeneficiariosOut` | Titular (vínculo) o Administrador | sí |
| `RT-PS-06` | GET | `/administracion/pases` | `AdminPaseListaPresenter` | `PaginatedData[AdminPaseListItemOut]` | Administrador | sí |
| `RT-PS-07` | GET | `/administracion/pases/cortesias` | `AdminCortesiaListaPresenter` | `PaginatedData[AdminCortesiaListItemOut]` | Administrador | sí |
| `RT-PS-08` | POST | `/administracion/pases/cortesias` | `AdminCortesiaCrearPresenter` | `AdminCortesiaOut` | Administrador | sí |

`RT-PS-08` is the courtesy-pass route from `FL-07`: it creates a **free right with a reason and an audit trail** and must never create a fictitious payment order or transaction.

### 1.5 `pagos` — orders, verdicts, attempts

| id_ruta | método | ruta propuesta | presenter | wrapper | permiso | provisional |
|---|---|---|---|---|---|---|
| `RT-PG-06` | GET | `/pagos/ordenes/{orden_id}/intentos` | `PagoIntentosPresenter` | `PagoIntentosOut` | Titular del comprobador o Administrador | sí |
| `RT-PG-07` | GET | `/administracion/pagos/{compra_id}` | `AdminPagoDetallePresenter` | `AdminPagoDetalleOut` | Administrador | sí |

`RT-PG-04` (frozen by GOV-01) remains the **operational list**, and it keeps the `estado_operativo` filter — a frozen obligation, not an optional improvement (`FR-07` §3.4, `F-9`).

### 1.6 `marketplace` — products, orders, stock, delivery

| id_ruta | método | ruta propuesta | presenter | wrapper | permiso | provisional |
|---|---|---|---|---|---|---|
| `RT-MK-01` | GET | `/marketplace/categorias` | `CategoriaListaPresenter` | `CategoriaListaOut` | público | sí |
| `RT-MK-02` | GET | `/marketplace/productos` | `ProductoListaPresenter` | `PaginatedData[ProductoListItemOut]` | público | sí |
| `RT-MK-03` | GET | `/marketplace/productos/{slug}` | `ProductoDetallePresenter` | `ProductoDetalleOut` | público | sí |
| `RT-MK-04` | GET | `/marketplace/pedidos/{token}` | `PedidoSeguimientoPresenter` | `PedidoSeguimientoOut` | Titular (vínculo) | sí |
| `RT-MK-05` | GET | `/administracion/marketplace/productos` | `AdminProductoListaPresenter` | `PaginatedData[AdminProductoListItemOut]` | Administrador | sí |
| `RT-MK-06` | GET | `/administracion/marketplace/productos/{producto_id}` | `AdminProductoDetallePresenter` | `AdminProductoDetalleOut` | Administrador | sí |
| `RT-MK-07` | GET | `/administracion/marketplace/pedidos` | `AdminPedidoListaPresenter` | `PaginatedData[AdminPedidoListItemOut]` | Administrador | sí |
| `RT-MK-08` | GET | `/administracion/marketplace/inventario` | `AdminInventarioPresenter` | `AdminInventarioOut` | Administrador | sí |
| `RT-MK-09` | POST | `/administracion/marketplace/inventario/movimientos` | `AdminInventarioMovimientoPresenter` | `AdminInventarioMovimientoOut` | Administrador | sí |
| `RT-MK-10` | GET | `/administracion/marketplace/entregas` | `AdminEntregaListaPresenter` | `PaginatedData[AdminEntregaListItemOut]` | Administrador | sí |

`RT-MK-09` is `FL-09`: an entry/exit/adjustment with a **reason and an actor**, and **no purchase** for a non-sale exit.

### 1.7 `validaciones` — ticket preview, confirm, audit

| id_ruta | método | ruta propuesta | presenter | wrapper | permiso | provisional |
|---|---|---|---|---|---|---|
| `RT-VA-01` | GET | `/administracion/validaciones` | `AdminValidacionListaPresenter` | `PaginatedData[AdminValidacionListItemOut]` | Administrador | sí |
| `RT-VA-02` | GET | `/administracion/pases/validar` | `— (no data route)` | — | Operador autenticado | sí |

`RT-RT-01` (preview) and `RT-RT-02` (confirm) are already frozen by GOV-01. **`RT-VA-02` is a screen, not a data route** — it is listed only so the register is complete; the screen consumes `RT-RT-01`/`RT-RT-02`.

### 1.8 `competencias` — tournaments, rounds, matches, bracket, agenda

| id_ruta | método | ruta propuesta | presenter | wrapper | permiso | provisional |
|---|---|---|---|---|---|---|
| `RT-CP-01` | GET | `/administracion/competencias` | `CompetenciaListaPresenter` | `PaginatedData[CompetenciaListItemOut]` | Administrador | sí |
| `RT-CP-02` | GET | `/administracion/competencias/{competencia_id}` | `CompetenciaDetallePresenter` | `CompetenciaDetalleOut` | Administrador | sí |
| `RT-CP-03` | GET | `/administracion/competencias/{competencia_id}/cuadro` | `CuadroPresenter` | `CuadroOut` | Administrador | sí |
| `RT-CP-04` | GET | `/administracion/competencias/{competencia_id}/encuentros/{encuentro_id}` | `EncuentroDetallePresenter` | `EncuentroDetalleOut` | Administrador | sí |
| `RT-CP-05` | GET | `/administracion/competencias/agenda` | `AgendaPresenter` | `AgendaOut` | Administrador | sí |
| `RT-CP-06` | POST | `/administracion/encuentros/{encuentro_id}/resultado` | `EncuentroResultadoPresenter` | `EncuentroDetalleOut` | Administrador | sí |
| `RT-CP-07` | POST | `/administracion/encuentros/{encuentro_id}/avance/preview` | `AvancePreviewPresenter` | `AvancePreviewOut` | Administrador | sí |
| `RT-CP-08` | POST | `/administracion/encuentros/{encuentro_id}/avance/confirmar` | `AvanceConfirmarPresenter` | `CuadroOut` | Administrador | sí |
| `RT-CP-09` | POST | `/administracion/encuentros/{encuentro_id}/correccion/preview` | `CorreccionPreviewPresenter` | `CorreccionPreviewOut` | Administrador | sí |
| `RT-CP-10` | GET | `/competencias/{competencia_id}/cuadro` | `CuadroPublicoPresenter` | `CuadroOut` | público | sí |

`RT-CP-07`/`RT-CP-08` split **preview** from **confirm** — this is the frozen `FREEZE-RT` principle applied to the bracket (`QA-K04`: "advance preview does not write; confirm does"). `RT-CP-09` gives the impact preview required by `QA-K03`.

### 1.9 `patrocinadores` — sponsors

| id_ruta | método | ruta propuesta | presenter | wrapper | permiso | provisional |
|---|---|---|---|---|---|---|
| `RT-PA-01` | GET | `/administracion/patrocinadores` | `PatrocinadorListaPresenter` | `PaginatedData[PatrocinadorListItemOut]` | Administrador | sí |
| `RT-PA-02` | GET | `/administracion/patrocinadores/{patrocinador_id}` | `PatrocinadorDetallePresenter` | `PatrocinadorDetalleOut` | Administrador | sí |

### 1.10 `notificaciones` / recovery — the one remaining public write

| id_ruta | método | ruta propuesta | presenter | wrapper | permiso | provisional |
|---|---|---|---|---|---|---|
| `RT-RC-01` | POST | `/recuperar-compra` | `RecuperarCompraPresenter` | `RecuperarCompraOut` | público | sí |

`RT-RC-01` answers with a **neutral** message regardless of whether a purchase exists (`REC-01`, `QA-U03`).

---

## 2. Summary Counts

| Block | GOV-01 frozen rows | GOV-02 additions | Total proposed rows | All provisional? |
|---|---:|---:|---:|---|
| `eventos` | 2 | 5 | 7 | yes |
| `usuarios` | 3 | 7 | 10 | yes |
| `inscripciones` | 1 | 13 | 14 | yes |
| `pagos` | 5 | 2 | 7 | yes |
| `validaciones` | 3 | 1 (+1 non-data) | 4 (+1) | yes |
| `pases` | 1 | 8 | 9 | yes |
| `marketplace` | 1 | 10 | 11 | yes |
| `patrocinadores` | 1 | 2 | 3 | yes |
| `competencias` | 0 | 10 | 10 | yes |
| recovery | 0 | 1 | 1 | yes |
| **Total** | **19** | **59** | **78** | **yes — 78/78** |

**GOV-01-OPEN-12 is now addressed**: the read-route families (catalogues, accounts, teams, competitions, payments detail, marketplace, validations audit) are enumerated. The register is **proposed**, not approved — A0 ratifies it before any API-0x packet consumes it.

---

## 3. Provisional Decisions Register (explicit)

| ID | Decision | Status | Owner | Affects |
|---|---|---|---|---|
| `P-01` | Guest-management links travel as a **path token** (`/pases/gestionar/[token]`, `/tienda/pedidos/[token]`) | **Provisional.** The plan explicitly says *"the link token does not have to travel in the route (it could be a temporary session mechanism); define it with the architecture agent."* | A0 + A7 | PASS-02, SHOP-03, `RT-PS-03`, `RT-MK-04` |
| `P-02` | `/mi-cuenta` replaces `/dashboard` | **Provisional** (UX proposal, not a technical obligation) | A7 | ACCOUNT-01…05 |
| `P-03` | `/registro` replaces `/register` | **Provisional** | A7 | AUTH-02 |
| `P-04` | A **public** bracket route `/competencias/[id]` exists with **no page ID** | **Provisional.** It appears only in `frontend/05` §2. It is registered here as `RT-CP-10` but it is **not** one of the 38 page IDs. | A0 + A7 | — |
| `P-05` | The 22 admin destinations are **conceptual**; some become tabs or panels of one route | **Provisional**, stated by the plan (`frontend/01` §3) | A7 | ADM-01…ADM-22 |
| `P-06` | `estado_operativo` must be exposed as a filter in the admin payments UI | **Frozen obligation** (`F-9`, `RT-PG-04`) — not provisional | A0 + A7 | ADM-14 |
| `P-07` | Whether guest checkout also covers **inscriptions** | **Open** (`PD-07`) | A0 | SPORT-01 |
| `P-08` | Public edition history | **Not ratified** (`GOV-01-OPEN-02`) | A0 | PUB-01, PUB-02 |
| `P-09` | Current `/administracion/competencias/cuadro` → proposed `/administracion/competencias/[id]/cuadro` | **Provisional** | A7 | ADM-12 |
| `P-10` | `REC-01` email provider | **Deferred** (`PD-08`) | A0 | REC-01, `RT-RC-01` |
| `P-11` | Query-parameter names for the admin lists (`q`, `ordering`, `desde`, `hasta`) | **Provisional.** Only `RT-PG-04` has a frozen query contract. The rest mirror it. | A7 | all admin list routes |
| `P-12` | Edition scoping for list endpoints: explicit `edicion_id` vs actor's active edition vs single published edition | **Frozen** (`D-01` / `FREEZE-ED-1.0.0`) — resolution order is fixed; only the *transport* of the scope is provisional | A1 + A7 | all edition-scoped reads |

---

## 4. What This Register Does NOT Do

- It does **not** register any controller in `Aplicacion/backend/config/api.py` (forbidden root in this packet).
- It does **not** create a Zod mirror, a query-key factory, a service or a hook.
- It does **not** decide the wrapper JSON shape of the 59 new routes — that is the DOM/API packets' job, under `FREEZE-PS-1.0.0`.
- It does **not** claim any of the 78 routes exists. It states what each page **will need** so the UI packets can be designed against a frozen contract instead of a guess.

---

## 5. Acceptance Criteria For This Document

- [x] The GOV-01 ledger's 19 rows are carried forward unchanged (no renumbering).
- [x] The read-route families named in `GOV-01-OPEN-12` are enumerated (59 new rows).
- [x] **Every** row is marked `provisional = sí`.
- [x] No live URL is asserted; the existence condition (registration in `config/api.py`) is stated for all rows.
- [x] Presenter and wrapper names follow the frozen naming convention (`<Entidad><Operación>In/Out`, `<Entidad>Presenter`).
- [x] The `PROVISIONAL_CONTRACT_FIXTURE` restriction is restated.
- [x] Provisional decisions are listed explicitly with owner and affected page IDs.
- [x] No backend file, contract file or plan file was created or modified.
