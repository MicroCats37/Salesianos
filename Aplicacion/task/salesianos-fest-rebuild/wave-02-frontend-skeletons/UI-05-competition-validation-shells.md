# UI-05 - Build Competition, Marketplace Admin, Pass, Sponsor, And Validation Skeletons

## Purpose

Create remaining admin/operational route shells, including a shared match detail presentation and separate entry/delivery validation experiences.

## Original Plan Tasks

- No direct source-plan ID. Preparatory slice for downstream `API-05` and `XCT-01`.

## Dependencies

- `GOV-02`, `FND-06`, `FND-07`; provisional presenters frozen.

## Mandatory Context

- Contracts: frontend architecture, Smart Fields, API wrapper/auth.
- Plan IDs/routes: `ADM-10 /administracion/competencias`, `ADM-11 /administracion/competencias/[id]`, `ADM-12 /administracion/competencias/[id]/cuadro`, `ADM-13 /administracion/competencias/agenda`, `ADM-15 /administracion/pases`, `ADM-16 /administracion/pases/validar`, `ADM-17 /administracion/marketplace`, `ADM-18 /administracion/marketplace/productos/[id]`, `ADM-19 /administracion/marketplace/inventario`, `ADM-20 /administracion/marketplace/entregas`, `ADM-21 /administracion/patrocinadores`, `ADM-22 /administracion/validaciones`; frontend 04/05/06 and FL-10/11.
- Documentation: `03b`, `05a`, `07` current evidence.
- Skills in full relevant order: UI/UX, feature architecture, forms, shadcn, responsive/a11y; API-data only for read-only contract clarification.

## Allowed Edit Roots

- Matching target admin route presentation
- Owning competition/pass/marketplace/sponsor/validation feature `views/**`, `components/**`, `fixtures/**`, colocated UI tests
- Packet evidence/state.

## Forbidden Edit Roots

- Services/network hooks/wire schemas/query keys/shared API/auth/providers/UI/config; backend/frozen/normative roots.

## Implementation Steps

1. Approve route briefs and compare shadcn candidates for bracket/scroll area, match drawer/dialog, tables, scanner preview, file/gallery forms, and audit timeline.
2. Implement one match-detail composition reachable from competition, agenda, and bracket.
3. Implement separate pass-entry and marketplace-delivery scanner flows: preview never consumes; explicit confirm state follows.
4. Cover no rounds/equips, overlap/version conflict, impact preview, invalid/used/revoked ticket, media error, permission, loading/empty/error/success states.
5. Add provisional fixtures, focused tests, keyboard/scanner fallback and all-width audits.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/features/admin src/features/competencias src/features/validaciones src/app`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features/admin src/features/competencias src/features/validaciones src/app`
- Audit widths `360`, `390`, `768`, `1024`, `1440`, including horizontal bracket and manual-code fallback.

## Acceptance Criteria

- Agenda/bracket/detail share presentation semantics; preview/correction effects are explicit.
- Entry and delivery remain separate operations over a reusable preview component.
- shadcn candidate evidence and complete fixture-removal ledger exist.

## Parallelism And Conflicts

- Feature subroots may be separate review commits; shared scanner/UI/nav requests go through A0.
- Do not edit shared transport, schemas, keys, or config.

## Rollback

Revert named route/feature skeletons and fixtures only.

## Apply Progress Output

Persist page IDs/routes, briefs, candidate comparison, states, fixtures, files, skills, tests/viewports, A0 requests, rollback, API-05/XCT-01 handoff.

## Next Packet

- [API-05](../wave-03-api-integration/API-05-competition-admin-integration.md) and later `XCT-01`.
