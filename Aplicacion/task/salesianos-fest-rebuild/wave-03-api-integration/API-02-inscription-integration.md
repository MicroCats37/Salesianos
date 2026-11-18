# API-02 - Integrate Registration Wizard, Pool, Teams, And Purchases

## Purpose

Replace registration fixtures with real package, quote, purchase, pool, participant, team, and expansion contracts.

## Original Plan Tasks

- `T-072`.

## Dependencies

- `UI-02`, `DOM-01`, `DOM-02`, `FND-05`, `FND-07`, `FND-08`; presenters/schemas frozen.

## Mandatory Context

- Contracts: next architecture, Smart Fields, API wrapper/schema DRY.
- Plan: SPORT-01, ACCOUNT-03, FL-03/04/05, RN-I01-I06, API use-case contracts.
- Required backend references: edition package catalog/quote; create registration/initial purchase; registration detail/pool; resolve/add/assign/move/remove participant; expansion purchase; operational team presenter. Verify exact registered endpoints, presenters, schemas, and envelopes from GOV-01/DOM records.
- Skills in full order: UI/UX -> feature architecture -> API-data -> forms -> shadcn -> responsive/a11y.

## Allowed Edit Roots

- UI-02 registration route/feature services/hooks/schemas/key utils/views/components/tests
- UI-02 fixtures for deletion; packet evidence/state.

## Forbidden Edit Roots

- Shared API/auth/providers/UI/config; backend/other features; frozen/normative roots.

## Implementation Steps

1. Add exact Zod mirrors for catalog/quote/detail/pool/team/payment states and errors.
2. Add services/query options/key factory; include edition, registration, filters, and page in keys.
3. Define create/update mappings and targeted invalidation after purchase/assignment/move/removal/expansion.
4. Do not optimistically calculate capacity/eligibility; invalidate when exact backend shape cannot be preserved.
5. Remove every fixture/mock and test 422 field errors, 409 races, pending/indeterminate payment, and recovery.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/features/inscripciones src/app`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features/inscripciones src/app`
- Repository root: `rg -n "PROVISIONAL_CONTRACT_FIXTURE" Aplicacion/frontend/src/features/inscripciones`
- Audit `360`, `390`, `768`, `1024`, `1440`.

## Acceptance Criteria

- Service/hook/query-key ownership is singular and exact envelopes parse loudly.
- Cache invalidation reflects backend results; browser never derives available capacity or eligibility.
- All registration mocks are removed and failures preserve recoverable operation state.

## Parallelism And Conflicts

- Disjoint from pass/shop/competition feature integrations.
- Shared catalog keys or API changes require A0 serialization.

## Rollback

Revert integration/tests without restoring a production fixture fallback; preserve skeleton for controlled repair.

## Apply Progress Output

Record task, endpoint/presenter/schema ledger, services/hooks/keys, invalidation/error/payload policy, mock deletion, files, commands/viewports, rollback, XCT-02 readiness.

## Next Packet

- `XCT-02` after other admin integrations.
