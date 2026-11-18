# DOM-05 - Implement Marketplace Orders And Price Snapshots

## Purpose

Create domain-specific orders/details and trusted snapshots without mixed carts or premature delivery state.

## Original Plan Tasks

- `T-041`.

## Dependencies

- `DOM-04`, `FND-04`.

## Mandatory Context

- Relevant backend architecture/API/schema/test contracts.
- Plan: RN-C01/C02, RN-M03, FL-08, marketplace/commercial page contract, QA-M03/M04.
- Documentation: commerce/payment and marketplace evidence.
- Skill: `salesianos-api-data`; no UI skills.

## Allowed Edit Roots

- Marketplace module root/migrations/tests selected by `DOM-04`.
- Packet evidence/state.

## Forbidden Edit Roots

- Commerce/pagos internals; inventory delivery implementation reserved for DOM-06; frontend/shared/frozen/normative roots; secrets/DB.

## Implementation Steps

1. Implement order/detail and commerce adapter with server-validated quantities/prices.
2. Freeze historical snapshots independent of later price/offer changes.
3. Keep order/payment/delivery states distinct and expose typed presenters.
4. Reject mixed pass/registration items.
5. Add pending/paid snapshot, invalid product/edition, ownership, and duplicate-submit tests.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/marketplace/tests -q -k "pedido or detalle or snapshot"`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Orders contain marketplace details only and preserve trusted snapshots.
- Paid does not mean delivered; duplicate submission does not duplicate a recoverable order.
- Presenter exposes clear next actions without provider internals.

## Parallelism And Conflicts

- Serial after DOM-04 migrations; may overlap unrelated domains.
- DOM-06 consumes the frozen order interface.

## Rollback

Revert order module slices/migrations before DOM-06; preserve shared purchase/payment history.

## Apply Progress Output

Record task, order/commerce interface, files/migrations, tests/commands, QA links, rollback, and DOM-06 readiness.

## Next Packet

- [DOM-06](DOM-06-inventory-reservation-delivery.md)
