# DOM-03 - Implement Pass Purchases, Beneficiaries, And Courtesy Rights

## Purpose

Create edition-scoped pass purchases and assignments while preserving buyer/attendee separation and audited non-payment courtesy rights.

## Original Plan Tasks

- `T-030`, `T-031`, `T-032`.

## Dependencies

- `FND-02`, `FND-03`, `FND-04`, `FND-05`, frozen rights contract.

## Mandatory Context

- Relevant Django architecture, API wrapper, schema DRY, and test contracts.
- Plan: RN-P01-P08, FL-06/07, auth guest-link contract, data model pass/right entities, QA-P01-P03.
- Documentation: current pass/beneficiary/accreditation endpoint and flow evidence.
- Skill: `salesianos-api-data` where endpoints/schemas are implemented; no UI skills.

## Allowed Edit Roots

- Frozen target pass/benefit module root under `Aplicacion/backend/modules/**`
- Its migrations/tests; packet evidence/state.

## Forbidden Edit Roots

- Payment coordinator internals; registration/marketplace/validation modules; shared A0 files; frontend/frozen/normative roots; secrets/DB.

## Implementation Steps

1. Implement catalog/purchase without mandatory Usuario and without granting unpaid rights.
2. Implement beneficiary assignment, ownership/token scope, duplicate prevention, and audit.
3. Implement courtesy as an audited right with actor/reason and no fake payment.
4. Preserve unresolved revocation/BOX rules as explicit blockers, not guesses.
5. Add focused purchase, assignment, ownership, courtesy, duplicate, and concurrency tests in review slices.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/salesianos_fest/tests -q -k "pase or beneficiario or cortesia"`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Guest purchase does not create Usuario and cannot be accessed by DNI alone.
- Only paid capacity can be assigned; duplicate active rights are rejected.
- Courtesy creates no order/transaction and remains attributable/revocable by policy.

## Parallelism And Conflicts

- May run with marketplace/competitions on disjoint modules.
- Validation contract consumers wait for its right presenter freeze.

## Rollback

Revert packet migrations/code/tests before validation consumers; never erase existing payment/audit facts in live rollback.

## Apply Progress Output

Persist tasks, rights/token decisions, unresolved PDs, files/migrations, QA tests/commands, review slices, rollback, and `XCT-01`/`API-03` readiness.

## Next Packet

- `API-03` and `XCT-01` after schema/presenter freeze.
