# DOM-01 - Build Registration Catalog And Initial Purchase

## Purpose

Implement edition-scoped packages, disciplines, benefits, eligibility presentation, and initial registration purchase without granting unpaid capacity.

## Original Plan Tasks

- `T-020`, `T-021`.

## Dependencies

- `FND-02`, `FND-03`, `FND-04`; A0 envelope/registration frozen.

## Mandatory Context

- `contract/django-app-architecture-contract.md`, `PLAN_REFACTORIZACION.md`, `SCHEMA_DRY_INTENTION.md`, API wrapper and test contracts.
- Plan: RN-I01/I02, RN-C01/C02, FL-03, data model registration entities, API use-case contract, QA-I01.
- Documentation: current registration endpoint/data/flow evidence.
- Skill: `salesianos-api-data` for endpoints, presenters, and schemas; no UI skills.

## Allowed Edit Roots

- Frozen target registration module root under `Aplicacion/backend/modules/**`
- Its migrations/tests; A0 registration request evidence; packet evidence/state.

## Forbidden Edit Roots

- Commerce/pagos/event/identity internals; shared A0 files; frontend; frozen roots; contracts/plan/docs; secrets/DB.

## Implementation Steps

1. Implement edition-scoped package/discipline/benefit/price catalog and typed presenters.
2. Implement initial registration/team/purchase flow using commerce interfaces.
3. Keep capacity at zero until verified activation; freeze snapshots server-side.
4. Add success, invalid edition/package, pending-payment, duplicate-submit, and permission tests.
5. Keep each behavior plus tests in review slices near 400 changed lines.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/salesianos_fest/tests -q -k "paquete or inscripcion"`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Catalog is real, edition-scoped, and contains no invented fallback price.
- Initial purchase is recoverable and cannot enable unpaid capacity or duplicate registration.
- Presenters own operational causes; controllers contain no business rules.

## Parallelism And Conflicts

- Disjoint from passes, marketplace, competitions, sponsors.
- Same-app migrations serialize with `DOM-02`; A0 registers controllers afterward.

## Rollback

Revert module/migration/test slices before `DOM-02`; preserve shared commerce/payment history.

## Apply Progress Output

Persist packet/tasks, physical module root, files/migrations, interfaces consumed, tests/commands, review slices, A0 requests, regressions, rollback, and `DOM-02` readiness.

## Next Packet

- [DOM-02](DOM-02-inscription-pool-expansion.md)
