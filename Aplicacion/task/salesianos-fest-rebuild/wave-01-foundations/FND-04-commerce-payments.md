# FND-04 - Implement Shared Commerce And Payment Attempts

## Purpose

Provide purchase snapshots, orders, provider attempts, verified callbacks, and safe retry semantics without activating domain rights.

## Original Plan Tasks

- `T-013`, `T-014`.

## Dependencies

- Frozen commerce/payment contract; `FND-01` shared envelope hooks.

## Mandatory Context

- `contract/django-app-architecture-contract.md`, `PLAN_REFACTORIZACION.md`, `api-wrapper-presenter-contract.md`, `TEST_ARCHITECTURE_CONTRACT.md`.
- Plan: DEC-10/11/12, RN-C01-C08, FL-12 and recovery matrix, `contratos/03-integraciones-y-eventos-internos.md` Izipay section.
- Documentation: current payment/data/flow evidence in `02a`, `04-datos-y-dominio.md`, `05-flujos-end-to-end.md`.
- Skill: `salesianos-api-data` when defining endpoints/schemas.

## Allowed Edit Roots

- `Aplicacion/backend/modules/commerce/**`
- `Aplicacion/backend/modules/pagos/**`
- Focused tests and packet evidence/state.

## Forbidden Edit Roots

- Domain rights modules; A0 shared files; frontend; frozen roots; contracts/plan/docs; provider secrets/DB.

## Implementation Steps

1. Implement Compra snapshots and origin, OrdenPago, TransaccionPago, and provider-attempt history.
2. Verify signatures server-side without logging credentials/provider payload secrets.
3. Reuse pending purchase/order safely; closing/reopening checkout cannot cancel or duplicate purchase.
4. Make callback processing idempotent and expose operational state without activating domain rights.
5. Add focused retry, duplicate, late callback, signature, and status tests.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/commerce/tests modules/pagos/tests -q`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Server freezes trusted totals; browser values cannot override money.
- Attempts remain auditable; duplicate/late callbacks do not duplicate payment facts.
- Payment confirmation and right activation are separate states.

## Parallelism And Conflicts

- Commerce and pagos may be separate commits but one packet owner coordinates their interface.
- Shared settings/DI/registration are A0 requests; no concurrent migration edits inside the same app.

## Rollback

Revert commerce/pagos migrations, code, and tests together before right-activation consumers proceed.

## Apply Progress Output

Persist task IDs, models/migrations, provider/idempotency contract, files, tests/commands, secret-redaction confirmation, A0 requests, rollback, and `FND-05` readiness.

## Next Packet

- [FND-05](FND-05-rights-activation.md)
