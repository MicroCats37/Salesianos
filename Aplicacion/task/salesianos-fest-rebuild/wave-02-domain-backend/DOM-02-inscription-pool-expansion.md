# DOM-02 - Implement Capacity Pool, Assignment, And Expansion

## Purpose

Protect paid capacity, assignment/move/removal, and expansion behavior under concurrency.

## Original Plan Tasks

- `T-022`, `T-023`.

## Dependencies

- `DOM-01`, `FND-05`; same-app migration ownership reserved.

## Mandatory Context

- Relevant backend architecture, API wrapper, schema DRY, and test contracts.
- Plan: RN-I03-I06, FL-04/05, data invariants, QA-I02-I05, payment activation interface.
- Documentation: current pool/assignment endpoint and data evidence.
- Skill: `salesianos-api-data` for API/data work only; no UI skills.

## Allowed Edit Roots

- Registration module root selected by `DOM-01`
- Its migrations/tests; packet evidence/state.

## Forbidden Edit Roots

- Commerce/pagos coordinator internals; competitions/pass/marketplace modules; shared A0 files; frontend/frozen/normative roots; secrets/DB.

## Implementation Steps

1. Implement paid/active/available capacity invariants and atomic assignment.
2. Implement add/move/remove with eligibility, duplicate, ownership, edition, and race protection.
3. Implement separate expansion purchase and idempotent capacity activation.
4. Prevent fixed-initial benefit duplication; leave unresolved benefit rules explicit.
5. Add success/rejection/concurrency/retry tests and operational presenters.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/salesianos_fest/tests -q -k "cupo or asignacion or ampliacion"`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Available capacity never goes negative; simultaneous assignments cannot oversubscribe.
- Removal frees capacity without changing purchase/payment history.
- Expansion affects the same registration exactly once and does not duplicate fixed benefits.

## Parallelism And Conflicts

- Serial after `DOM-01`; may run with unrelated domain roots.
- Its eligibility presenter must freeze before competition and frontend integration.

## Rollback

Revert in reverse review-slice order; never delete payment facts or already-audited assignment history during a live-data rollback.

## Apply Progress Output

Record tasks, invariants/locking strategy, files/migrations, QA links, tests/commands/results, review slices, rollback and downstream readiness.

## Next Packet

- `DOM-07` and `API-02` when presenter/schema freeze is recorded.
