# SH-06 — Mobile / Desktop Wireframe Intent For High-Priority Flows

**Artifact:** `evidence/routes/SH-06-wireframe-intent-high-priority.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — **wireframe intent only; no implementation code, no JSX, no component**
**Date:** 2026-11-19
**Authority:** `Aplicacion/plan/salesianos-fest-rebuild/frontend/01-mapa-rutas-y-navegacion.md` §7 (design priorities) · `frontend/06-sistema-ux-ui.md` §7 (per-page deliverables) · `Aplicacion/plan/salesianos-fest-rebuild/frontend/02`, `03`, `04`, `05`

---

## 0. Scope And Priority Source

`frontend/01` §7 sets the design priorities. This document covers the **Alta** priority flows in full and names the **Media** ones with a lighter treatment. The **Baja/diferido** items (branding, institutional pages, unrequested extensions) are explicitly **not** wired.

| Priority | Flows | Page IDs | Treatment |
|---|---|---|---|
| **Alta** | Sports registration + registration detail | `SPORT-01`, `ACCOUNT-03` | Full wireframe, both breakpoints |
| **Alta** | Admin payments | `ADM-14` | Full wireframe, both breakpoints |
| **Alta** | Admin teams | `ADM-07`, `ADM-08` | Full wireframe, both breakpoints |
| **Alta** | Competitions / matches | `ADM-11`, `ADM-12`, `ADM-13` | Full wireframe, both breakpoints |
| **Alta** | Passes and the guest buyer | `PASS-01`, `PASS-02` | Full wireframe, both breakpoints |
| **Media** | Marketplace product / order / inventory | `SHOP-02`, `SHOP-03`, `ADM-19` | Named in §7 with the structural rules; wireframes belong to the UI packet |
| **Media** | Courtesy passes, tickets, entry control | `ADM-15`, `ADM-16`, `ADM-20` | Named in §7 with the structural rules |
| **Media** | Sponsors | `ADM-21` | Named in §7 with the structural rules |

**Wireframe conventions used below**

- `▓` primary CTA · `░` secondary action · `[ ]` input · `▸` disclosure · `⋯` row menu · `●` verdict chip · `→` flow direction
- Solid boxes are **backend-owned** content; dotted boxes are **client-computed presentation only** (labels, ordering, formatting) — never a business rule.
- Every wireframe must be implementable with the shadcn candidates selected in `SH-04`.

---

## 1. `SPORT-01` — `/inscripcion`: the sports wizard

**Primary task:** a responsible person creates a registration and buys the initial cupos.
**Flow:** `FL-02` → `FL-03`. **Priority:** Alta.
**Key invariant:** a registration created but not paid must show **0 enabled cupos**, and reloading must not duplicate the registration (`QA-I01`).

### 1.1 Desktop (≥ 1024) — centred 640 px step, contextual summary rail

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ‹ Volver                                   Edición: Salesianos FEST 2026    │
├────────────────────────────────────────────┬─────────────────────────────────┤
│  STEP 1  ● Edición y paquete               │  RESUMEN (fijo, no sticky)      │
│  STEP 2  ○ Equipos                         │                                 │
│  STEP 3  ○ Cupos y resumen                 │  Paquete: Fútbol 7 · Senior     │
│  STEP 4  ○ Confirmación y compra           │  Condiciones: …                 │
│                                            │  Mínimo de compra: 8 cupos     │
│  ┌──────────────────────────────────────┐  │  Precio: 250.00 PEN   ← backend │
│  │ Paquete                             │  │  Beneficios incluidos: …        │
│  │ ● Fútbol 7 · Senior            [✓]   │  │  ─────────────────────────────  │
│  │ ○ Vóley 6 · Mixto                   │  │  PASOS SIGUIENTES              │
│  │ ○ultimate …                         │  │  1 Elegir paquete              │
│  │                                     │  │  2 Definir equipos              │
│  │ [Continuar ▓]  [Atrás]              │  │  3 Confirmar cupos              │
│  └──────────────────────────────────────┘  │  4 Pagar                        │
└────────────────────────────────────────────┴─────────────────────────────────┘
```

### 1.2 Mobile (360 / 390) — full-screen step, sticky footer CTA, progress visible

```
┌──────────────────────┐
│ ‹  Paso 1 de 4      │
│ ▓▓▓░░░░░░░░░░░░░░░░░ │  ← progress, current step announced
├──────────────────────┤
│ EDITOR Y PAQUETE     │
│                      │
│ ¿Qué paquete?        │
│                      │
│ ┌──────────────────┐ │
│ │ Fútbol 7 · Senior │ │
│ │ 8 cupos mínimo   │ │
│ │ 250.00 PEN    ✓  │ │  ← precio del backend, nunca calculado
│ └──────────────────┘ │
│ ┌──────────────────┐ │
│ │ Vóley 6 · Mixto   │ │
│ └──────────────────┘ │
│                      │
│ Condiciones ▸        │  ← disclosure, no nueva página
├──────────────────────┤
│ [ Continuar ▓      ] │  ← sticky, ≥44 px, no tapa contenido
└──────────────────────┘
```

**Intent notes**
- The step indicator is a **labelled** progress (`progress` component + step names), not a bare bar.
- The summary rail on desktop is read-only context; on mobile it collapses into a disclosure at the end of the flow.
- The CTA says what happens ("Continuar" → next step; the final step says "Crear inscripción y continuar al pago").
- **No step may ask for the whole roster before payment** if the approved flow allows assignment afterwards (plan `frontend/02` §SPORT-01).

---

## 2. `ACCOUNT-03` — `/mis-inscripciones/[id]`: the responsible person's detail

**Primary task:** understand the state of the registration and act on it (assign, move, add cupos).
**Priority:** Alta. **Key invariant:** after removing a player, the cupos balance updates and the purchase does not disappear (`QA-I04`).

### 2.1 Desktop (≥ 1024) — header + pool band + tabbed body

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Salesianos FEST 2026 · Fútbol 7 · Senior     ● Inscripción activa          │
│ Próxima acción: Asignar 2 participantes          [Agregar cupos ▓] [⋯]      │
├──────────────────────────────────────────────────────────────────────────────┤
│  CUPOS                                                                    │
│  ┌───────────────┬───────────────┬───────────────┐                         │
│  │ Pagados       │ Asignados     │ Disponibles   │  ← los TRES del backend  │
│  │ 10            │ 8             │ 2             │                         │
│  └───────────────┴───────────────┴───────────────┘                         │
│  «8 de 10 cupos asignados»  ← la misma información en prosa (a11y)          │
├──────────────────────────────────────────────────────────────────────────────┤
│ [ Resumen ] [ Equipos ] [ Pool y personas ] [ Compras de cupos ] [ Historial ]│
├──────────────────────────────────────────────────────────────────────────────┤
│  POOL Y PERSONAS                                                          │
│  [ Buscar por documento ] [ Agregar persona ▓]                              │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ Persona        │ Disciplina │ Estado          │ Acción            │   │
│  │ Ana Pérez      │ Fútbol 7   │ ● Asignada      │ [Quitar] [Mover]  │   │
│  │ Luis Ramírez   │ Fútbol 7   │ ● Sin asignar   │ [Asignar ▓]       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│  «No hay cupos deportivos disponibles» ← motivo del backend, no un 409    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Mobile (360 / 390) — pool band as a stacked trio, tabs become a scrollable segmented control

```
┌──────────────────────┐
│ ‹ Mis inscripciones  │
│                      │
│ Salesianos FEST 2026 │
│ Fútbol 7 · Senior    │
│ ● Inscripción activa │
│                      │
│ PÁGINA PAGOS ▓       │
│ [Agregar cupos ▓]    │
├──────────────────────┤
│ ┌──────────────────┐ │
│ │ 10 cupos pagados │ │
│ │ 8 asignados      │ │
│ │ 2 disponibles    │ │
│ └──────────────────┘ │
│ «8 de 10 asignados»  │
├──────────────────────┤
│ Resumen  Equipos  ⟨Pool⟩  Compras  Historial  ← scroll, no wrap
├──────────────────────┤
│ [ Buscar documento ] │
│ ┌──────────────────┐ │
│ │ Luis Ramírez     │ │
│ │ Fútbol 7         │ │
│ │ ● Sin asignar    │ │
│ │ [ Asignar ▓ ]    │ │
│ └──────────────────┘ │
└──────────────────────┘
```

**Intent notes**
- The pool is shown as **three labelled numbers** *and* as a sentence — a11y requirement A11Y-15 / SH-02 §2.3.
- "Quitar" is destructive → confirmation names the effect: *"Retirar a esta persona libera su cupo en esta inscripción; no genera devolución."*
- At 360 the table becomes one card per person, each carrying the column headers as inline labels (SH-02 §2.2, tables).

---

## 3. `ADM-14` — `/administracion/pagos`: admin payments, three separated levels

**Primary task:** understand and resolve a payment incidence.
**Priority:** Alta. **Key invariant:** one understandable verdict per row; the technical diagnosis is hidden by default (`QA-A01`); the `estado_operativo` filter is **mandatory** (`F-9`).

### 3.1 Desktop (≥ 1024) — list (level 1); detail opens a right panel (levels 2 and 3)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Pagos                                   Edición: [FEST 2026 ▾] [Actualizar]  │
├──────────────────────────────────────────────────────────────────────────────┤
│ [ Buscar… ] [Estado operativo ▾][Tipo ▾][Desde–Hasta] [Limpiar filtros]      │
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────┬──────────────────────┐ │
│ │ Compra   │ Concepto        │ Estado      │ ⋯      │ DETALLE              │ │
│ ├───────────────────────────────────────────────────┼──────────────────────┤ │
│ │ C-1042   │ Ampliación 5    │ ● Confirmado│ ⋯     │ ▸ Qué compró         │ │
│ │ C-1043   │ Pase FEST ×2    │ ● Verificando│ ⋯    │ ▸ Pago y estado      │ │
│ │ C-1044   │ Paquete Fútbol  │ ● Necesita   │ ⋯    │ ▸ Derechos otorgados │ │
│ │          │                │   atención   │      │                      │ │
│ │          │                │             │      │ ▸ Diagnóstico ▸      │ │
│ │          │                │             │      │   (oculto por defecto)│ │
│ └───────────────────────────────────────────────────┴──────────────────────┘ │
│ 1–25 de 143   ‹ ‹ 1 2 3 … 6 › ›      (page_size 25 · 1-based · D-06)        │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Mobile (360 / 390) — filter sheet + one verdict card per purchase

```
┌──────────────────────┐
│ ‹ Pagos        [Filtros]│
├──────────────────────┤
│ C-1042               │
│ Ampliación 5 cupos   │
│ ● Pago confirmado    │
│ Comprador: A. Pérez  │
│ 250.00 PEN           │
│ [Ver detalle ▓]      │
├──────────────────────┤
│ C-1043               │
│ Pase FEST ×2         │
│ ● Verificando pago   │
│ [Ver detalle ▓]      │
├──────────────────────┤
│ C-1044               │
│ Paquete Fútbol       │
│ ● Necesita atención  │
│ [Ver detalle ▓]      │
└──────────────────────┘
        ▓ filtro sheet overlay (modal, foco atrapado)
```

**Intent notes**
- The filter sheet at 360 is a modal drawer with focus trap and restore (A11Y-08).
- The three levels are **three separate disclosures**, never one merged wall of provider fields.
- "Aprobación manual" is **never** a ubiquitous button: it appears only inside the relevant record and only when `acciones_disponibles` permits it.
- The verdict chip = colour + icon + backend `etiqueta` text (A11Y-11).

---

## 4. `ADM-07` / `ADM-08` — admin teams: list and drilldown

**Primary task:** find why a team cannot compete and fix it.
**Priority:** Alta (redesign priority — the frozen system has **no** drilldown).
**Key invariant:** the reason comes from the backend; the client does not infer incompleteness.

### 4.1 Desktop (≥ 1024)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Equipos                                     [Competencia ▾][Estado ▾][q]   │
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────────────────┐ │
│ │ Equipo      │ Disciplina · Cat │ Plantilla  │ Estado              │ ⋯ │ │
│ ├────────────────────────────────────────────────────────────────────────┤ │
│ │ Equipo Norte│ Fútbol 7 · Senior│ 6 / 7–10  │ ● Falta 1 jugador   │ ⋯ │ │
│ │             │                  │            │ para competir       │   │ │
│ │ Rival Sur   │ Fútbol 7 · Senior│ 9 / 7–10  │ ● Listo             │ ⋯ │ │
│ │             │                  │            │                    │   │ │
│ └────────────────────────────────────────────────────────────────────────┘ │
│                                        «Ver equipo» is a real link per row │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 `ADM-08` detail — mobile first (360 / 390)

```
┌──────────────────────┐
│ ‹ Equipos             │
│                      │
│ EQUIPO NORTE         │
│ Fútbol 7 · Senior    │
│                      │
│ ┌──────────────────┐ │
│ │ ● Falta 1 jugador│ │
│ │   para competir  │ │
│ │   (motivo del    │ │
│ │    backend)      │ │
│ └──────────────────┘ │
│                      │
│ PLANTILLA 6 / 7–10   │
│ ┌──────────────────┐ │
│ │ Ana Pérez   ●    │ │
│ │ Luis R.     ●    │ │
│ │ Carla M.    ●    │ │
│ │ + 3 más          │ │
│ └──────────────────┘ │
│                      │
│ INSCRIPCIÓN          │
│ Inscripción #231     │
│ Cupos: 2 disponibles │
│                      │
│ [Agregar jugador ▓]  │
└──────────────────────┘
```

**Intent notes**
- The "why" is a **sentence from the backend** (`estado_operativo.etiqueta` + `.descripcion`), not a badge.
- Numbers "6 / 7–10" must be accompanied by a sentence for screen readers.
- "Agregar jugador" opens the shared person-resolution sheet (a `drawer`, not a page), reusing the `RT-ID-01/02/03` flow.

---

## 5. `ADM-11` / `ADM-12` / `ADM-13` — competitions: detail, bracket, agenda

**Primary task:** run the competition (schedule, results, advance, correct).
**Priority:** Alta.
**Key invariants:** *preview does not write, confirm does* (`QA-K04`); corrections show impact and require a reason (`QA-K03`); a version conflict never silently applies stale changes.

### 5.1 `ADM-12` bracket — desktop (≥ 1024) and mobile (360 / 390)

```
DESKTOP
┌──────────────────────────────────────────────────────────────────────────────┐
│ Cuadro · Copa Fútbol 7                [Ronda ▾] [Vista previa ▓]            │
├───────────────┬───────────────┬───────────────┬─────────────────────────────┤
│ Octavos       │ Cuartos       │ Semifinal     │ Final                        │
│ ┌───────────┐ │ ┌───────────┐ │ ┌───────────┐ │ ┌───────────┐               │
│ │ Norte 2-1 │ │ │ Norte 3-1 │ │ │ Norte 4-2 │ │ │ ¿Final?   │  ← sin definir │
│ │ ▓ Abrir   │ │ │ ▓ Abrir   │ │ │ ▓ Abrir   │ │ │           │               │
│ └───────────┘ │ └───────────┘ │ └───────────┘ │ └───────────┘               │
│ ┌───────────┐ │ ┌───────────┐ │               │                              │
│ │ Rival 0-0 │ │ │ Rival 2-3 │ │               │                              │
│ └───────────┘ │ └───────────┘ │               │                              │
└───────────────┴───────────────┴───────────────┴─────────────────────────────┘

MOBILE (360/390)
┌──────────────────────┐
│ ‹ Cuadro              │
│ [Ronda ▾]             │
├──────────────────────┤
│ ◀ Octavos │ Cuartos ▶ │  ← scroll horizontal CONTAINER
│ ┌───────────┐         │    (no page overflow)
│ │ Norte 2-1 │         │
│ │ ▓ Abrir   │         │
│ └───────────┘         │
│ ┌───────────┐         │
│ │ Rival 0-0 │         │
│ └───────────┘         │
├──────────────────────┤
│ Rondas: ● ○ ○ ○       │  ← indicadores de ronda
└──────────────────────┘
```

### 5.2 `ADM-11` match detail — the reusable panel

```
DESKTOP — panel lateral (drawer, lado derecho)
┌────────────────────────────────────────────────────────────┐
│ ◀ Encuentro #12        Copa Fútbol 7 · Cuartos           │
│────────────────────────────────────────────────────────────│
│ ● Programado — 21/11 18:00 (hora local de la edición)    │
│                                                            │
│ PARTICIPANTES                    │ RESULTADO              │
│  Equipo Norte  ● Confirmado      │  Norte 2 — 1 Rival    │
│  Rival Sur    ● Confirmado       │  [Registrar resultado]│
│                                                            │
│ SECUENCIA DE AVANCE                                     │
│  Ganador → Cuartos slot #3                                │
│  [Ver vista previa del avance ▓]  [Confirmar avance]      │
│                                                            │
│ HISTORIAL DE CORRECCIONES                                 │
│  14/11 — resultado corregido (motivo: score mal registrado)│
└────────────────────────────────────────────────────────────┘

MOBILE — bottom drawer, altura 90vh, foco atrapado y restaurado
┌──────────────────────┐
│ Encuentro #12    [×] │
│ Copa Fútbol 7        │
│ ● Programado         │
│                      │
│ Norte 2 — 1 Rival    │
│                      │
│ [Ver vista previa ▓] │
│ [Confirmar avance]   │
└──────────────────────┘
```

**Intent notes**
- The match detail is **one** reusable panel opened from list, agenda and bracket — no divergent editors (`frontend/05` §3).
- Every action states its **consequence**: "Ganador registrado: Equipo Norte"; "La corrección afecta a 2 encuentros posteriores".
- A version conflict shows "Los datos cambiaron. Actualiza y revisa antes de guardar." and **does not** apply the stale mutation.
- The bracket never computes winners; it renders what the backend returns.

---

## 6. `PASS-01` / `PASS-02` — passes and the guest buyer

**Primary task (PASS-01):** buy party passes without an account. **Primary task (PASS-02):** assign those passes without an account.
**Priority:** Alta. **Key invariants:** closing the checkout does not delete the purchase; beneficiaries are never assigned over an unpaid purchase; a DNI alone never grants access to someone else's purchase (`QA-U03`).

### 6.1 `PASS-01` — mobile (360 / 390)

```
┌──────────────────────┐
│ ‹ Pases                │
│                      │
│ PASE FEST 2026        │
│ 35.00 PEN             │  ← backend
│                      │
│ Cantidad              │
│ [ − ]  2  [ + ]      │  ← stepper ≥44 px, anuncia el valor
│                      │
│ ┌──────────────────┐ │
│ │ Comprador        │ │
│ │ [Tipo ▾]         │ │
│ │ [Nº documento  ] │ │
│ │ [correo         ] │ │
│ └──────────────────┘ │
│                      │
│ El comprador y los    │  ← copy explains the model
│ asistentes pueden     │
│ ser distintas personas│
│                      │
│ Total: 70.00 PEN      │
├──────────────────────┤
│ [ Continuar al pago ] │  ← CTA sticky
└──────────────────────┘
```

### 6.2 `PASS-01` — desktop (≥ 1024)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Pases                                                                      │
├─────────────────────────────────────────────┬───────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │  RESUMEN                     │
│ │ Pase FEST 2026                          │ │  2 × 35.00 = 70.00 PEN       │
│ │ Entrada individual de fiesta            │ │  ─────────────────────────   │
│ │ 35.00 PEN                    [Cantidad 2]│ │  Comprador                   │
│ └─────────────────────────────────────────┘ │  Tipo  [DNI ▾]              │
│ ┌─────────────────────────────────────────┐ │  Documento [__________]      │
│ │ Pase VIP                                 │ │  Correo   [__________]      │
│ │ 60.00 PEN                    [Cantidad 1]│ │  ─────────────────────────   │
│ └─────────────────────────────────────────┘ │  [ Continuar al pago ▓ ]     │
└─────────────────────────────────────────────┴───────────────────────────────┘
```

### 6.3 `PASS-02` — `/pases/gestionar/[token]` — guest management

```
┌──────────────────────┐
│ ‹ Pasas              │
│                      │
│ TU COMPRA            │
│ Pase FEST 2026 ×2    │
│                      │
│ ┌──────────────────┐ │
│ │ 2 acquired       │ │
│ │ 1 assigned       │ │
│ │ 1 pending        │ │
│ └──────────────────┘ │
│                      │
│ BENEFICIARIOS        │
│ ┌──────────────────┐ │
│ │ Ana Pérez        │ │
│ │ ● Entrada activa │ │
│ │ [Quitar ▓]       │ │
│ └──────────────────┘ │
│ ┌──────────────────┐ │
│ │ [Agregar persona]│ │
│ │ Tipo [DNI ▾]      │ │
│ │ Documento [_____] │ │
│ │ [Resolver ▓]      │ │
│ └──────────────────┘ │
└──────────────────────┘
```

**Intent notes**
- The three counters (adquiridos · asignados · pendientes) come from the backend.
- The access-denied state is **neutral**: "El enlace no está vigente o no corresponde a esta compra." — it never reveals whether a purchase exists.
- Revocation (per `PD-02`) is an irreversible action → `alert-dialog` naming the effect.
- "Esta persona ya tiene una entrada activa para esta edición" is the backend's `PASE_BENEFICIARIO_DUPLICADO` message, rendered verbatim (SH-03 §6).

---

## 7. Media-Priority Structural Rules (no full wireframes in this packet)

| Route | Structural rule that the wireframe must respect |
|---|---|
| `SHOP-02` | Gallery is a keyboard-operable `carousel` with descriptive alt text; price/offer pair is one block; availability is the backend's; "Comprar" is the only primary action. |
| `SHOP-03` | Order state shows payment state **and** delivery state as two separate facts. A paid order that was not delivered must not read as "delivered" (`QA-M04`). |
| `ADM-19` | Stock movements are a ledger (actor, type, quantity, reason, instant). An administrative exit creates **no** purchase. |
| `ADM-15` | Courtesy passes are visibly distinguished from purchased passes by their origin, and revocations are shown with their audit reason. |
| `ADM-16` | **Preview does not consume.** Reading a QR shows a preview of the right; confirming the entry is a separate, deliberate action. Manual code entry is always present. |
| `ADM-20` | Delivery has the same preview/confirm separation as entry validation, plus a double-redemption guard. |
| `ADM-21` | Ordered image gallery, descriptive alt text, edition relationship, visibility. No monetary fields. |

---

## 8. What This Document Deliberately Does Not Contain

- No JSX, TSX, CSS, Tailwind classes or component code.
- No invented endpoints or URLs — every data dependency points at `SH-05`, where all 78 routes are marked provisional.
- No invented prices, cupos, roster sizes or availability. Every number in the wireframes is a **placeholder slot** fed by the backend.
- No stock screenshots or image assets.
- No motion specification beyond what `SH-01` §3.7 constrains.

---

## 9. Acceptance Criteria For This Document

- [x] All six **Alta** priority flows have both a mobile and a desktop wireframe intent.
- [x] The Media-priority routes have explicit structural rules.
- [x] Each wireframe shows states that map to the ten required states of `SH-03`.
- [x] Every backend-owned value is marked as such; no business rule appears in the client layout.
- [x] The five mandatory widths are addressed per flow (360 / 390 / 768 / 1024 / 1440).
- [x] Accessibility requirements are visible in the wireframes (labels, focus, touch size, tab semantics, verdict chips with text).
- [x] No implementation code was produced.
