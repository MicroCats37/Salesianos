# Parallel Waves And DAG

Concurrency is based on disjoint edit roots, not on agent availability. Default maximum is three simultaneous applies; use two when migrations or frontend route trees are active.

## Executable DAG

```text
GOV-00 -> GOV-01 -> GOV-02
GOV-01 -> FND-01 -> FND-02 -> domain backend packets
GOV-01 -> FND-03 -> identity-dependent domain packets
GOV-01 -> FND-04 -> FND-05 -> purchase/right domain packets
GOV-02 -> FND-06 -> FND-07 -> FND-08 -> UI skeleton packets
backend presenter/schema freeze + matching UI skeleton -> API integration packet
domain/API integration -> XCT-01/XCT-02/XCT-03
all cross-cutting packets -> VER-01 -> VER-02 -> VER-03
```

## Wave Model

| Wave | Packets | Max concurrency | Gate |
|---|---|---:|---|
| 00 governance | `GOV-00` then `GOV-01` then `GOV-02` | 1 | Checkpoint, manifest, contract freeze, baseline evidence |
| 01 foundations | `FND-02`, `FND-03`, `FND-04`, `FND-06` after A0 shared work; `FND-05`, `FND-07`, `FND-08` by dependency | 3 | Backend check/migrations, frontend static/focused checks |
| 02 backend domains | `DOM-01`, `DOM-03`, `DOM-04`, `DOM-07`, `DOM-08`; then dependent packets | 3 | Focused module tests plus backend aggregate |
| 02 frontend skeletons | `UI-01` through `UI-05` after shell and contract freeze | 2 | Focused component tests, typecheck, Biome, five widths |
| 03 API integration | `API-01` through `API-05` when each backend contract freezes | 2 | No provisional mock remains in integrated scope |
| 04 cross-cutting | `XCT-01`, `XCT-02`, then `XCT-03` as dependencies permit | 2 | Full integration aggregate and deployment smoke |
| 05 verification/cleanup | `VER-01`, then `VER-02`, then `VER-03` | 1 | Full suites, QA evidence, archive, cutover approval |

## Conflict Hotspots

Always serialize edits to:

- `Aplicacion/backend/config/api.py`, settings, core response/exception/permission files.
- Migrations in the same Django app or touching the same model/constraint.
- `Aplicacion/frontend/src/lib/api.ts`, auth, providers, shared query client.
- `Aplicacion/frontend/src/components/ui/**`, package/lock/config files.
- Shared query-key namespaces and Zod wrappers.
- `Aplicacion/proxy/**`, `Aplicacion/worker/**`, compose/deployment files.
- `STATE.md` updates; the finishing apply rebases its state evidence on the latest board.

## Aggregate Wave Gates

Commands are future commands and must be run with the shown workdir.

| Gate | Workdir | Commands |
|---|---|---|
| Backend wave | `Aplicacion/backend` | `python manage.py check`; `python manage.py makemigrations --check --dry-run`; `python -m pytest modules -q` |
| Frontend wave | `Aplicacion/frontend` | `npx tsc --noEmit`; `npx vitest run`; `npx biome check .` |
| Integration wave | repository root | Target compose smoke command approved in `XCT-03`; endpoint registration inventory diff; both aggregate gates |
| Final | repository root | Commands in `VER-01` and `VER-02`; all 29 QA cases; responsive matrix 360/390/768/1024/1440 |

Known baseline failures are evidence, not waivers. A failure absent from the baseline or introduced in changed scope is a regression.
