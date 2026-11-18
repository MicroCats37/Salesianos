# UI-04 - Build Admin Registration, Team, Participant, And Payment Skeletons

## Purpose

Create operational admin screens that explain causes and separate commercial/payment/right layers before API integration.

## Original Plan Tasks

- No direct source-plan ID. Preparatory slice for downstream `API-04`.

## Dependencies

- `GOV-02`, `FND-06`, `FND-07`; provisional operational presenters frozen.

## Mandatory Context

- Contracts: frontend architecture, Smart Fields, API wrapper/auth.
- Plan IDs/routes: `ADM-05 /administracion/inscripciones`, `ADM-06 /administracion/inscripciones/[id]`, `ADM-07 /administracion/equipos`, `ADM-08 /administracion/equipos/[id]`, `ADM-09 /administracion/participantes`, `ADM-14 /administracion/pagos`; frontend 01/04/06, FL-05/12.
- Documentation: `03b`, `05a`, `07` current evidence.
- Skills in full order: UI/UX, feature architecture, forms where filters/actions require them, shadcn, responsive/a11y; API-data only for read-only contract clarification.

## Allowed Edit Roots

- Matching admin app route presentation
- Admin registration/team/payment feature `views/**`, `components/**`, `fixtures/**`, colocated UI tests
- Packet evidence/state.

## Forbidden Edit Roots

- Services/network hooks/wire schemas/query keys/shared API/auth/providers/UI/config; backend/frozen/normative roots.

## Implementation Steps

1. Approve route briefs and compare shadcn candidates for sidebar, data tables, filter bars, tabs, drawers, dialogs, and operational status.
2. Implement drilldown and explicit reason/next-action presentation.
3. Separate payment list, commercial detail, and advanced diagnostic views.
4. Cover loading/empty/filter-empty/403/409/422/5xx/stale/conflict/success/confirmation states.
5. Add marked provisional fixtures, focused tests, responsive table/action audits at all widths.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/features/admin src/app`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features/admin src/app`
- Audit widths `360`, `390`, `768`, `1024`, `1440`; no hover-only action or page overflow.

## Acceptance Criteria

- Team detail explains eligibility/roster state from presenter fixtures.
- Payment UI never derives a verdict from raw order/attempt fields.
- Candidate comparison, route states, and fixture-removal ledger are complete.

## Parallelism And Conflicts

- May run with other skeletons on distinct route/components; admin navigation changes are A0 requests.
- Shared table/UI primitives remain A0-owned.

## Rollback

Revert only these admin route/feature presentation files and fixtures.

## Apply Progress Output

Record page IDs/routes, briefs, shadcn candidates, states, fixture paths, files, skills, tests/viewports, A0 requests, rollback, API-04 handoff.

## Next Packet

- [API-04](../wave-03-api-integration/API-04-admin-operations-integration.md)
