# GOV-00 - Create A Non-Destructive Checkpoint And Manifest

## Purpose

Establish traceable starting evidence before any target implementation. This packet inventories and classifies content; it must delete, move, overwrite, or normalize nothing.

## Original Plan Tasks

- `T-000`: validate decisions and keep pending items explicit.

## Dependencies

- None. This is the first packet.

## Mandatory Context

- `AGENTS.md`; every file in `contract/`.
- `Aplicacion/plan/salesianos-fest-rebuild/README.md` and `00-decisiones-y-alcance.md`.
- `Aplicacion/plan/salesianos-fest-rebuild/implementacion/01-arquitectura-y-dependencias.md` and `02-plan-de-tareas-y-agentes.md`.
- `Aplicacion/documentacion/00-cobertura-y-trazabilidad.md` as current-state evidence only.
- `Aplicacion/task/salesianos-fest-rebuild/00-contrato-global-de-apply.md` and `STATE.md`.

## Allowed Edit Roots

- `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/**`
- `Aplicacion/task/salesianos-fest-rebuild/STATE.md`
- Engram apply-progress/state topics.

## Forbidden Edit Roots

- All application roots, including both target and frozen source code.
- `contract/**`, `Aplicacion/plan/**`, `Aplicacion/documentacion/**`, skills, agents, runtime config, databases, dumps, `.env*`.
- Any deletion, move, cleanup, generated dependency directory, or secret-content capture.

## Implementation Steps

1. Record branch, HEAD, full `git status --short`, and pre-existing changes without modifying them.
2. Generate a path/size/SHA-256/tracked-status/classification manifest for `Aplicacion/`; never read secret values into evidence.
3. Classify each path as KEEP, COPY/REBUILD, QUARANTINE, DELETE-LATER, GENERATED, or NEVER-DELETE.
4. Record the rollback source for each future quarantine/delete candidate and the unresolved decision owner.
5. Record baseline task numbering: 54 source-defined IDs, not 96 invented tasks.
6. Update state and Engram; make zero product changes and zero deletions.

## Tests And Checks

- Repository root: `git status --short`
- Repository root: `git rev-parse --show-toplevel`
- Repository root: `git rev-parse HEAD`
- Repository root: `git ls-files Aplicacion`
- Repository root: `git diff --name-only -- contract Aplicacion/plan .opencode/skills .opencode/agents`
- PowerShell validation: `Get-ChildItem -LiteralPath "Aplicacion" -File -Recurse -Force | Where-Object { $_.FullName -notmatch '\\(node_modules|\.venv|\.next)\\' } | Get-FileHash -Algorithm SHA256`

## Acceptance Criteria

- Evidence identifies checkpoint, manifest, classifications, rollback sources, and unresolved decisions.
- Secret values are absent; only redacted metadata is recorded.
- No source or target content was deleted, moved, overwritten, or cleaned.
- Pre-existing changes remain untouched and distinguishable.

## Parallelism And Conflicts

- Exclusive packet. No other apply starts until its evidence is persisted.
- It owns only checkpoint evidence and state, never application content.

## Rollback

Delete only evidence created by this packet or revert its documentation work unit. Do not alter pre-existing files.

## Apply Progress Output

Upsert `sdd/salesianos-fest-rebuild/apply-progress` with packet/status, branch/HEAD, manifest path and checksum, classification counts, pre-existing status summary, secret redaction confirmation, zero-deletion proof, rollback sources, commands/exit codes, and next packet. Update `sdd/salesianos-fest-rebuild/state`.

## Next Packet

- [GOV-01](GOV-01-contract-freeze.md)
