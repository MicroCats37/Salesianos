# XCT-01 - Implement Shared Ticket Preview And Atomic Validation

## Purpose

Provide a reusable credential resolver with separate pass-entry and product-delivery operations, atomic confirmation, and audit.

## Original Plan Tasks

- `T-080`, `T-081`.

## Dependencies

- `DOM-03`, `DOM-06`, `API-03`, `API-05`; frozen right/delivery interfaces.

## Mandatory Context

- Backend architecture, API wrapper/schema DRY/test contracts; frontend architecture and responsive contract for operator screens.
- Plan: RN-P06-P08, FL-10, validation entities, integration ticket section, ADM-16/20/22, QA-V01/V02.
- Documentation: endpoint/flow/page evidence for validation.
- Backend skill: `salesianos-api-data`. Frontend skill order: UI/UX -> feature architecture -> API-data -> forms if manual code input -> shadcn -> responsive/a11y.

## Allowed Edit Roots

- `Aplicacion/backend/modules/validaciones/**`
- `Aplicacion/frontend/src/features/validaciones/**` and matching route presentation/tests
- Packet evidence/state; A0 registration requests.

## Forbidden Edit Roots

- Pass/marketplace business internals; shared A0 backend/frontend files directly; frozen/normative roots; secrets/DB.

## Implementation Steps

1. Implement credential resolution and typed owner adapters without duplicating right/stock rules.
2. Keep preview read-only; confirmation revalidates under transaction/locking with idempotency key.
3. Store actor/time/type/quantity/result and preserve failed/repeated audit outcomes safely.
4. Integrate distinct entry and delivery screens with manual code fallback and permission states.
5. Add concurrent scan, repeated use, revoked/invalid, preview-no-write, and UI envelope tests.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/validaciones/tests -q`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/frontend`: `npx vitest run src/features/validaciones src/app`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features/validaciones src/app`
- Audit operator routes at `360`, `390`, `768`, `1024`, `1440`.

## Acceptance Criteria

- Preview never consumes; simultaneous confirmations permit only authorized quantity once.
- Pass entry and product delivery share infrastructure but not business decisions/screens.
- Audit and user-facing reason are safe, typed, and permission-aware.

## Parallelism And Conflicts

- Backend and frontend work may be separate commits after contract freeze; one packet owner integrates them.
- Owner adapters remain in their domains; A0 serializes registration/shared keys.

## Rollback

Revert code/tests/migrations before operational use; never delete validation history during a live rollback.

## Apply Progress Output

Persist tasks, adapter/presenter/schema ledger, files/migrations, service/hook/key/cache/error ownership, concurrency tests/commands/viewports, A0 requests, rollback, and XCT-02 readiness.

## Next Packet

- [XCT-02](XCT-02-transversal-admin.md)
