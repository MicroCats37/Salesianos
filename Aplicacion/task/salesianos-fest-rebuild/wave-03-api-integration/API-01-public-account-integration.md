# API-01 - Integrate Public, Identity, Account, And Recovery Routes

## Purpose

Replace UI-01 fixtures with registered event/identity/account/recovery contracts and production query/mutation ownership.

## Original Plan Tasks

- `T-070`, `T-071`.

## Dependencies

- `UI-01`, `FND-02`, `FND-03`, `FND-07`, `FND-08`; relevant presenters/schemas registered and frozen.

## Mandatory Context

- Contracts: next frontend architecture, Smart Fields, API wrapper/schema DRY.
- Plan: PUB-01/02, AUTH-01/02, ACCOUNT-01/02/04/05, REC-01; FL-01/02; auth and API contracts.
- Required backend references: edition/module catalog; local-to-RENIEC resolver; account registration/session; owned registrations/purchases summaries; neutral recovery request. Use exact endpoint/controller, presenter, and schema IDs from GOV-01 freeze and verify in `Aplicacion/backend/config/api.py`.
- Skills in order: UI/UX -> feature architecture -> API-data -> forms -> shadcn -> responsive/a11y.

## Allowed Edit Roots

- UI-01 route/feature roots, including owning `services/**`, `hooks/**`, `schemas/**`, `utils/*claves*`, components/views/tests
- UI-01 provisional fixture files for deletion
- Packet evidence/state.

## Forbidden Edit Roots

- Shared `src/lib/api.ts`, auth/providers/query client/components UI/config unless a separate A0 work unit is approved; backend; other features; frozen/normative roots.

## Implementation Steps

1. Verify each registered endpoint and freeze exact success/error/pagination/204 Zod mirrors.
2. Add one service, exported query options, domain key factory, and focused hooks per dataset.
3. Define stale times and targeted invalidation for account/registration/recovery mutations.
4. Map 401/403/404/409/422/500 envelopes; map field errors via FND-07.
5. Delete every UI-01 provisional fixture/import/fallback and test real adapter boundaries.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/features src/app -t "public|account|auth|recovery"`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features src/app`
- Repository root: `rg -n "PROVISIONAL_CONTRACT_FIXTURE" Aplicacion/frontend/src`
- Audit routes at `360`, `390`, `768`, `1024`, `1440`.

## Acceptance Criteria

- All visible data/actions use registered endpoints and exact presenter/schema mirrors.
- Query keys include edition/filter/page identity and mutations invalidate only affected data.
- No UI-01 fixture/mock/fallback remains; recovery response remains neutral.

## Parallelism And Conflicts

- May run with other API packets on disjoint feature roots.
- Shared transport/auth/key ownership changes serialize through A0.

## Rollback

Revert feature integration and tests together; do not restore production mock fallback. Restore skeleton only on a non-production branch if needed.

## Apply Progress Output

Persist tasks, endpoint/controller/presenter/schema ledger, service/hook/key owners, stale/invalidation/error policy, files, mock deletion proof, commands/results/viewports, rollback, and next packet.

## Next Packet

- `XCT-02` after all admin/account integrations; other API packets may proceed.
