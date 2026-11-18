# FND-03 - Implement Identity, Roles, And RENIEC Resolution

## Purpose

Establish Persona independent from Usuario, Django role authority, titularity boundaries, and local-first external resolution.

## Original Plan Tasks

- `T-011`, `T-012`.

## Dependencies

- `GOV-01`; A0 permission/registration extension points from `FND-01`.

## Mandatory Context

- `contract/django-app-architecture-contract.md`, `PLAN_REFACTORIZACION.md`, `api-wrapper-presenter-contract.md`, `TEST_ARCHITECTURE_CONTRACT.md`.
- Plan: DEC-02/03/04, RN-U01-U04, FL-02, `contratos/02-autenticacion-y-permisos.md`, integration contract RENIEC section.
- Documentation: `02a-inventario-de-endpoints.md`, `04-datos-y-dominio.md`, `05-flujos-end-to-end.md`.
- Skill: `.opencode/skills/salesianos-api-data/SKILL.md` for API/schema work only.

## Allowed Edit Roots

- `Aplicacion/backend/modules/usuarios/**`
- Feature-specific tests and packet evidence/state.

## Forbidden Edit Roots

- A0 shared files directly; other modules/frontend; frozen roots; contracts/plan/docs; secrets/DB.

## Implementation Steps

1. Implement Persona uniqueness, optional Usuario relation, Normal/Admin Django groups, and titularity checks.
2. Implement local-first resolver with typed external states and persist only on confirmed operation.
3. Protect concurrent duplicate creation and avoid DNI-as-authorization behavior.
4. Add typed presenters/errors and focused success/rejection/concurrency tests.
5. Request A0 registration/permission changes separately.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python -m pytest modules/usuarios/tests -q`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python manage.py check`

## Acceptance Criteria

- Persona can exist without Usuario; account/role behavior remains backend-owned.
- Local hit avoids RENIEC; external failure is recoverable; confirmed persistence is race-safe.
- Knowing a document never grants access to another person's operations.

## Parallelism And Conflicts

- Disjoint from event and commerce module roots.
- Shared auth/settings/registration edits are A0 serialized.

## Rollback

Revert identity module/migrations/tests as one work unit before dependent domain data exists.

## Apply Progress Output

Persist tasks, identity/titularity contract version, external adapter behavior, files/migrations, tests/commands, A0 requests, baseline/regressions, rollback, and consumers unblocked.

## Next Packet

- `DOM-01`, `DOM-03`, and `API-01` when their other dependencies are ready.
