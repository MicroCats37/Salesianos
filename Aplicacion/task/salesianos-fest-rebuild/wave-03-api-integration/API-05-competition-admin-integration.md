# API-05 - Integrate Competition And Remaining Admin Routes, Then Remove All Mocks

## Purpose

Connect competition, pass, marketplace, sponsor, and validation-admin surfaces; enforce the global real-contract cutover.

## Original Plan Tasks

- `T-077`, `T-078`, `T-082`.

## Dependencies

- `UI-05`, `DOM-03` through `DOM-08`, `FND-07/08`; matching presenters/schemas frozen.

## Mandatory Context

- Contracts: next architecture, Smart Fields, API wrapper/auth/schema DRY.
- Plan: ADM-10-13/15-22, frontend 04/05/06, FL-10/11, RN-K/RN-A, API use-case contracts.
- Required backend references: competition/team/round/match/agenda/bracket/preview/confirm/correct; pass/courtesy admin; marketplace product/order/inventory; sponsor CRUD/media; validation audit. Verify exact endpoint/controller/presenter/schema registration and envelope.
- Skills in full order: UI/UX -> feature architecture -> API-data -> forms -> shadcn -> responsive/a11y.

## Allowed Edit Roots

- UI-05 owning feature services/hooks/schemas/key utils/views/components/tests and route presentation
- All provisional fixture files under target feature roots for deletion
- A0-approved integration evidence/state.

## Forbidden Edit Roots

- Shared transport/auth/providers/UI/package/config except an explicit serialized A0 sub-work-unit; backend; frozen/normative roots.

## Implementation Steps

1. Mirror exact operational schemas, including expected version, preview impact, actions, audit, media, and pagination.
2. Add services/query options/domain key factories and targeted invalidation for each dataset.
3. Keep preview reads non-writing; map 403/409/422 and stale-version recovery; use corrected multipart through API-data owner.
4. Replace every UI-05 fixture and scan the whole target for provisional fixtures, mock imports, static business fallbacks, and unconsumed routes.
5. Record any unintegrated registered endpoint as explicit debt/owner; no hidden mock may remain in a completed route.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/features/admin src/features/competencias src/features/validaciones src/app`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features src/app`
- Repository root: `rg -n "PROVISIONAL_CONTRACT_FIXTURE|mock|fallback" Aplicacion/frontend/src`
- Workdir `Aplicacion/backend`: `python manage.py check`
- Audit all affected routes at `360`, `390`, `768`, `1024`, `1440`.

## Acceptance Criteria

- Endpoint/presenter/schema, service/hook/key, cache invalidation, envelope/error, and mock-removal ownership is complete.
- Preview does not mutate; confirmation/correction handles version conflicts and impact.
- No completed route uses a hidden mock or invented fallback; all exceptions are explicit blockers/debt.

## Parallelism And Conflicts

- Serialize shared admin/query namespaces and A0 files.
- This is the API wave gate; it finishes after API-01 through API-04 evidence is current.

## Rollback

Revert feature integration slices without restoring production mocks. If cutover fails, mark routes blocked and restore only non-production skeleton evidence.

## Apply Progress Output

Persist tasks, complete endpoint-consumer ledger, presenters/schemas, services/hooks/keys/invalidation/errors, multipart use, mock scan/deletion, files, commands/viewports, debt/blockers, rollback, and cross-cutting readiness.

## Next Packet

- `XCT-01`, then `XCT-02` and `XCT-03` by dependency.
