# XCT-03 - Reconcile Payments, Harden Deployment, And Gate Notifications

## Purpose

Close payment-right recovery, target media/permission deployment, and notification integration only if SMTP decisions are approved.

## Original Plan Tasks

- `T-084`, `T-085`, `T-086`.

## Dependencies

- `FND-05`, `DOM-02/03/06`, `XCT-02`; PD-08 approval is required only for notification provider configuration.

## Mandatory Context

- All contracts, with emphasis on backend architecture, API messages, tests, and secret handling.
- Plan: RN-C03-C08, FL-12/recovery matrix, media/integration contract, notification deferral, QA-C01-C03/MEDIA01/N01.
- Documentation: runtime/deployment/payment/media evidence.
- Skill: `salesianos-api-data`; no UI skills unless recovery/admin presentation changes are explicitly in scope.

## Allowed Edit Roots

- A0-owned target payment recovery/coordinator files
- `Aplicacion/backend/config/**`, target media/deployment settings, `Aplicacion/proxy/**`, `Aplicacion/worker/**`
- Approved target notification module/config excluding secret values
- Focused tests and packet evidence/state.

## Forbidden Edit Roots

- Domain rights internals; frozen roots; contracts/plan/docs; `.env*`, databases/dumps, secret values; destructive cleanup.

## Implementation Steps

1. Implement reconciliation for verified payment with missing/partial right activation and safe retry.
2. Verify endpoint registration order, DI, permissions, media volume/serving/backup, and target deployment configuration.
3. Keep email failure independent from payment/right success; configure provider only with explicit PD-08 approval and environment variable names, never values.
4. If PD-08 is unresolved, persist T-086 as blocked/deferred without inventing SMTP settings.
5. Add recovery, duplicate, permission, media persistence, notification failure, and deployment smoke checks.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/commerce/tests modules/pagos/tests modules/notificaciones/tests -q`
- Workdir `Aplicacion/backend`: `python manage.py check`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion`: `docker compose config --quiet`
- Workdir `Aplicacion`: `docker compose build`
- Repository root: `git diff --check`

## Acceptance Criteria

- Verified payments cannot become lost or double-activate rights; incidents are recoverable/auditable.
- Target media/permissions/deployment config is coherent and contains no committed secrets.
- Notification failure never reverts purchases; unresolved SMTP remains an explicit blocker, not fake completion.

## Parallelism And Conflicts

- A0 serializes all shared config/deployment edits.
- Payment recovery tests may run independently from media build; evidence merge is serialized.

## Rollback

Restore A0 config from checkpoint and revert packet work units; do not remove volumes, user media, payment facts, or secrets. Never use `docker compose down -v`.

## Apply Progress Output

Persist tasks and per-task status, reconciliation evidence, config/files, DI/registration order, environment variable names only, commands/results, PD-08 decision/blocker, rollback, and VER-01 readiness.

## Next Packet

- [VER-01](../wave-05-verification-cleanup/VER-01-baseline-regression-payments.md)
