# DOM-06 - Implement Inventory, Anti-Oversell, And Delivery State

## Purpose

Audit every stock movement and prevent oversell/double decrement while separating payment from delivery.

## Original Plan Tasks

- `T-042`, `T-043`.

## Dependencies

- `DOM-04`, `DOM-05`, `FND-05`; PD-05 policy explicitly recorded.

## Mandatory Context

- Relevant backend architecture/API/schema/test contracts.
- Plan: RN-M04-M07, FL-08/09, inventory entities/invariants, QA-M01/M02/M04.
- Documentation: current payment/commerce operation evidence.
- Skill: `salesianos-api-data`; no UI skills.

## Allowed Edit Roots

- Marketplace module root/migrations/tests.
- Packet evidence/state.

## Forbidden Edit Roots

- Payment coordinator internals; ticket/validation module; frontend/shared/frozen/normative roots; secrets/DB.

## Implementation Steps

1. Implement immutable movement ledger with reason/reference/actor and compensating reversals.
2. Implement approved reservation or transactional availability strategy.
3. Activate sale stock effect exactly once after verified payment.
4. Separate paid, reserved, available, partially delivered if approved, and delivered states.
5. Add concurrent purchase, duplicate activation, manual movement, insufficient stock, and delivery tests.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/marketplace/tests -q -k "inventario or stock or entrega or reserva"`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Simultaneous orders cannot oversell and repeated activation cannot double-decrement.
- Non-sale exits create no fake purchase/payment.
- Delivery remains independently auditable and retry-safe.

## Parallelism And Conflicts

- Serial on marketplace migrations; disjoint from other domains.
- `XCT-01` waits for delivery/right presenter freeze.

## Rollback

Use compensating movements for live stock facts; code rollback must never delete the audit ledger.

## Apply Progress Output

Persist tasks, stock strategy/PD decision, locking/idempotency evidence, files/migrations, commands/results, rollback, and validation/API readiness.

## Next Packet

- `API-03` and `XCT-01` after frozen presenters.
