# DOM-07 - Implement Competitions, Scheduling, Results, And Corrections

## Purpose

Build edition-scoped eligibility, rounds, matches, agenda, result progression, preview, and conflict-safe correction.

## Original Plan Tasks

- `T-050`, `T-051`, `T-052`.

## Dependencies

- `FND-02`, `DOM-02` eligibility presenter frozen.

## Mandatory Context

- Relevant backend architecture/API/schema/test contracts.
- Plan: RN-K01-K03, FL-11, competition data model, `frontend/05-competencias-y-encuentros.md`, QA-K01-K03.
- Documentation: current competition endpoints/pages/flows.
- Skill: `salesianos-api-data`; no UI skills.

## Allowed Edit Roots

- `Aplicacion/backend/modules/competencias/**`
- Its migrations/tests; packet evidence/state.

## Forbidden Edit Roots

- Registration pool internals; commerce/passes/marketplace; shared A0/frontend/frozen/normative roots; secrets/DB.

## Implementation Steps

1. Implement competition/team eligibility through the registration contract, not direct rule duplication.
2. Implement rounds/matches/agenda and no-overlap/version constraints.
3. Implement result/winner, read-only preview, confirmed progression, and impact-aware correction with reason.
4. Expose one coherent operational presenter used by agenda/bracket/detail.
5. Add eligibility, overlap, bye, preview-no-write, progression, stale-version, and correction tests in slices.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/competencias/tests -q`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Wrong edition/discipline teams are rejected with backend-owned reasons.
- Preview never writes; confirmation is version-safe and correction impact is explicit.
- Agenda, bracket, and match detail derive from one operational source.

## Parallelism And Conflicts

- May run with passes/marketplace; does not edit registration.
- Same-app migrations and A0 registration serialize.

## Rollback

Revert competition slices/migrations before frontend integration; preserve audited results in live rollback through compensating/versioned operations.

## Apply Progress Output

Record tasks, eligibility interface, files/migrations, presenter version, QA tests/commands, review slices, rollback, and API-05 readiness.

## Next Packet

- `UI-05` may already exist; [API-05](../wave-03-api-integration/API-05-competition-admin-integration.md) waits for this freeze.
