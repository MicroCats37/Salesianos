# GOV-01 - Freeze Cross-Module Execution Contracts

## Purpose

Turn the existing plan's proposed interfaces into an explicit apply freeze record without creating a new formal SDD phase or changing normative files.

## Original Plan Tasks

- `T-003`, `T-004`, `T-005`, `T-006`, `T-007`.

## Dependencies

- `GOV-00` complete with checkpoint/manifest evidence.

## Mandatory Context

- All `contract/` files, especially `api-wrapper-presenter-contract.md`, `django-app-architecture-contract.md`, `TEST_ARCHITECTURE_CONTRACT.md`, and `SCHEMA_DRY_INTENTION.md`.
- Plan: `00-decisiones-y-alcance.md`, all `funcional/*.md`, all `contratos/*.md`, `frontend/01-mapa-rutas-y-navegacion.md`, and `implementacion/01-arquitectura-y-dependencias.md`.
- Evidence: `Aplicacion/documentacion/02a-inventario-de-endpoints.md`, `02b-proposito-y-consumidores-de-endpoints.md`, `05a-matriz-pagina-flujo-endpoint-datos.md`.
- Skills: `.opencode/skills/salesianos-api-data/SKILL.md` and `references/api-data-contract.md`.
- Global apply and frontend contract-first documents in the parent task directory.

## Allowed Edit Roots

- `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/**`
- `Aplicacion/task/salesianos-fest-rebuild/STATE.md`
- Engram apply-progress/state topics.

## Forbidden Edit Roots

- All code roots, contracts, plan, current-state documentation, skills, agents, config, databases, secrets, and unrelated files.

## Implementation Steps

1. Freeze event/edition scope selection before dependent modules; explicitly replace global active-event assumptions.
2. Freeze Persona/Usuario/titularity, commerce/payment/idempotency, rights preview/confirm/revoke, and media interfaces.
3. Freeze one response/error/pagination envelope and record the test-client contradiction resolution.
4. Define backend presenter/schema versions and a route-to-wrapper ledger.
5. Define provisional typed fixture examples for frontend skeletons; mark them non-production and free of business rules.
6. Record all unresolved PD items with owner/blocking scope; do not convert proposals into approvals.

## Tests And Checks

- Repository root: `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion .opencode/skills .opencode/agents`
- Repository root: `rg -n "PROVISIONAL_CONTRACT_FIXTURE|field_errors|page_size|estado_operativo" Aplicacion/task/salesianos-fest-rebuild/evidence/contracts`
- Repository root: `rg -n "EVENTO_ACTIVO_NOMBRE" Aplicacion/task/salesianos-fest-rebuild/evidence/contracts`

## Acceptance Criteria

- Freeze record names exact owners, identifiers, wrappers, errors, and versioning expectations.
- Edition scope and backend presenter/schema contracts precede parallel skeleton/domain work.
- Test-client and envelope contradictions have an explicit governing decision or a blocking status.
- Fixtures contain examples only and are clearly provisional.

## Parallelism And Conflicts

- Exclusive A0 governance packet; do not parallelize contract freeze edits.
- Consumers may start only after their relevant freeze entries are marked ready.

## Rollback

Revert only the freeze evidence/state work unit. No application rollback is required.

## Apply Progress Output

Upsert `sdd/salesianos-fest-rebuild/apply-progress` with task IDs, freeze versions, decisions/open PDs, contract files read, envelope/test-client decision, provisional fixture ledger, files changed, commands/exit codes, deviations, rollback, and consumers unblocked.

## Next Packet

- [GOV-02](GOV-02-route-ux-baseline.md)
