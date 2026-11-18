# UI-02 - Build Registration Wizard And Detail Skeletons

## Purpose

Build the registration wizard and owner detail/pool/team UI before real endpoints, using no browser-side registration rules.

## Original Plan Tasks

- No direct source-plan ID. Preparatory slice for downstream `API-02`.

## Dependencies

- `GOV-02`, `FND-06`, `FND-07`; frozen provisional registration presenter examples.

## Mandatory Context

- Contracts: next frontend architecture, Smart Fields, API wrapper.
- Plan: `SPORT-01 /inscripcion`, `ACCOUNT-03 /mis-inscripciones/[id]`; frontend 01/02/06, FL-03/04/05, RN-I01-I06.
- Documentation: `03a`, `05a`, `07` as current evidence.
- Skills in full relevant order: `salesianos-ui-ux -> salesianos-feature-architecture -> salesianos-forms-smart-fields -> salesianos-shadcn -> salesianos-responsive-a11y`; API-data is read-only contract context if fixture shape needs clarification.

## Allowed Edit Roots

- Matching target app route presentation
- Registration feature `views/**`, `components/**`, `fixtures/**`, colocated UI tests
- Packet evidence/state.

## Forbidden Edit Roots

- Services/network hooks/wire schemas/query keys/shared API/auth/providers/UI/config; backend/frozen/normative roots.

## Implementation Steps

1. Approve wizard/detail briefs and compare shadcn candidates for stepper, form, tabs, tables, drawers, confirmation, and status summaries.
2. Implement package/team/capacity/confirmation steps and detail sections Pool, Teams, Participants, Purchases, Benefits.
3. Render backend-projected reasons; fixture values are examples, never computed eligibility/capacity/price.
4. Cover loading/empty/error/422/409/permission/pending payment/indeterminate/success/closed-period states.
5. Add provisional fixture adapter, focused UI/form tests, and five-width audits.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/features/inscripciones src/app`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/features/inscripciones src/app`
- Audit widths `360`, `390`, `768`, `1024`, `1440`, including step navigation and responsive roster tables.

## Acceptance Criteria

- Wizard recovers a pending operation and never presents unpaid capacity as available.
- Detail distinguishes paid/assigned/available without calculating them in React.
- shadcn comparison and fixture deletion ledger are recorded.

## Parallelism And Conflicts

- Disjoint from backend and other feature roots; coordinate route overlap with UI-01 account navigation.
- No shared components/API/query keys may be edited.

## Rollback

Revert route/feature skeletons and provisional fixtures only.

## Apply Progress Output

Record page IDs/routes, brief, shadcn comparison, visible states, fixture paths, files, skills, tests/viewports, conflicts, rollback, API-02 handoff.

## Next Packet

- [API-02](../wave-03-api-integration/API-02-inscription-integration.md)
