# FND-08 - Consolidate API Clients, Query Keys, And Safe Cache Updates

## Purpose

Establish one client/key owner per dataset and remove unsafe optimistic helper behavior before real route integrations.

## Original Plan Tasks

- No direct source-plan ID. This required divergence packet supports all API integration packets and the real-contract cutover.

## Dependencies

- `FND-06`; payload/error behavior from `FND-07`; frozen endpoint/envelope contract.

## Mandatory Context

- `contract/next-app-architecture-contract.md`, API wrapper contract, schema DRY contract.
- Plan: frontend UX data rules and implementation section "do not inherit".
- Skill: `.opencode/skills/salesianos-api-data/SKILL.md` and `references/api-data-contract.md`; feature architecture skill for ownership boundaries.
- Frozen source cache/key/client files listed by the skill as read-only evidence.

## Allowed Edit Roots

- `Aplicacion/frontend/src/lib/api.ts` and shared query-client files (A0 only)
- Target canonical query/cache utility roots selected in the freeze record
- Direct focused tests; packet evidence/state.

## Forbidden Edit Roots

- Route pages/components and domain-specific service/schema implementation; backend; frozen roots; contracts/plan/docs; unrelated shared UI/config.

## Implementation Steps

1. Inventory duplicate clients/key namespaces and select one owner per backend dataset.
2. Define key factories and exported `queryOptions`; include every response-changing parameter.
3. Correct optimistic helpers to preserve exact paginated/list/detail shapes, snapshot/rollback on error, and invalidate on settle.
4. Remove orphan detail writes and unsafe array assumptions; prefer invalidation when exact shape is unknown.
5. Add focused key, invalidation, rollback, paginated-shape, and error tests.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx vitest run src/lib src/hooks src/utils`
- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx biome check src/lib src/hooks src/utils`

## Acceptance Criteria

- One transport owner and one query-key namespace exist per dataset.
- Optimistic updates cannot write arrays into paginated envelopes or leave stale/orphan entries.
- All mutations have explicit targeted invalidation or documented invalidation-only behavior.

## Parallelism And Conflicts

- Exclusive A0 packet for shared client/query/cache owners.
- No API integration packet starts until its key/client owner is frozen.

## Rollback

Revert consolidation and tests together; restore prior canonical owners from checkpoint without reintroducing duplicate production paths.

## Apply Progress Output

Record client/key ownership ledger, removed/retained paths, cache policies, files, contracts/skills, tests/commands, remaining duplication, rollback, and API packets unblocked.

## Next Packet

- `UI-01` through `UI-05` may proceed; API packets wait for matching backend contracts.
