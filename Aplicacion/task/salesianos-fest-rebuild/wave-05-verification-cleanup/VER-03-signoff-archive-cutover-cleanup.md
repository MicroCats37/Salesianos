# VER-03 - Sign Off, Archive, Cut Over, Then Perform Approved Cleanup

## Purpose

Approve the green target, prove rollback, cut over deliberately, and only then remove explicitly approved obsolete content.

## Original Plan Tasks

- `T-095`.

## Dependencies

- `VER-01` and `VER-02` green; checkpoint/manifest current; target replacement green; named product/A0 approval.

## Mandatory Context

- All contracts; complete target plan; global apply/rollback contract; manifest/classification/verification evidence; STATE and all Engram progress/verify records.
- Plan decisions/open PDs and final acceptance criteria.
- No implementation skill is required for sign-off; load relevant data/deployment skills only for evidence validation.

## Allowed Edit Roots

- `Aplicacion/task/salesianos-fest-rebuild/evidence/archive/**`
- `Aplicacion/task/salesianos-fest-rebuild/evidence/cutover/**`
- STATE and Engram archive/verify/apply topics
- Only paths in a separately approved cleanup allowlist after archive and cutover gates.

## Forbidden Edit Roots

- `contract/**`, plan, current-state documentation, skills/agents.
- Frozen source roots unless the user separately approves their retirement.
- `.env*`, secret values, databases/dumps/media, or any unclassified/unarchived path.
- `node_modules`, `.venv`, `.next`, caches, or residue cleanup before the explicit cleanup gate.

## Implementation Steps

1. Reconcile decisions/PDs, packet statuses, QA evidence, known debt, and release owner approval.
2. Create a tracked or external archive excluding regenerated dependencies; record checksum/size/location without secrets.
3. Restore-spot-check at least five files across backend/frontend/integration roots and prove rollback instructions.
4. Execute approved cutover and smoke verification; record old/new endpoints and rollback trigger.
5. Only after green cutover, apply the explicit cleanup allowlist. Quarantine before delete where required; never delete secrets/data blindly.
6. Re-run manifest/status/full smoke and publish archive report.

## Tests And Checks

- Repository root: `git status --short`
- Repository root: `git diff --check`
- Workdir `Aplicacion/backend`: `python manage.py check`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion`: `docker compose config --quiet`
- Workdir `Aplicacion`: `docker compose up -d --build`
- Workdir `Aplicacion`: `docker compose ps --all`
- Workdir `Aplicacion`: `docker compose down` (never `-v`)
- Re-run the manifest checksum comparison and archive restore spot-check command recorded by GOV-00.

## Acceptance Criteria

- Product/A0 sign-off, green verification, archive checksum, restore spot-check, cutover evidence, and rollback trigger all exist.
- Cleanup touches only approved classified paths after cutover; secrets/data/source retirement require separate approval.
- Final status/manifest and archive report identify every retained, quarantined, and removed path.

## Parallelism And Conflicts

- Fully serialized. No other apply may edit target, deployment, archive, or cleanup paths during cutover.

## Rollback

Trigger rollback on failed smoke/critical QA: restore prior deployment/reference from checkpoint/archive, leave evidence intact, and stop cleanup. Never use stash or destructive volume removal.

## Apply Progress Output

Persist task, approvals, final decisions/debt, archive location/checksum/spot-check, cutover commands/results, cleanup allowlist and actual paths, zero-secret confirmation, rollback trigger/result, final status, and next recommendation. Upsert `sdd/salesianos-fest-rebuild/archive-report` and final state.

## Next Packet

- None. Any post-cutover defect or source retirement requires a new separately approved packet.
