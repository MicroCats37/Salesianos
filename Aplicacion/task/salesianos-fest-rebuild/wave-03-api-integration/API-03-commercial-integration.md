# API-03 - Integrate Pass, Shop, Checkout, And Guest Management

## Purpose

Connect pass and marketplace shells to real purchase, payment status, beneficiary, product/order, and delivery presenters.

## Original Plan Tasks

- `T-073`, `T-074`.

## Dependencies

- `UI-03`, `DOM-03` through `DOM-06`, `FND-04/05/07/08`; contracts frozen.

## Mandatory Context

- Contracts: next architecture, Smart Fields, API wrapper/schema DRY.
- Plan: PASS-01/02, SHOP-01/02/03, FL-06/08, RN-P/RN-C/RN-M, payment state contract.
- Required backend references: pass catalog/create purchase/manage beneficiaries; product category/list/detail/create order/order status; payment order/attempt status/retry; delivery ticket projection. Verify exact endpoint/controller, presenter, schema, pagination, and errors.
- Skills in full order: UI/UX -> feature architecture -> API-data -> forms (buyer/beneficiary/file forms) -> shadcn -> responsive/a11y.

## Allowed Edit Roots

- UI-03 pass/marketplace/payment feature services/hooks/schemas/key utils/views/components/tests
- UI-03 fixtures for deletion; packet evidence/state.

## Forbidden Edit Roots

- Shared transport/query/auth/providers/UI/config; backend; other features; frozen/normative roots.

## Implementation Steps

1. Mirror all list/detail/purchase/order/payment/delivery envelopes with exact Zod schemas.
2. Add one owner per dataset and query keys including edition/slug/token/order/filter/page.
3. Define create-only purchase/order payloads, beneficiary mutations, payment retry/status invalidation, and no mixed cart.
4. Treat payment confirmation and delivery/right state independently; no optimistic money/stock/right updates.
5. Remove fixtures and test token expiry, 409 stock/right races, 422 fields, 204, image failure, and payment uncertainty.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/features/pases src/features/marketplace src/features/pagos src/app`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features/pases src/features/marketplace src/features/pagos src/app`
- Repository root: `rg -n "PROVISIONAL_CONTRACT_FIXTURE" Aplicacion/frontend/src/features`
- Audit `360`, `390`, `768`, `1024`, `1440` including gallery/dialog/token states.

## Acceptance Criteria

- Exact service/hook/key ownership, invalidation, envelope/error behavior, and token scope are documented/tested.
- No mock or hidden fallback remains; closing checkout never fabricates a payment result.
- Paid/right/delivery states remain distinct and server-owned.

## Parallelism And Conflicts

- Pass and shop may be review slices but shared payment hooks/keys have one owner.
- Shared transport/auth edits require A0.

## Rollback

Revert integration slices/tests; never restore production commercial mocks or mutate backend facts.

## Apply Progress Output

Persist tasks, endpoint/presenter/schema ledger, services/hooks/keys, cache/error/payload policy, mock deletion, files, commands/viewports, rollback, XCT-01/XCT-03 readiness.

## Next Packet

- [XCT-01](../wave-04-cross-cutting/XCT-01-tickets-validation.md)
