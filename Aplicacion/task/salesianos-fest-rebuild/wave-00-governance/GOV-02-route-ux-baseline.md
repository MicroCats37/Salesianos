# GOV-02 - Freeze Route Briefs And Record The Test Baseline

## Purpose

Approve route-level UX intent and capture pre-implementation backend/frontend check results so later failures can be classified as baseline or regression.

## Original Plan Tasks

- `T-001`, `T-002`.

## Dependencies

- `GOV-01` contract freeze complete.

## Mandatory Context

- `contract/next-app-architecture-contract.md`, `smart.md`, and relevant API/auth contracts.
- Plan: all `frontend/*.md`, `funcional/04-flujos-end-to-end.md`, `implementacion/03-pruebas-y-aceptacion.md`.
- Documentation: `03a-paginas-publicas-y-compra.md`, `03b-paginas-administrativas-y-operativas.md`, `05a-matriz-pagina-flujo-endpoint-datos.md`, `07-guia-para-ui-ux.md`.
- Skills: all six `.opencode/skills/salesianos-*` definitions; UI agents are read-only workflow references.
- `00-workflow-frontend-contract-first.md` and `00-olas-paralelas.md`.

## Allowed Edit Roots

- `Aplicacion/task/salesianos-fest-rebuild/evidence/routes/**`
- `Aplicacion/task/salesianos-fest-rebuild/evidence/baseline/**`
- `Aplicacion/task/salesianos-fest-rebuild/STATE.md`
- Engram apply-progress/state topics.

## Forbidden Edit Roots

- All application code, contracts, plan, current-state docs, skills, agents, runtime config, DB/secrets, and unrelated files.

## Implementation Steps

1. Produce route briefs for all plan page IDs with actors, actions, states, flows, presenter/endpoint dependencies, responsive intent, and shadcn candidate comparison requirement.
2. Mark route and endpoint proposals that remain provisional; do not invent live URLs.
3. Run and record current frozen-source baseline checks before target implementation.
4. Classify each failure/warning by command and path; do not fix baseline failures in this packet.
5. Record the target command matrix separately from frozen-source baseline evidence.

## Tests And Checks

- Frozen backend workdir `backend`: `python -m pytest modules -q`
- Frozen backend workdir `backend`: `python manage.py check`
- Frozen backend workdir `backend`: `python manage.py makemigrations --check --dry-run`
- Frozen frontend workdir `frontend`: `npx tsc --noEmit`
- Frozen frontend workdir `frontend`: `npx vitest run`
- Frozen frontend workdir `frontend`: `npx biome check .`
- Repository root: `git status --short`

## Acceptance Criteria

- Every proposed page ID has a reviewable route brief and visible state matrix.
- High-priority flows have mobile/desktop wireframe intent without implementation code.
- Every command has date, workdir, exit code, and concise result; no test is claimed passed unless run.
- Baseline failures are separated from future regressions.

## Parallelism And Conflicts

- Route brief drafting may be divided by route family, but A7 owns the merged artifact.
- Baseline commands may run independently; evidence writes are serialized.

## Rollback

Revert only route/baseline evidence and state updates. Never alter frozen source to make baseline green.

## Apply Progress Output

Upsert `sdd/salesianos-fest-rebuild/apply-progress` with route brief inventory, page IDs, provisional decisions, contracts/skills read, commands/exit codes, baseline failures/warnings, shadcn comparison obligations, files changed, rollback, and foundation/UI packets unblocked.

## Next Packet

- [FND-01](../wave-01-foundations/FND-01-backend-shared-api-media.md)
- [FND-06](../wave-01-foundations/FND-06-frontend-shell.md) after A0 scheduling.
