# VER-01 - Run Full Regression And Payment Reliability Verification

## Purpose

Execute complete target suites against the recorded baseline, triage regressions, and verify payment/idempotency scenarios.

## Original Plan Tasks

- `T-090`, `T-091`.

## Dependencies

- All implementation/cross-cutting packets complete or explicitly blocked; baseline evidence exists.

## Mandatory Context

- All contracts, especially the recorded test-client governing decision.
- Plan: `implementacion/03-pruebas-y-aceptacion.md`, payment/commerce rules/flows, QA-C01-C03.
- `evidence/baseline/**`, current STATE, all apply-progress records.
- Skill: `salesianos-api-data` for contract/inventory verification; no construction skill unless a separate fix packet is approved.

## Allowed Edit Roots

- `Aplicacion/task/salesianos-fest-rebuild/evidence/verification/**`
- Test files only when correcting a test defect that does not change product behavior
- STATE and Engram verify/apply topics.

## Forbidden Edit Roots

- Production code, contracts/plan/docs, frozen roots, config, databases/secrets, cleanup. Product defects return to the owning packet or a separately approved fix packet.

## Implementation Steps

1. Run full target backend/frontend suites and static/migration checks.
2. Compare failures with baseline by command/path/signature; classify known failure, regression, flaky/unproven, or environment blocker.
3. Execute payment modal/retry/duplicate callback/post-payment activation recovery cases.
4. Regenerate endpoint inventory from target registration and compare expected consumers.
5. Persist evidence; do not mark blocked tests as passed.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules -q`
- Workdir `Aplicacion/backend`: `python manage.py check`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx vitest run`
- Workdir `Aplicacion/frontend`: `npx biome check .`
- Workdir `Aplicacion`: `docker compose config --quiet`

## Acceptance Criteria

- Every failure is classified with baseline evidence and owner; new regressions block progress.
- QA-C01-C03 and payment duplicate/retry/reconciliation behavior have real execution evidence.
- Endpoint inventory/consumer drift is resolved or explicitly blocking.

## Parallelism And Conflicts

- Test commands may run independently; triage and evidence merge have one A9 owner.
- Fixes are not performed opportunistically in this packet.

## Rollback

Verification artifacts are removable/revertible; test-only corrections revert with their evidence. No product rollback occurs here.

## Apply Progress Output

Persist tasks, exact commands/versions/exit codes, baseline comparison, failure/regression ledger, payment QA evidence, inventory diff, files, blockers/owners, rollback, and VER-02 readiness. Also upsert `sdd/salesianos-fest-rebuild/verify-report`.

## Next Packet

- [VER-02](VER-02-e2e-ux-security.md) only when regressions are cleared or explicitly blocking.
