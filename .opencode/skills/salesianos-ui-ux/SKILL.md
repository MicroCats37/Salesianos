---
name: salesianos-ui-ux
description: "Trigger: Salesianos UI, route design, page redesign, frontend UX. Design route-level UI without changing contracts or behavior."
license: MIT
metadata:
  author: "Salesianos"
  version: "1.0.0"
---

# Salesianos UI/UX

## Activation Contract

Use for any Salesianos route, page, flow, or presentation-layer design or implementation.

## Hard Rules

- Read relevant files in `contract/` before proposing or changing UI.
- Preserve backend ownership, API/service contracts, business rules, and existing functional behavior.
- Start from the route purpose, users and roles, primary actions, states, and service/endpoint contracts.
- Define a specific visual direction and reusable tokens before coding. Reject generic dashboard, card-grid, gradient, and placeholder-heavy AI layouts.
- Treat the frozen previous frontend as visual evidence, not as an implementation source. Preserve recognizable brand identity while improving hierarchy, accessibility, responsive behavior, and consistency.
- Define brand and semantic design tokens globally. Never specify literal colors per component when a shared role such as primary, surface, border, success, warning, or destructive can express the intent.

## Decision Gates

| Scope                               | Required source                                                        |
| ----------------------------------- | ---------------------------------------------------------------------- |
| Public or purchase route            | `Aplicacion/documentacion/03a-paginas-publicas-y-compra.md`            |
| Administrative or operational route | `Aplicacion/documentacion/03b-paginas-administrativas-y-operativas.md` |
| Data or endpoint uncertainty        | `Aplicacion/documentacion/05a-matriz-pagina-flujo-endpoint-datos.md`   |
| Any visual change                   | `Aplicacion/documentacion/07-guia-para-ui-ux.md`                       |
| Existing visual identity            | Inspect the frozen previous frontend; convert useful values to tokens  |
| New or changed color                | Assign a semantic global token before component implementation         |

## Execution Steps

1. Identify the route, actors, permissions, job-to-be-done, and success outcome.
2. Trace every visible action and state to its existing service and endpoint.
3. Enumerate initial, loading, empty, error, validation, success, and permission states.
4. Set visual direction, typography, semantic color roles, spacing, density, hierarchy, and interaction tokens. Map retained legacy identity to the new token system.
5. Design the smallest coherent route flow that preserves documented behavior.
6. Validate the proposal against the route-flow matrix and UI/UX guide before implementation.

## Output Contract

Return route scope, user/action model, invariant behavior, state matrix, visual direction, legacy identity retained, semantic token additions, responsive intent, and unresolved contract questions.

## References

- `contract/`
- `Aplicacion/documentacion/03a-paginas-publicas-y-compra.md`
- `Aplicacion/documentacion/03b-paginas-administrativas-y-operativas.md`
- `Aplicacion/documentacion/05a-matriz-pagina-flujo-endpoint-datos.md`
- `Aplicacion/documentacion/07-guia-para-ui-ux.md`
