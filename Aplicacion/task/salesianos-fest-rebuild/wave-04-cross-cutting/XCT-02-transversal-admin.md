# XCT-02 - Complete Transversal Administration And Audit

## Purpose

Connect the admin summary, edition context, filters, details, actions, and audit across domains without duplicating their services.

## Original Plan Tasks

- `T-083`.

## Dependencies

- API integration wave complete; `XCT-01`; domain operational presenters frozen.

## Mandatory Context

- Backend/API/auth contracts and frontend architecture/responsive contracts.
- Plan: ADM-01-22, RN-A01-A03, FL-12, admin panel and UX system docs, QA-A01-A03.
- Documentation: `03b`, `05a`, endpoint inventories, UI guide.
- Backend uses `salesianos-api-data`; frontend uses full construction order with forms skill where actions require forms.

## Allowed Edit Roots

- Frozen administration module aggregation roots under `Aplicacion/backend/modules/administracion/**`
- Target admin feature/route roots and focused tests
- Packet evidence/state; A0 shared-file requests.

## Forbidden Edit Roots

- Domain business service internals; shared config/transport/auth/UI directly; frozen/normative roots; secrets/DB.

## Implementation Steps

1. Compose admin selectors/results/presenters from domain interfaces; do not reimplement rules.
2. Add edition-aware summary metrics/actions and filters that link to resolvable operational views.
3. Enforce permissions/audit/reason/version on sensitive commands.
4. Integrate frontend services/hooks/schemas/keys and targeted invalidation for admin datasets.
5. Test force-forbidden commands, stale conflicts, filter mapping, drilldowns, audit, and all visible states.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/administracion/tests -q`
- Workdir `Aplicacion/backend`: `python manage.py check`
- Workdir `Aplicacion/frontend`: `npx vitest run src/features/admin src/app`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features/admin src/app`
- Audit admin routes at `360`, `390`, `768`, `1024`, `1440`.

## Acceptance Criteria

- Summary issues lead to filtered records and concrete authorized actions.
- Admin aggregates do not own domain rules; backend rejects forced unauthorized commands.
- Audit evidence names actor/time/reason without exposing secrets or raw internals.

## Parallelism And Conflicts

- Serialize backend admin aggregator files and frontend admin key namespaces.
- Shared registration/auth/navigation changes are A0-only requests.

## Rollback

Revert aggregator/frontend integration/tests together; preserve domain data and audit records.

## Apply Progress Output

Record task, domain interfaces consumed, endpoint/presenter/schema/service/hook/key ledger, files, permissions/audit tests, commands/viewports, shared requests, rollback, and XCT-03 readiness.

## Next Packet

- [XCT-03](XCT-03-payment-media-notifications.md)
