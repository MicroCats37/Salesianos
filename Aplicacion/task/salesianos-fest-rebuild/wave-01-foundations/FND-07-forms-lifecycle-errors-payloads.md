# FND-07 - Correct Form Hydration, Server Errors, And Payload Semantics

## Purpose

Resolve the known GenericForm lifecycle and transport-mapping defects before route forms depend on them.

## Original Plan Tasks

- No direct source-plan ID. This is a required construction-divergence packet supporting downstream frontend integration packets.

## Dependencies

- `FND-06`; frozen error envelope from `GOV-01`.

## Mandatory Context

- `contract/smart.md`, `next-app-architecture-contract.md`, API wrapper contract.
- Plan: RN-A03, frontend UX error/form rules, API validation/status rules.
- Skills in order: `salesianos-ui-ux`, `salesianos-feature-architecture`, `salesianos-api-data`, `salesianos-forms-smart-fields`, `salesianos-responsive-a11y`.
- References: form smart-field matrix and API-data contract.
- Frozen source form/error/payload files as read-only evidence.

## Allowed Edit Roots

- `Aplicacion/frontend/src/components/genericForm/**`
- `Aplicacion/frontend/src/errors/**`
- `Aplicacion/frontend/src/lib/forms/**`
- `Aplicacion/frontend/src/utils/payload-builder.ts`
- Direct focused tests; packet evidence/state.

## Forbidden Edit Roots

- Pages/features/services/query keys; shared transport/auth/providers/UI config; backend; frozen roots; contracts/plan/docs.

## Implementation Steps

1. Add deterministic `reset(initialData)` behavior on record/data changes without dirty-value reset loops.
2. Parse Django 422 details into `fieldErrors` and call RHF `setError` exactly once per field.
3. Separate full validated create mappings from strict initial-data-aware update mappings.
4. Make Zod own coercion in manual/wizard modes; preserve `undefined`, nullable `null`, and File values.
5. Add focused hydration, create/update exact-shape, 422, coercion, and file-handoff tests.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/components/genericForm src/errors src/lib/forms src/utils`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/components/genericForm src/errors src/lib/forms src/utils/payload-builder.ts`

## Acceptance Criteria

- Edit forms rehydrate deterministically; create forms never use update-diff semantics.
- Backend field errors reach associated controls; no component-level ad hoc parser is required.
- Exact payload tests cover absent/null/create/update/file behavior.

## Parallelism And Conflicts

- Exclusive on generic form/error/payload roots.
- UI skeletons without forms may proceed; form-dependent skeletons wait.

## Rollback

Revert shared form implementation and its focused tests together.

## Apply Progress Output

Record divergence list, files, contracts/skills, exact behavior tests and commands, remaining workarounds, changed-line count, rollback, and affected frontend packets unblocked.

## Next Packet

- [FND-08](FND-08-query-cache-consolidation.md)
