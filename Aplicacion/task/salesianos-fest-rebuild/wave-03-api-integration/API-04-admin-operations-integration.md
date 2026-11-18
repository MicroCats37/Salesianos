# API-04 - Integrate Admin Registration, Team, Participant, And Payment Operations

## Purpose

Connect admin operational views to backend-projected causes, filters, actions, audit, and payment diagnosis.

## Original Plan Tasks

- `T-075`, `T-076`.

## Dependencies

- `UI-04`, `DOM-01/02`, `FND-04/05/07/08`; admin/payment presenters frozen.

## Mandatory Context

- Contracts: next architecture, Smart Fields, API wrapper/auth/schema DRY.
- Plan: ADM-05-09/14, FL-05/12, RN-A01-A03, operational presenter examples.
- Required backend references: admin registration/team/participant list/detail/actions; operational payment list/filter/detail/diagnostic/recovery actions; permissions and audit schemas. Verify exact registrations and envelopes.
- Skills in full order: UI/UX -> feature architecture -> API-data -> forms -> shadcn -> responsive/a11y.

## Allowed Edit Roots

- UI-04 admin feature services/hooks/schemas/key utils/views/components/tests
- UI-04 fixtures for deletion; packet evidence/state.

## Forbidden Edit Roots

- Shared API/auth/providers/UI/config; backend/other features; frozen/normative roots.

## Implementation Steps

1. Add exact operational list/detail/action Zod mirrors and permission/error envelopes.
2. Add single services/query options/key owners; include edition/filter/status/page/record/version.
3. Define invalidation after roster/admin/payment operations; avoid optimistic writes unless exact presenter shape is preserved.
4. Map 403/409/422/500 and stale version; require reason/confirmation for sensitive actions.
5. Delete fixtures and test forced forbidden commands, filter mapping, diagnostics separation, field errors, and cache refresh.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/features/admin src/app -t "team|participant|registration|payment"`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features/admin src/app`
- Repository root: `rg -n "PROVISIONAL_CONTRACT_FIXTURE" Aplicacion/frontend/src/features/admin`
- Audit `360`, `390`, `768`, `1024`, `1440`.

## Acceptance Criteria

- Backend presenter supplies operational status/reason/actions; client does not derive them.
- Service/hook/query-key/invalidation/envelope ownership is explicit and tested.
- No fixture remains; unauthorized forced operations are handled as backend 403.

## Parallelism And Conflicts

- Disjoint from commercial/competition integrations except shared admin keys; one owner must serialize shared namespaces.
- A0 owns shared auth/transport.

## Rollback

Revert integration/tests without restoring production mocks; retain skeleton for controlled repair.

## Apply Progress Output

Persist tasks, endpoint/presenter/schema ledger, services/hooks/keys, invalidation/error/actions policy, mock deletion, files, commands/viewports, rollback, XCT-02 readiness.

## Next Packet

- [XCT-02](../wave-04-cross-cutting/XCT-02-transversal-admin.md)
