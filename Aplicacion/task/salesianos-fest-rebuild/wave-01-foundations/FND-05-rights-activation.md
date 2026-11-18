# FND-05 - Coordinate Exactly-Once Rights Activation

## Purpose

Add the cross-domain coordinator that turns a verified payment into one recoverable, idempotent domain activation.

## Original Plan Tasks

- `T-015`.

## Dependencies

- `FND-04`; frozen right activation interfaces from `GOV-01`.

## Mandatory Context

- `contract/django-app-architecture-contract.md`, `PLAN_REFACTORIZACION.md`, `api-wrapper-presenter-contract.md`.
- Plan: RN-C05-C08, `funcional/01-modulos-y-responsabilidades.md` interfaces, integration activation sequence, FL-03/04/06/08.
- Documentation: commerce/pagos/domain flow evidence.
- Skill: `salesianos-api-data` only for coordinator endpoint/presenter contracts.

## Allowed Edit Roots

- Frozen physical coordinator root under `Aplicacion/backend/modules/commerce/**` or `pagos/**` as recorded by GOV-01
- Coordinator-focused tests; packet evidence/state.

## Forbidden Edit Roots

- Inscription/pass/marketplace internals; A0 shared files; frontend; frozen roots; contracts/plan/docs; secrets/DB.

## Implementation Steps

1. Implement origin-dispatched activation interface without importing presentation layers.
2. Persist activation key/status/incidence so retries are exactly once and recoverable.
3. Keep verified payment when domain activation fails; expose safe next action.
4. Provide test fakes/ports for domain consumers without duplicating their rules.
5. Add duplicate, delayed, partial failure, and retry tests.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/commerce/tests modules/pagos/tests -q -k "activ or idempot"`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- One payment fact causes at most one effective activation per purchase/origin.
- Failure after payment is visible and safely retryable.
- Coordinator knows interfaces, not cup/beneficiary/stock rules.

## Parallelism And Conflicts

- Exclusive on coordinator files; domain modules implement their adapters later on disjoint roots.
- A0 reviews any shared registration/DI change.

## Rollback

Revert coordinator and migration work unit; preserve underlying payment history.

## Apply Progress Output

Record task, activation key/state model, interface owners, files/migrations, commands/results, failure/retry evidence, deviations, rollback, and domain adapters unblocked.

## Next Packet

- `DOM-02`, `DOM-03`, and `DOM-06` after their domain prerequisites.
