# UI-01 - Build Public, Authentication, Account, And Recovery Skeletons

## Purpose

Create responsive presentation shells and visible states for public/account routes against feature-local provisional fixtures only.

## Original Plan Tasks

- No direct source-plan ID. This preparatory slice enables downstream `API-01`, which owns the original page-task mapping.

## Dependencies

- `GOV-02`, `FND-06`; form routes also require `FND-07`.

## Mandatory Context

- Contracts: `next-app-architecture-contract.md`, `smart.md`, API wrapper contract.
- Plan: page IDs/routes `PUB-01 /`, `PUB-02 /informacion`, `AUTH-01 /login`, `AUTH-02 /registro`, `ACCOUNT-01 /mi-cuenta`, `ACCOUNT-02 /mis-inscripciones`, `ACCOUNT-04 /mis-compras`, `ACCOUNT-05 /mis-compras/[id]`, `REC-01 /recuperar-compra`; frontend 01/02/06 and FL-01/02.
- Documentation: `03a`, `05a`, `07-guia-para-ui-ux.md` as current evidence.
- Skills in order: `salesianos-ui-ux`, `salesianos-feature-architecture`, `salesianos-forms-smart-fields` for auth/register/recovery forms, `salesianos-shadcn`, `salesianos-responsive-a11y`. Do not load API-data to create transport in this skeleton.

## Allowed Edit Roots

- Matching `Aplicacion/frontend/src/app/**` route pages/loading/error presentation
- Owning feature `views/**`, `components/**`, `fixtures/**`, and colocated UI tests
- Packet evidence/state.

## Forbidden Edit Roots

- `services/**`, network `hooks/**`, wire `schemas/**`, query-key `utils/**`, `src/lib/**`, auth/providers, `components/ui/**`, package/config/lock files, backend, frozen/normative roots.

## Implementation Steps

1. Produce/approve route briefs and compare shadcn candidates for navigation, forms, lists, status, empty states, and dialogs.
2. Implement thin route shells and feature views for all named IDs.
3. Cover loading, initial empty, filtered empty, recoverable error, validation, permission, success, partial payment, and neutral recovery response states.
4. Add `PROVISIONAL_CONTRACT_FIXTURE` adapters mirroring frozen examples; no prices/auth/business decisions.
5. Add component/navigation/form-state tests and five-width audits.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/app src/features --runInBand`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/app src/features`
- Audit widths `360`, `390`, `768`, `1024`, `1440`; keyboard, focus, labels/errors, overflow, reduced motion.

## Acceptance Criteria

- Every named route has its plan-defined purpose/actions/states and no invented catalog/payment/auth rule.
- shadcn comparison is recorded before composition; no shared primitive is overwritten.
- Provisional fixtures are local, typed, marked, and listed for deletion in API-01.

## Parallelism And Conflicts

- May run with backend domains and other skeletons on disjoint route/feature roots.
- A7 coordinates shared navigation requests through FND-06; do not edit shared files.

## Rollback

Revert only these route/feature presentation files and fixtures; shared shell remains intact.

## Apply Progress Output

Persist routes/page IDs, brief, shadcn candidate table/items, fixture paths, files, skills, tests/checks/viewports, shared-file requests, rollback, and API-01 handoff.

## Next Packet

- [API-01](../wave-03-api-integration/API-01-public-account-integration.md)
