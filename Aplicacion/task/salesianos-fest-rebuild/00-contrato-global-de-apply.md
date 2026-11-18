# Global Apply Contract

Every packet inherits this contract. Packet-specific instructions narrow it; they never weaken it.

## Mandatory Read Order

1. Root [`AGENTS.md`](../../../AGENTS.md).
2. All seven files in [`contract/`](../../../contract/), then the packet's relevant contract subset.
3. [`Aplicacion/plan/salesianos-fest-rebuild/`](../../plan/salesianos-fest-rebuild/) files named by the packet.
4. Relevant current-state evidence under [`Aplicacion/documentacion/`](../../documentacion/).
5. Required project-local skills under [`.opencode/skills/`](../../../.opencode/skills/).
6. The packet and current [STATE.md](STATE.md).

## Precedence

`contract/` > target plan > executable packet > current-state documentation > current code.

The known test-client contradiction is not permission to choose silently. Record the governing decision before test-bearing implementation. Current architecture evidence favors `ninja_extra.testing.TestAsyncClient` or `django.test.Client` for async controllers.

## Root Ownership

| Root | Role | Default policy |
|---|---|---|
| `Aplicacion/backend/**` | Target backend | Editable only when packet allows it |
| `Aplicacion/frontend/**` | Target frontend | Editable only when packet allows it |
| `Aplicacion/worker/**`, `Aplicacion/proxy/**` | Target integration edge | Editable only in an explicit A0 packet |
| `backend/**`, `frontend/**`, `worker/**`, `proxy/**` | Frozen source references | Read-only; source fixes require a separately approved packet |
| `contract/**` | Normative fallback | Read-only in ordinary apply packets |
| `Aplicacion/plan/**` | Spec/design | Read-only |
| `Aplicacion/task/**` | Executable task source/state | Only packet/state/evidence updates explicitly allowed |
| `Aplicacion/documentacion/**` | Current-state evidence | Read-only; not target specification |

## Shared Files

A0 exclusively owns and serializes:

- `Aplicacion/backend/config/api.py`, settings, router registration, and deployment config.
- `Aplicacion/backend/core/responses.py`, `exceptions.py`, `permissions.py`, and shared capability policy.
- `Aplicacion/frontend/src/lib/api.ts`, shared auth, global providers, `components/ui/**`.
- Frontend package, lock, shadcn, Biome, TypeScript, Next, Vitest, and PostCSS config files.
- Shared query-client configuration and cross-domain migration ordering.

Domain packets may request a shared-file change in apply progress; they may not edit the file themselves.

## Hard Prohibitions

- Never use `git stash` or any variant.
- Never expose, print, copy, hash into chat, or commit secret values. Record only path, classification, and redacted metadata.
- Never place price, eligibility, capacity, payment confirmation, permission, stock, rights, or transition rules in frontend code.
- Never invent endpoints, response fields, page data, prices, or successful test results.
- Never edit source roots, contracts, plan files, skills, agents, runtime config outside a packet's allowed roots, databases, dumps, `.env*`, or unrelated changes.
- Never delete or overwrite source/target content before checkpoint, manifest, rollback/archive, and a green replacement.
- Never let a mock become a production fallback or silent transport path.

## Contract Freeze

Backend presenter/schema contracts and edition scope must freeze before backend and frontend skeleton work run in parallel. A skeleton may use a typed local fixture adapter only when:

- It is marked `PROVISIONAL_CONTRACT_FIXTURE`.
- It mirrors a named plan wrapper/presenter.
- It contains examples, not business calculations.
- It lives inside the owning feature, not shared API/schema/query-key files.
- Its integration packet deletes/replaces it after the real presenter/schema freezes.

See [the frontend contract-first workflow](00-workflow-frontend-contract-first.md).

## Testing Policy

- Every apply runs focused tests and static checks listed in its packet.
- Every wave gate runs aggregate checks from [the wave DAG](00-olas-paralelas.md).
- Record an early baseline and distinguish known failures from new regressions.
- Full backend/frontend suites, the QA matrix, responsive checks, accessibility, permissions, security, and concurrency run during final verification.
- A failed focused check blocks completion unless recorded as a verified pre-existing baseline failure with unchanged evidence.
- Keep tests with the behavior they verify; do not defer test creation to a later packet.

Commands are shown with an explicit workdir. Apply agents should use their execution tool's `workdir` parameter rather than `cd`.

## Progress Persistence

After each work unit, upsert `sdd/salesianos-fest-rebuild/apply-progress` and update `sdd/salesianos-fest-rebuild/state` plus [STATE.md](STATE.md). Record:

- Packet ID, original task IDs, owner, status, dependency evidence.
- Contracts, plan files, documentation, and skills read.
- Allowed roots used and changed files with no secret contents.
- Work-unit commits or review slices and changed-line forecast/actual count.
- Commands run, exit codes, and concise outputs; never claim unrun tests passed.
- Baseline-known failures versus regressions.
- Decisions, deviations, blockers, mocks remaining, and rollback instructions.
- Next packet(s) made ready.

## Rollback And Cleanup

Implementation rollback is packet-scoped: revert only the packet's reviewed work unit or restore from the recorded checkpoint. Cleanup requires all of these:

1. Checkpoint and complete path/hash/classification manifest.
2. Green target replacement and final verification evidence.
3. External or tracked archive with checksum and restore spot-check.
4. Named rollback owner and cutover decision.
5. Explicit cleanup allowlist; secrets, databases, and dumps require separate approval.

If any gate is missing, cleanup is blocked.
