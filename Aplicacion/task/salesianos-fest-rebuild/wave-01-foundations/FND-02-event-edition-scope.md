# FND-02 - Implement Event And Edition Scoping

## Purpose

Make edition identity explicit before any domain stores or queries edition-bound data.

## Original Plan Tasks

- `T-010`.

## Dependencies

- Contract freeze for event/edition; `FND-01` registration extension point.

## Mandatory Context

- `contract/django-app-architecture-contract.md`, `PLAN_REFACTORIZACION.md`, `SCHEMA_DRY_INTENTION.md`.
- Plan: `00-decisiones-y-alcance.md` DEC-01, `funcional/02-reglas-de-negocio.md` RN-E01/E02, `funcional/03-modelo-de-datos.md`, `funcional/04-flujos-end-to-end.md` FL-01.
- Documentation: `04-datos-y-dominio.md`; frozen `backend/config/settings/base.py` only as evidence of the rejected global active-event assumption.
- No UI skills; load `salesianos-api-data` only if an endpoint/schema is in scope.

## Allowed Edit Roots

- `Aplicacion/backend/modules/eventos/**`
- A0 request evidence for shared registration/settings; packet evidence/state.

## Forbidden Edit Roots

- Shared A0 files directly; other domain modules; frontend; frozen roots; contracts/plan/docs; secrets/DB.

## Implementation Steps

1. Implement Event/Edition model, constraints, selectors, services, schemas/presenter, and migration according to frozen physical layout.
2. Define explicit edition selection/scope for reads and writes; do not fall back to a global name constant.
3. Expose only frozen query/command contracts and safe empty/not-published behavior.
4. Add isolation tests for two editions and historical reuse.
5. Request A0 registration/settings changes through progress evidence.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/eventos/tests -q`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Every edition-bound operation requires an explicit coherent scope.
- Two editions cannot leak registrations, catalogs, prices, passes, or operations.
- Migrations replay and focused tests cover success, wrong edition, missing edition, and concurrency where applicable.

## Parallelism And Conflicts

- May run with identity/commerce/frontend shell after shared files freeze.
- Migration and A0 registration updates serialize through A0.

## Rollback

Revert module/migration work unit before dependent migrations; remove only A0 registrations added for this module.

## Apply Progress Output

Record packet/task, edition-scope decision, files/migrations, contracts, commands/results, A0 requests, regression classification, rollback, and domain packets unblocked in the apply-progress topic.

## Next Packet

- `DOM-01`, `DOM-03`, `DOM-04`, `DOM-07`, and `DOM-08` after their other dependencies.
