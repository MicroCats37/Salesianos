# UI-03 - Build Pass, Shop, Guest Order, And Checkout Skeletons

## Purpose

Create presentation-only commercial flows with distinct pass/shop checkout experiences and recoverable payment states.

## Original Plan Tasks

- No direct source-plan ID. Preparatory slice for downstream `API-03`.

## Dependencies

- `GOV-02`, `FND-06`, `FND-07`; frozen provisional commercial wrappers.

## Mandatory Context

- Contracts: frontend architecture, Smart Fields, API wrapper.
- Plan IDs/routes: `PASS-01 /pases`, `PASS-02 /pases/gestionar/[token]`, `SHOP-01 /tienda`, `SHOP-02 /tienda/[slug]`, `SHOP-03 /tienda/pedidos/[token]`; frontend 01/03/06, FL-06/08, payment state contract.
- Documentation: `03a`, `05a`, `07` current evidence.
- Skills in order: UI/UX, feature architecture, forms, shadcn, responsive/a11y; API-data only for read-only contract clarification.

## Allowed Edit Roots

- Matching target app route presentation
- Pass, shop, checkout feature `views/**`, `components/**`, `fixtures/**`, colocated UI tests
- Packet evidence/state.

## Forbidden Edit Roots

- Services/network hooks/wire schemas/query keys/shared API/auth/providers/UI/config; backend/frozen/normative roots.

## Implementation Steps

1. Approve route briefs and compare shadcn candidates for product cards/gallery, checkout/dialog, status, beneficiary lists, and recovery views.
2. Implement separate pass and shop flows; no mixed cart.
3. Render payment pending/verifying/confirmed/not-completed/needs-attention and paid-versus-delivered states from fixtures.
4. Cover empty/disabled module/out-of-stock/image error/token expired/permission/validation/success states.
5. Add marked provisional fixtures, UI tests, keyboard gallery/dialog checks, and five-width audits.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/features/pases src/features/marketplace src/features/pagos src/app`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features/pases src/features/marketplace src/features/pagos src/app`
- Audit widths `360`, `390`, `768`, `1024`, `1440`.

## Acceptance Criteria

- Closing checkout is presented as recoverable, not cancellation or confirmed payment.
- Pass beneficiaries and marketplace delivery remain distinct; no business values are computed in UI.
- shadcn comparison and all mock-removal paths are recorded.

## Parallelism And Conflicts

- Pass/shop feature roots may be separate work-unit commits; shared checkout component requests go through A0.
- No shared transport/schema/key files.

## Rollback

Revert route/feature skeletons and fixture adapters only.

## Apply Progress Output

Persist page IDs/routes, briefs, candidate comparison, fixture/removal ledger, files, skills, tests/viewports, shared requests, rollback, API-03 handoff.

## Next Packet

- [API-03](../wave-03-api-integration/API-03-commercial-integration.md)
