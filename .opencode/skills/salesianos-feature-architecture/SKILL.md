---
name: salesianos-feature-architecture
description: "Trigger: Salesianos feature, route, page, view, container, module, feature folder. Build frontend features with the required layer boundaries."
license: Apache-2.0
metadata:
  author: "Salesianos"
  version: "1.0"
---

# Salesianos Feature Architecture

## Activation Contract

Use when creating or restructuring a Salesianos route, page, view, container, module, or feature folder. Do not use it to choose visual direction, shadcn components, or accessibility acceptance; those belong to `salesianos-ui-ux`, `salesianos-shadcn`, and `salesianos-responsive-a11y`.

## Hard Rules

- Before editing, read relevant `contract/`, existing source, and `Aplicacion/documentacion/03a-*`, `03b-*`, `05a-*`, and `07-*` route evidence.
- Edit the frontend root selected for the current task. Keep `app/**` routing-only and `'use client'` at the lowest interactive boundary.
- Enforce: route page -> feature view/container -> components -> hooks -> services -> schemas; keep colocated tests with each changed layer.
- Keep transport and business rules out of pages and components. Never use raw `fetch`; delegate API construction to `salesianos-api-data`.
- Never add to `_legacy-*`, target `Aplicacion/frontend`, or cite deleted `features-app-example` / `features-example-app` as a pattern.
- Use granular named exports; no wildcard or global feature barrels. Preserve backend ownership of price, eligibility, capacity, payment, roster, and transitions.

## Decision Gates

| Situation | Decision |
| --- | --- |
| Same domain, endpoint, schema, permissions, and shared behavior | Reuse or extend the existing feature |
| Same domain but distinct admin/public endpoint, permission, or schema | Add the namespaced variant within that domain |
| New cohesive domain/use case with no owner | Create a feature with only the layers it needs |
| Reuse would create cross-domain coupling | Keep separate features and share only proven cross-feature primitives |

| CURRENT BEHAVIOR | TARGET RULE | REQUIRED AGENT ACTION |
| --- | --- | --- |
| A legacy copy or stale scaffold is present | The user-selected frontend root and current feature code are authoritative | Do not cite legacy scaffolding as a pattern; report only a concrete conflict with the current task |

## Execution Steps

1. Record route, actors, actions, states, existing owner, and endpoints from the required evidence.
2. Inspect current feature consumers before choosing reuse, extension, or creation.
3. Map every file to route, view/container, component, hook, service, schema, utility, or test ownership.
4. Implement from contracts inward, keeping pages thin and tests colocated.
5. Verify focused typecheck, tests, and lint; report any architecture deviation.

## Output Contract

Return route scope, reuse/create decision, layer/file map, endpoint dependencies, tests/checks, and explicit deviations or blocked backend-owned work.

## References

- `references/pattern-catalogue.md`
- `../../../contract/next-app-architecture-contract.md`
- `../../../Aplicacion/documentacion/03a-paginas-publicas-y-compra.md`
- `../../../Aplicacion/documentacion/03b-paginas-administrativas-y-operativas.md`
- `../../../Aplicacion/documentacion/05a-matriz-pagina-flujo-endpoint-datos.md`
- `../../../Aplicacion/documentacion/07-guia-para-ui-ux.md`
