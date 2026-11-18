# Salesianos Project Workflow

Read and follow relevant files in `contract/` before any implementation. Preserve backend ownership, API contracts, business rules, and documented functional behavior.

## UI/UX Agents

- Use `ui-ux-designer` first for a route-level brief and shadcn candidate comparison; it must not edit code.
- Use `ui-ux-implementer` only with an approved brief; it may edit frontend presentation files and relevant UI tests only.
- Use `ui-ux-reviewer` after implementation for a read-only responsive, accessibility, guideline, and functional-flow review.

## UI/UX Skills

- Load `salesianos-ui-ux` for route purpose, roles, actions, states, endpoint traceability, and visual direction.
- Load `salesianos-shadcn` before selecting or adding components; inspect `frontend/components.json` and use shadcn MCP first.
- Load `salesianos-responsive-a11y` before completion and audit widths 360, 390, 768, 1024, and 1440.
- Use the project-local vendor skills in `.agents/skills/` as required by each agent.

## Construction Workflow

Use this order, skipping only steps that are not in scope:

1. `salesianos-ui-ux` - always establish route purpose, actors, actions, states, and visual intent.
2. `salesianos-feature-architecture` - always for route, page, view, container, module, or feature construction.
3. `salesianos-api-data` - when endpoints, services, hooks, schemas, payloads, query keys, cache, mutations, or uploads are involved.
4. `salesianos-forms-smart-fields` - when forms, Smart Fields, validation, hydration, dependent fields, or file fields are involved.
5. `salesianos-shadcn` - when selecting, adding, replacing, or composing shadcn components.
6. `salesianos-responsive-a11y` - always before completion or review of UI work.

The legacy `.agent/skills/app-builder/` is a generic greenfield scaffolder and is not authoritative for Salesianos construction. Do not load it as a substitute for the project-local `salesianos-*` skills.
