# FND-06 - Build The Target Frontend Shell And Shared Providers

## Purpose

Create the serialized target route groups, navigation, auth presentation boundary, API transport owner, global providers, and shared UI baseline.

## Original Plan Tasks

- `T-017`.

## Dependencies

- `GOV-02`; A0 owns all shared frontend files.

## Mandatory Context

- `contract/next-app-architecture-contract.md`, `smart.md`, API wrapper contract.
- Plan: `frontend/01-mapa-rutas-y-navegacion.md`, `frontend/06-sistema-ux-ui.md`, auth contract, implementation architecture.
- Documentation: `03a`, `03b`, `05a`, `07-guia-para-ui-ux.md` as current evidence.
- Skills in order: `salesianos-ui-ux`, `salesianos-feature-architecture`, `salesianos-api-data`, `salesianos-shadcn`, `salesianos-responsive-a11y`.
- Agent workflow: `.opencode/agents/ui-ux-designer.md`, implementer, reviewer.

## Allowed Edit Roots

- `Aplicacion/frontend/src/app/**` shell/layout files
- `Aplicacion/frontend/src/lib/api.ts`, shared auth/providers/query client
- `Aplicacion/frontend/src/components/ui/**` and shell components
- `Aplicacion/frontend/{package.json,package-lock.json,components.json,biome.json,tsconfig*.json,next.config.ts,postcss.config.mjs,vitest*.ts}`
- Directly relevant tests; packet evidence/state.

## Forbidden Edit Roots

- Feature route implementations beyond shell placeholders; backend; frozen roots; contracts/plan/docs; secrets; generated dependencies.

## Implementation Steps

1. Obtain route-level brief and shadcn candidate comparison before editing.
2. Establish routing-only app structure, public/account/admin layouts, navigation, providers, and lowest interactive boundaries.
3. Establish one transport/query-client/auth owner without domain endpoints or mock business data.
4. Add shared UI items only through shadcn MCP review; preserve local customizations.
5. Add shell/navigation tests and five-width responsive/accessibility checks.

## Tests And Checks

- Workdir `Aplicacion/frontend`: `npx tsc --noEmit`
- Workdir `Aplicacion/frontend`: `npx vitest run src/app src/components`
- Workdir `Aplicacion/frontend`: `npx biome check src/app src/components src/lib`
- Manual/browser audit: widths `360`, `390`, `768`, `1024`, `1440`.

## Acceptance Criteria

- Shell navigation reflects plan actors/modules and does not invent enabled modules.
- Shared transport/auth/providers/components have one A0 owner.
- Keyboard, focus, labels, overflow, and reduced-motion behavior are specified/tested.

## Parallelism And Conflicts

- Exclusive on all shared frontend/config files.
- Feature skeleton packets start only after this packet and may not touch these roots.

## Rollback

Revert shell/config/dependency work unit together; do not remove unrelated generated or pre-existing files.

## Apply Progress Output

Persist task, approved brief, shadcn candidates/items/commands, files/config changes, contracts/skills, tests/checks/viewports, deviations, rollback, and skeleton packets unblocked.

## Next Packet

- [FND-07](FND-07-forms-lifecycle-errors-payloads.md), then skeleton packets by dependency.
