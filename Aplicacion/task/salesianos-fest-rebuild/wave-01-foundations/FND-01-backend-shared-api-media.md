# FND-01 - Establish A0 Backend API, Permissions, And Media Foundations

## Purpose

Create the serialized shared backend surface for endpoint registration, safe envelopes/exceptions, permissions, and local persistent media.

## Original Plan Tasks

- `T-016`, `T-018`.

## Dependencies

- `GOV-01` and `GOV-02`; A0 exclusive ownership reserved.

## Mandatory Context

- `contract/django-app-architecture-contract.md`, `PLAN_REFACTORIZACION.md`, `api-wrapper-presenter-contract.md`, `SCHEMA_DRY_INTENTION.md`, `TEST_ARCHITECTURE_CONTRACT.md`.
- Plan: `contratos/01-api-wrappers-presenters.md`, `02-autenticacion-y-permisos.md`, `03-integraciones-y-eventos-internos.md`, `funcional/03-modelo-de-datos.md`, `implementacion/01-arquitectura-y-dependencias.md`.
- Documentation: `01-arquitectura-y-runtime.md`, `02a-inventario-de-endpoints.md`, `06-operacion-y-deuda-tecnica.md`.
- Skill: `.opencode/skills/salesianos-api-data/SKILL.md` and its API-data reference.

## Allowed Edit Roots

- `Aplicacion/backend/config/api.py`
- `Aplicacion/backend/config/settings/**`
- `Aplicacion/backend/core/responses.py`, `exceptions.py`, `permissions.py`, `capacidades.py`, media utilities/tests
- `Aplicacion/backend/**/tests/**` directly covering this foundation
- Packet evidence/state.

## Forbidden Edit Roots

- Frozen roots; contracts/plan/documentation; domain module internals; frontend; secrets/databases/dumps; proxy/worker; unrelated config.

## Implementation Steps

1. Freeze one success/error/pagination envelope and safe public error catalog; never return raw exception text.
2. Establish permission/authentication authority and 401/403 behavior.
3. Define media root/URL, validation hooks, persistence expectations, backup/cleanup contract without secret values.
4. Provide A0 registration extension points; do not register unfinished domain controllers.
5. Add focused envelope, status, permission, and media validation tests.

## Tests And Checks

- Workdir `Aplicacion/backend`: `python manage.py check`
- Workdir `Aplicacion/backend`: `python manage.py makemigrations --check --dry-run`
- Workdir `Aplicacion/backend`: `python -m pytest core/tests modules/usuarios/tests -q`
- Repository root: `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion`

## Acceptance Criteria

- Shared files have one A0 owner and stable extension contract.
- 401/403/404/409/422/500 envelopes are safe and typed.
- Media policy uses persistent local storage and rejects invalid size/type/signature paths.
- No secrets or domain rules enter shared config.

## Parallelism And Conflicts

- Exclusive shared-file packet. Domain work may inspect but not edit these files.
- Complete before packets that require app registration or media settings.

## Rollback

Revert this A0 work unit and its focused tests together; restore the recorded registration/settings checkpoint.

## Apply Progress Output

Persist `sdd/salesianos-fest-rebuild/apply-progress`: packet/tasks, shared files, contracts/skill, envelope/version, permission/media decisions, commands/results, baseline comparison, deviations, rollback, and consumers unblocked.

## Next Packet

- `FND-02`, `FND-03`, and `FND-04` may start on disjoint roots.
