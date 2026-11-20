# UI-03 - Pass, Shop, Guest Order And Checkout Skeletons

**Artifact:** `evidence/ui/UI-03-commerce-shells.md` - **Packet:** UI-03 (`wave-02-frontend-skeletons`)
**Owner:** A7 - **Status:** `verification_required` (implementation applied, runtime verification deferred)
**Date:** 2026-11-19 - **Target:** `Aplicacion/frontend/**` only
**Packet:** `Aplicacion/task/salesianos-fest-rebuild/wave-02-frontend-skeletons/UI-03-commerce-shells.md`

---

## 1. Scope actually applied

The packet names five page IDs. All five were applied, in two NEW features
that did not exist before this packet (`features/pases/**` and
`features/marketplace/**`).

| Page ID | Route | Route file | Feature view | State |
|---|---|---|---|---|
| `PASS-01` | `/pases` | `app/(public)/pases/page.tsx` (modified) | `features/pases/views/PasesView.tsx` | **applied** |
| `PASS-02` | `/pases/gestionar/[token]` | `app/(public)/pases/gestionar/[token]/page.tsx` (modified) | `features/pases/views/PaseGestionarView.tsx` | **applied** |
| `SHOP-01` | `/tienda` | `app/(public)/tienda/page.tsx` (modified) | `features/marketplace/views/TiendaCatalogoView.tsx` | **applied** |
| `SHOP-02` | `/tienda/[slug]` | `app/(public)/tienda/[slug]/page.tsx` (modified) | `features/marketplace/views/ProductoDetalleView.tsx` | **applied** |
| `SHOP-03` | `/tienda/pedidos/[token]` | `app/(public)/tienda/pedidos/[token]/page.tsx` (modified) | `features/marketplace/views/PedidoSeguimientoView.tsx` | **applied** |

`REC-01` (`/recuperar-compra`) is **UI-01** and was not touched.
---

## 2. The route brief applied

The briefs were produced by **GOV-02** and were read before any code was written:

- `evidence/routes/RB-02-commerce-passes-store.md` -> `PASS-01`, `PASS-02`,
  `SHOP-01`, `SHOP-02`, `SHOP-03` (and `REC-01`, which is UI-01).
- `evidence/routes/SH-01` (tokens) - `SH-02` (five widths + a11y) - `SH-03`
  (ten states) - `SH-04` (shadcn families) - `SH-05` (provisional endpoints) -
  `SH-06` (wireframes).
- `evidence/domains/DOM-03` (passes), `DOM-04` (catalogue and media),
  `DOM-05` (order), `DOM-06` (inventory, reservation and delivery) - the
  PRESENTERS of the target were read directly from
  `Aplicacion/backend/modules/**` to mirror their shapes 1:1.
- `Aplicacion/plan/salesianos-fest-rebuild/frontend/03-paginas-comerciales.md`
  (the five page briefs and the shared payment component).

### The transversal rule that decided the composition (`D-UI03-01`)

> **There is no mixed cart.** Each module keeps its own checkout. Only the
> payment VISUAL and the order state are shared (`frontend/03`; `GOV-02-RB-02a`).

So the packet produced **two independent features** with **two independent
checkouts**. No component of `features/pases/**` imports anything of
`features/marketplace/**` and the other way round.

### The rule that decided the honesty of the states (`D-UI03-02`)

> **A provisional fixture may render the configuration of the PRODUCT; it may
> never render the PERSONAL data of the reader, and it may never reach a
> route.**

Every route of this packet renders the **honest state** by default
(`sin-datos`): the catalogue is not connected, the payment gateway is not
connected and the order controller is not registered. The populated
compositions are implemented, typed and exercised by the suites; they are the
code that **API-03** binds to the real presenters.
---

## 3. shadcn candidate comparison (GOV-02-SH-01 re-run for this family)

The MCP was executed for this family, not inherited:

| # | Tool call | Result |
|---|---|---|
| 1 | `shadcn_get_project_registries` | `@shadcn` (the target registry) |
| 2 | `shadcn_search_items_in_registries` - card | `card` (registry:ui) + `hover-card` |
| 3 | `shadcn_search_items_in_registries` - carousel | `carousel` (registry:ui) |
| 4 | `shadcn_search_items_in_registries` - dialog | `dialog` (registry:ui) + `alert-dialog` |

| Item | Registry | Fit for this family | Local state | Decision |
|---|---|---|---|---|
| `dialog` / `dialog-close` | `registry:ui` | The two checkouts: the buyer form of the passes and the order of the store | **present** | **Selected / reused**. The `DialogContent` close button is disabled (`showCloseButton={false}`) and the dialog carries its own Spanish "Cerrar": the primitive's own label is "Close". |
| `alert-dialog` | `registry:ui` | The irreversible revocation of a right of entry | **present** | **Selected / reused** (`DialogoRevocar`) |
| `carousel` | `registry:ui` | The gallery of `ProductoImagen` | **present**, but its `CarouselPrevious` / `CarouselNext` ship the English screen-reader labels "Previous slide" / "Next slide", and `components/ui/**` is a FORBIDDEN root | **Rejected for the gallery**: the gallery of the store is composed in the feature with the local `button` primitive, with Spanish accessible names. Recorded as `A0-UI03-01`. |
| `card` | `registry:ui` | The product card | **present** | **Not used as the card**: the local `Item` primitive (`item.tsx`) is the row density the account area already uses, and the card of the product needs a media well. The card is composed in the feature. |
| `table` | `registry:ui` | The lines of an order | **present** | **Not used**: the order has a handful of lines and the brief asks for rows that read as a sentence at 360. The lines are a list. |
| `badge` | `registry:ui` | The offer and the availability | **present**, with the known typo in the `secondary` variant and no verdict variants | **Rejected for the verdict chips**: the payment chip is **composed** in the feature layer (icon shape + backend label + semantic bucket), because the local `badge` has no `success` / `warning` / `info` variants. **Shared primitive untouched.** |
| `item` | `registry:ui` | The rows of the beneficiaries and of the products | **present** | **Selected / reused** (`ListaBeneficiarios`) |
| `alert` | `registry:ui` | S-04, S-09 and the outcomes of the forms | **present** | **Selected / reused** |
| `empty` | `registry:ui` | S-02 and S-03 | **present** | **Selected / reused** through `RouteEmptyState` |
| `skeleton` | `registry:ui` | S-01 | **present** | **Not used**: the route files of this packet have no `loading.tsx` (the shell owns the group boundary). See `D-UI03-06`. |
| `input` + `label` | `registry:ui` | The fields of the buyer form and the quantity | **present** | **Selected / reused** |
| `select` | `registry:ui` | The type of the civil document | **present** | **Selected / reused** |
| `field` | `registry:ui` | The new form primitive | absent | **Rejected** - `GOV-02-SH-03`: `field` must not enter the `GenericForm` wrapper path without proving there is no double render of label/error. The buyer form uses `GenericForm` Mode 1 (`children`) and draws its own label/error once, per `contract/smart.md` 5.2. |

**No component was added. No file in `components/ui/**` was created, modified
or overwritten.**
---

## 4. The ten states, route by route

| State | `PASS-01` | `PASS-02` | `SHOP-01` | `SHOP-02` | `SHOP-03` |
|---|---|---|---|---|---|
| S-01 initial / loading | the route shows the honest state; the shell owns the group boundary | idem | idem | idem | idem |
| S-02 empty | "No hay pases a la venta en esta edición" | "Todavía no hay ninguna entrada asignada" | "No hay productos publicados en esta edición" | idem | "Este pedido todavía no se puede mostrar" |
| S-03 filtered-empty | not applicable (no filters) | not applicable | "No hay productos en esta categoría" + "Quitar el filtro" | not applicable | not applicable |
| S-04 recoverable error | `ShellErrorState` "No pudimos cargar el catálogo de pases" | `ShellErrorState` "No pudimos comprobar tu enlace" | `ShellErrorState` "No pudimos cargar el catálogo de la tienda" | `ShellErrorState` "No pudimos cargar este producto" | `ShellErrorState` "No pudimos comprobar tu enlace" |
| S-05 validation | the buyer form: Zod, a summary `role="alert"` with focus, `aria-invalid` / `aria-describedby` | the beneficiary form (see `D-UI03-05`) | the quantity bounds are the server's | the quantity bounds are the server's | not applicable |
| S-06 permission | `ShellPermissionDenied` (declared: the route is public, the state exists for the edition scope) | the **neutral denial**: the SAME message for an expired link, a link of somebody else and a wrong document | `ShellPermissionDenied` | `ShellPermissionDenied` | the **neutral denial**, identical for every reason |
| S-07 success | "Compra registrada" (the form's own outcome) | the assignment is acknowledged by the list | the detail opens | the order opens | the state is shown |
| S-08 in progress | the button is disabled and says "Enviando…"; no invented duration | idem | "Creando el pedido" | idem | not applicable |
| S-09 partial / indeterminate | the payment verdict "Pago confirmado, pendiente de activación" | idem | idem | idem | the payment line and the delivery line are two facts |
| S-10 irreversible confirmation | not applicable | `DialogoRevocar` names the effect: "Revocar la entrada la deja sin efecto y queda registrada en la auditoría. No genera devolución ni devuelve el pase al lote" | not applicable | not applicable | not applicable |
| payment states | the five states of `SH-03` 3 are rendered by `EstadoPagoPase` | idem | the five states are rendered by `EstadoPagoTienda` | idem | the payment line uses `EstadoPagoTienda` |
| paid vs delivered | not applicable | not applicable | not applicable | not applicable | **two labelled rows**: "Pago" and "Entrega"; a paid order that is not delivered never reads as "Entregado" (`QA-M04`) |
| recoverable close | the checkout dialog: "Si cierras esta ventana, la compra no se borra" | not applicable | the checkout dialog: "Si cierras esta ventana, el pedido no se borra" | idem | not applicable |

**The five presentable payment states** (`frontend/03`, `SH-03` 3) are the
only payment vocabulary of the packet: `pendiente`, `verificando`,
`confirmado`, `sin-confirmar` and `atencion`. The client NEVER derives a
payment state from a modal close or a timeout (`GOV-02-RB-02d`): it draws the
verdict it is given, with the label of the backend.
---

## 5. Provisional fixtures (FR-08)

Every fixture is **local to its feature**, **typed with `satisfies`**, **marked**
and **exported from no production barrel**.

| Fixture (symbol) | Mirrors | Contract | Path | Deleted in |
|---|---|---|---|---|
| `estadoPagoPendienteFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | `features/pases/fixtures/pase.fixture.ts` | **API-03** |
| `estadoPagoVerificandoFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | idem | **API-03** |
| `estadoPagoConfirmadoFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | idem | **API-03** |
| `estadoPagoSinConfirmarFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | idem | **API-03** |
| `estadoPagoAtencionFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | idem | **API-03** |
| `paseCatalogoFixture` | `PaseOut` (DOM-03, `RT-PS-01`) | `FREEZE-PS-1.0.0` | idem | **API-03** |
| `catalogoPasesFixture` | `PaseCatalogoOut` | `FREEZE-PS-1.0.0` | idem | **API-03** |
| `catalogoPasesVacioFixture` | `PaseCatalogoOut` (empty) | `FREEZE-PS-1.0.0` | idem | **API-03** |
| `beneficiarioPaseFixture` | `PaseBeneficiarioOut` | `FREEZE-PS-1.0.0` | idem | **API-03** |
| `compraPasesFixture` | `PaseCompraDetalleOut` | `FREEZE-PS-1.0.0` | idem | **API-03** |
| `estadoPagoPendienteFixture` .. `estadoPagoAtencionFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | `features/marketplace/fixtures/marketplace.fixture.ts` | **API-03** |
| `categoriaProductoFixture` | `CategoriaListaOut` (DOM-04, `RT-MK-01`) | `FREEZE-PS-1.0.0` | idem | **API-03** |
| `productoListItemFixture` | `ProductoListItemOut` (DOM-04, `RT-MK-02`) | `FREEZE-PS-1.0.0` | idem | **API-03** |
| `productoDetalleFixture` | `ProductoDetalleOut` (DOM-04, `RT-MK-03`) | `FREEZE-PS-1.0.0` | idem | **API-03** |
| `seguimientoPedidoFixture` | `PedidoSeguimientoOut` (DOM-05, `RT-MK-04`) | `FREEZE-CM-1.0.0` | idem | **API-03** |
| `estadoEntregaPedidoFixture` | `EstadoEntregaPedido` (DOM-05) | `FREEZE-CM-1.0.0` | idem | **API-03** |

**Rules honoured:** the literal token `PROVISIONAL_CONTRACT_FIXTURE` is in the
header of each file and the symbol name carries the `Fixture` suffix - no
business calculation, no `if`, no arithmetic, no `Date.now()` / `Math.random()`
/ `crypto.randomUUID()`, no price, no availability, no payment state and no
permission is DERIVED. The amounts are `0` on purpose (`FR-08` 2.4), so an
example amount can not look like a real price.

**No fixture is exported from a production barrel.** The fixtures are consumed
only by the suites of their feature.
---

## 6. Files changed (32 created, 5 modified, 0 deleted)

All of them are inside the allowed roots of the packet.

**Route presentation - modified (5)**

- `app/(public)/pases/page.tsx`
- `app/(public)/pases/gestionar/[token]/page.tsx`
- `app/(public)/tienda/page.tsx` - reads `searchParams` and hands the
  category to the view.
- `app/(public)/tienda/[slug]/page.tsx`
- `app/(public)/tienda/pedidos/[token]/page.tsx`

**Feature `pases` - created (19)**

- `types/pase.types.ts`
- `utils/monto.ts`
- `schemas/comprador-pase.schema.ts`
- `fixtures/pase.fixture.ts`
- `components/EstadoPagoPase.tsx` · `components/TarjetaPase.tsx` ·
  `components/SelectorCantidad.tsx` · `components/ResumenCompra.tsx` ·
  `components/FormularioComprador.tsx` · `components/DialogoCheckout.tsx` ·
  `components/CatalogoPases.tsx` · `components/ContadoresPases.tsx` ·
  `components/ListaBeneficiarios.tsx` · `components/DialogoRevocar.tsx` ·
  `components/index.ts`
- `views/PasesView.tsx` · `views/PaseGestionarView.tsx` · `views/index.ts`
- `__tests__/pases-estados.test.tsx`

**Feature `marketplace` - created (13)**

- `types/marketplace.types.ts`
- `utils/monto.ts`
- `fixtures/marketplace.fixture.ts`
- `components/EstadoPagoTienda.tsx` · `components/TarjetaProducto.tsx` ·
  `components/GaleriaProducto.tsx` · `components/DialogoCheckoutTienda.tsx` ·
  `components/index.ts`
- `views/TiendaCatalogoView.tsx` · `views/ProductoDetalleView.tsx` ·
  `views/PedidoSeguimientoView.tsx` · `views/index.ts`
- `__tests__/marketplace-estados.test.tsx`

**Not touched:** `src/components/shell/**` · `src/components/ui/**` ·
`src/app/globals.css` · `src/providers/**` · `src/lib/**` · `src/hooks/**` ·
`src/shared/**` · `src/features/{auth,portada,inscripciones,admin,theme,cuenta,public}/**`
· the backend · `contract/**` · the root `frontend/**`.
---

## 7. Skills loaded

| Order | Skill | Use in this packet |
|---|---|---|
| 1 | `salesianos-ui-ux` | Route purpose, actors, actions, states, the visual direction of `SH-01` and the semantic roles |
| 2 | `salesianos-feature-architecture` | Layer boundaries: thin pages, views own the composition, components own the presentation, types separate from the fixtures, no business logic in a page |
| 3 | `salesianos-forms-smart-fields` | The buyer form: `GenericForm` Mode 1 (`children`), Zod owns the validation, the label and the error of a field are drawn ONCE, `useWatch`/`useController` only for the named field |
| 4 | `salesianos-shadcn` | The MCP comparison of section 3, the reuse of the local primitives, the refusal to recreate a registry component, the hardcoded-colour audit |
| 5 | `salesianos-responsive-a11y` | The five-width contract, the 44 px targets, the labels and the live regions, the focus-managed error summary |
| 6 | `frontend-design` | The restraint: one memorable element per surface, copy that says one thing, errors that name the cause and the fix |

`salesianos-api-data` was **not** loaded: this packet creates **no transport**.
The forbidden roots of the packet list the network hooks, the wire schemas, the
query keys and `src/lib/**`.

---

## 8. Commands run, exit codes and results

**The only runtime command of this packet was the typecheck.** Everything else
was forbidden by the launch contract.

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| 1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 15 errors, all of them JSX structure errors in `ProductoDetalleView.tsx` (an edit had replaced the closing tag of the category paragraph) |
| 2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | clean, after the repair of the file and of the accent restoration of the store |
| 3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | clean, after the two suites were written |
| 4 | `git status --short -- Aplicacion/frontend/src/features/pases ...` | repo root | **0** | 2 untracked trees (the two new features) |
| 5 | `git status --short -- "Aplicacion/frontend/src/app/(public)"` | repo root | **0** | the 5 route files modified by this packet; the other lines were already modified by a concurrent agent and were NOT touched |

**NOT RUN** (forbidden by the launch contract, and recorded as deferred, never
as passed): `vitest` · `biome check` · `next build` · `npm install` · any
server · any browser · any visual automation · `git stash` · `git commit` ·
`git reset` · `git checkout`.

**Known baseline failures:** none introduced. The 15 type errors of command 1
were introduced by this packet and were fixed in this packet.
---

## 9. Tests written (NOT executed) and the five widths

The standing user preference (#11299) is that the suites of an apply packet are
**written** and **not executed**, and the packet status is
`verification_required`. The suites below were written and **have never run**:
nothing here may be read as a green result.

| Suite | Environment | What it freezes |
|---|---|---|
| `features/pases/__tests__/pases-estados.test.tsx` | jsdom | `PASS-01`: the honest empty, the recoverable error, the populated catalogue, the empty catalogue. `PASS-02`: the honest state, the NEUTRAL denial (it never says whether the purchase exists), the three counters and the list of persons, and the **five** presentable payment states with the label of the backend (and never the code) |
| `features/marketplace/__tests__/marketplace-estados.test.tsx` | jsdom | `SHOP-01`: the honest empty, the recoverable error, the empty catalogue, the filtered-empty with "Quitar el filtro" and the product card. `SHOP-02`: the honest state, the gallery position and the keyboard controls, the price of the server and the ABSENCE of a computed total. `SHOP-03`: the honest state, the neutral denial and the rule that a paid order which is not delivered never reads as "Entregado" |

Both suites also freeze the static rules of the area: **no literal colour**
(T-01), **no palette utility of a raw tone**, and the **44 px** targets of the
actions.

### The five widths

The audit at 360, 390, 768, 1024 and 1440 was **deferred**: no browser was run
in this packet. What the markup already guarantees, and what the browser pass
will have to confirm:

| Width | What the composition does | What is still unverified |
|---|---|---|
| 360 | One column. The catalogue of the passes is a single column of cards; the summary and the call to action are below the options. The gallery is a single image with the previous/next controls and the thumbnails below. Every action is at least 44 px high. | That no page overflows horizontally, that the sticky header does not cover the first action, that the long product names truncate |
| 390 | The same single column. | The same |
| 768 | The product grid is two columns; the detail of the product is still a single column capped by the band of the page; the passes keep the options above and the summary below | That the two columns do not squeeze the cards |
| 1024 | The passes are two columns (options + summary). The detail of the product is the gallery at 60% and the information at 40%. The grid of the store is three columns | That no column is stretched and that nothing is clipped |
| 1440 | The grid of the store is four columns and the content band is capped by the shell | The same |

### Accessibility that was decided in the markup

- Every input has a real `<label>` and its error is associated with
  `aria-describedby`.
- The summary of the errors of the form is a `role="alert"` with
  `tabIndex={-1}`, so it receives the focus after an invalid submit.
- The quantity stepper announces its value in a live region, and its two
  buttons have an accessible name.
- The gallery announces "Imagen N de M" in a live region, its two controls have
  accessible names and its thumbnails are buttons with `aria-current`.
- The verdict chip pairs an icon shape, the backend label and the semantic
  bucket: the colour never carries the meaning alone.
- The counters of `PASS-02` live in one `<dl>`, so a screen reader reads them
  as a sentence.
- The payment state and the delivery state of `SHOP-03` are **two labelled
  rows** of one `<dl>`.

**Residual gaps declared, never assumed green:** no browser rendering, no
screen-reader pass, no 200 % zoom reflow, no automated axe or Lighthouse run,
and the suites themselves have never been executed.
---

## 10. Deviations, decisions and A0 requests

| ID | Type | What |
|---|---|---|
| `D-UI03-01` | decision | **Two features, two checkouts, no shared cart.** `features/pases/**` and `features/marketplace/**` do not import each other. The shared checkout COMPONENT is an A0 request (the packet says the shared component goes through A0), so the five payment states are composed twice, once per feature, with the same semantics and the same copy. |
| `D-UI03-02` | decision | **A provisional fixture never reaches a route.** Every route of the packet renders the honest state by default; the populated compositions are exercised by the suites and are the code that API-03 binds. |
| `D-UI03-03` | decision | **The money is a NUMBER.** The target presenters type the amounts as `Decimal` and the target serialises them as a float (`Aplicacion/backend/core/types.py` -> `BaseSchema.ser_json_decimal_to_float`), so the view models declare `number` and not the string of `FR-08` 2.4 (that example mirrors a plan presenter that does not exist in the target). The amount is printed with the two decimals of the currency and with NO locale. |
| `D-UI03-04` | decision | **The state travels with its label.** `PaseBeneficiarioOut.estado`, `PaseBeneficiarioOut.estado` of the purchase and `PedidoSeguimientoOut.estado_pago` / `estado_entrega` publish a machine CODE and no wording. The interface never shows a code (`SH-03` 6), so the ADAPTER resolves the label and both travel together (`estado_etiqueta`, `EstadoDeclarado`). Same rule as `D-UI01-02`. |
| `D-UI03-05` | deviation | **The assignment form of `PASS-02` was NOT built.** The action exists in the brief of `PASS-02`, but it binds to `RT-PS-05` of a domain (`DOM-03`) that is still `verification_required`, and the assignment needs the transport that API-03 brings. The route shows the summary, the three counters, the list of persons and the revocation, and the assignment is declared here as owed. |
| `D-UI03-06` | deviation | **No `loading.tsx` of the packet.** S-01 is owned by the group boundary of the shell (`app/(public)/loading.tsx`), which is a forbidden root of this packet. |
| `D-UI03-07` | deviation | **The store checkout does NOT collect the identity of the buyer.** The payload of the order (`CrearPedidoIn`, DOM-05) declares ONLY the items: asking for a document here would be inventing a field the backend does not accept. |
| `D-UI03-08` | deviation | **The currency of the store is not declared.** `ProductoEspecificaOut` has no currency field, so the card receives it as an optional prop and prints the amount alone when it is absent, instead of guessing one. |
| `D-UI03-09` | deviation | **The stock of the product is not in the product wrapper.** It belongs to the inventory (`DOM-06`, `RT-MK-08..12`, NOT registered), so the card receives the reason of the block as a prop and DISABLES the call to action with a written reason. |

### A0 requests

| ID | Request |
|---|---|
| `A0-UI03-01` | The local `components/ui/carousel.tsx` ships the English screen-reader labels "Previous slide" and "Next slide". The gallery of the store was composed in the feature to avoid it, but the primitive should be localised. `components/ui/**` is a forbidden root of this packet. |
| `A0-UI03-02` | `PedidoController` and `InventarioController` are implemented but **NOT registered** in `Aplicacion/backend/config/api.py`. Until they are, `POST /marketplace/pedidos` and `GET /marketplace/pedidos/{token}` do not exist: `SHOP-02` cannot create an order and `SHOP-03` cannot read one. |
| `A0-UI03-03` | `ProductoEspecificaOut` publishes no currency and no stock. The store needs both before the card can show a price and an availability. |
| `A0-UI03-04` | `PaseBeneficiarioOut.estado` and `PedidoSeguimientoOut.estado_pago` / `estado_entrega` publish a code and no wording. Either the presenters publish the label, or the frontend adapter owns the dictionary. |
| `A0-UI03-05` | The five presentable payment states are composed twice, once per feature. The shared checkout component of `frontend/03` should live in a common place; `components/shell/**` is a forbidden root of this packet. |
| `A0-UI03-06` | `00-matriz-tareas.md` does not carry a row for UI-03 and the matrix is a forbidden root: the row has to be synchronised by the coordinator. |
---

## 11. API-03 handoff

### The seams that API-03 has to bind

| Seam | Where | What API-03 does |
|---|---|---|
| The catalogue of the passes | `features/pases/views/PasesView.tsx` - prop `catalogo?: CatalogoPases` | Reads `RT-PS-01` (`GET /api/pases`) and binds `PaseCatalogoOut` |
| The purchase of a batch | `features/pases/components/FormularioComprador.tsx` - prop `enviar?: (datos) => Promise<void>` | Reads `RT-CM-02` (`POST /api/pases/compras`) and hands the real service. **While the prop is absent the form says why the request cannot leave** |
| The checkout of the passes | `features/pases/components/DialogoCheckout.tsx` - props `enviar`, `pago` | Binds the payment order of `pagos` and the `estado_operativo` |
| The purchase of a batch and its persons | `features/pases/views/PaseGestionarView.tsx` - props `compra`, `pago` | Reads `RT-PS-03` / `RT-PS-04` with the header `X-Pase-Token` and binds `PaseCompraDetalleOut` |
| The revocation of a right | `features/pases/components/DialogoRevocar.tsx` - prop `revocar?` | Reads `RT-RT-03` (`DELETE .../beneficiarios/{persona_id}`) |
| The catalogue of the store | `features/marketplace/views/TiendaCatalogoView.tsx` - props `productos`, `categorias` | Reads `RT-MK-01` (`GET /api/marketplace/categorias`) and `RT-MK-02` (`GET /api/marketplace/productos`) |
| The detail of a product | `features/marketplace/views/ProductoDetalleView.tsx` - prop `producto?: ProductoDetalle` | Reads `RT-MK-03` (`GET /api/marketplace/productos/{slug}`) |
| The order of the store | `features/marketplace/components/DialogoCheckoutTienda.tsx` - prop `crearPedido?` | Reads `RT-CM-03` (`POST /api/marketplace/pedidos`). **The controller is NOT registered: `A0-UI03-02`** |
| The tracking of an order | `features/marketplace/views/PedidoSeguimientoView.tsx` - props `pedido`, `pago`, `entrega` | Reads `RT-MK-04` (`GET /api/marketplace/pedidos/{token}`). **The controller is NOT registered: `A0-UI03-02`** |
| The verdict bucket | `features/*/types/*.types.ts` - `RolPago` | The adapter maps `estado_operativo.codigo` to the bucket. **The bucket is presentational; the label always comes from the backend** |
| The label of a code | `estado_etiqueta`, `EstadoDeclarado` | The adapter resolves the wording of the codes of `DOM-03` and `DOM-05` (`A0-UI03-04`) |

### The deletion checklist (mandatory in API-03, `T-082` of the workflow)

1. Delete `features/pases/fixtures/pase.fixture.ts` and replace it with the Zod
   mirror of the frozen presenters.
2. Delete `features/marketplace/fixtures/marketplace.fixture.ts` and replace it
   with the Zod mirrors of the frozen presenters.
3. Prove that **no** module outside `__tests__` imports a fixture, that there is
   no `catch` that falls back to a fixture and that there is no hidden route.
4. Replace the view-model types of `features/*/types/*.types.ts` with the Zod
   mirrors (or keep them as the view contract and add the schemas next to
   them).
5. Bind the pagination of the catalogue of the store (`page` / `page_size`,
   `FREEZE-ENV-1.0.0` 4.3) and the `categoria_id` filter.
6. Bind the availability of the products to the inventory (`DOM-06`).
7. Add the `loading.tsx` of the five routes if the shell gives them up.
---

## 12. Workload and review boundary

The tasks artefact of this change carries **no** `Review Workload Forecast`,
so no chain decision was required before the apply (the same precedent as
DOM-06, FND-07, FND-08 and UI-01).

**The real size of this packet is ~3 650 changed lines** (32 created files and
5 modified route files), which exceeds the 400-line review budget by roughly
**9x**. There is **no commit** in this packet, so the budget is a report and
not a gate.

**Autonomous work units** (each one reviewable on its own, in this order):

| WU | Scope | Files |
|---|---|---|
| WU-1 | The view models, the money helper and the fixtures of the passes | `features/pases/{types,utils,fixtures}/**` |
| WU-2 | The five payment states and the cards of the passes | `features/pases/components/{EstadoPagoPase,TarjetaPase,ResumenCompra,ContadoresPases}.tsx` |
| WU-3 | The buyer form and the checkout of the passes | `features/pases/{schemas,components/{FormularioComprador,DialogoCheckout,SelectorCantidad,CatalogoPases}}.tsx` |
| WU-4 | The management of the batch and the two views of the passes | `features/pases/components/{ListaBeneficiarios,DialogoRevocar}.tsx` + `features/pases/views/**` |
| WU-5 | The view models, the money helper and the fixtures of the store | `features/marketplace/{types,utils,fixtures}/**` |
| WU-6 | The card, the gallery and the payment states of the store | `features/marketplace/components/{EstadoPagoTienda,TarjetaProducto,GaleriaProducto}.tsx` |
| WU-7 | The checkout of the store and the three views | `features/marketplace/components/DialogoCheckoutTienda.tsx` + `features/marketplace/views/**` |
| WU-8 | The five route files | `app/(public)/{pases,tienda}/**/page.tsx` |
| WU-9 | The two suites | `features/{pases,marketplace}/__tests__/**` |

**Rollback:** revert WU-9 to WU-1. The rollback is confined to the 32 created
files and the 5 modified route files; the shared shell, the providers, the
theme, the other features and the backend are untouched, so reverting this
packet leaves the product exactly as it was. `git stash` was never invoked and
no commit was created.

**Concurrency:** the changes of the other agents in `src/app/**`,
`src/features/**` (notably `features/inscripciones/**`, owned by UI-02) and
`src/components/**` were **not touched, reverted or merged**, and their rows
of the board were not edited. The `layout.tsx` of the two guest families that
appear modified in `git status` are **not** of this packet.

---

## 13. Acceptance criteria of the packet

- [x] Closing the checkout is presented as **recoverable**, not as a
      cancellation and not as a confirmed payment: both dialogs say that the
      purchase or the order survives the window, and the button is named
      "Cerrar".
- [x] The beneficiaries of the passes and the delivery of the store are
      **distinct**: `PASS-02` shows the three counters and the list of
      persons, `SHOP-03` shows the payment and the delivery as two rows, and
      a paid order that is not delivered never reads as "Entregado".
- [x] **No business value is computed in the UI**: no total, no price, no
      availability, no capacity, no payment state and no permission is derived.
      The summary of the purchase says that the total is confirmed by the
      server.
- [x] The shadcn comparison was recorded **before** the composition and no
      shared primitive was overwritten.
- [x] The provisional fixtures are local, typed, marked and listed for their
      deletion in API-03.
- [x] The unregistered controllers (`PedidoController`, `InventarioController`)
      were **not** bound and no endpoint payload was invented.
- [x] The only runtime command was the typecheck, and it is green.
- [ ] The five-width audit in a browser, the assistive-technology pass, the
      execution of the two suites and the lint pass are **DEFERRED** - the
      packet stays `verification_required`.