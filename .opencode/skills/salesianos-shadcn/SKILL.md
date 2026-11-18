---
name: salesianos-shadcn
description: "Trigger: shadcn, UI component, block, Sidebar, dialog, form, table. Select and integrate current shadcn source safely in Salesianos."
license: MIT
metadata:
  author: "Salesianos"
  version: "1.0.0"
---

# Salesianos shadcn

## Activation Contract

Use before selecting, adding, replacing, or composing any shadcn component or block.

## Hard Rules

- Inspect `Aplicacion/frontend/components.json` first. Do not reconfigure or duplicate the shadcn MCP.
- Use shadcn MCP before building a custom component. The standard `@shadcn` registry needs no explicit registry entry.
- Compare official components and blocks, including Sidebar variants when navigation is involved.
- Justify selection from route UX, user roles, information density, and mobile behavior.
- Never overwrite a customized local component blindly. Compose and customize current source after adding instead of recreating stale source.
- Define reusable brand, surface, border, state, chart, light-theme, and dark-theme values as semantic CSS variables in `Aplicacion/frontend/src/app/globals.css`.
- Components MUST consume semantic Tailwind/shadcn classes such as `bg-primary`, `text-muted-foreground`, and `border-border`. Reject literal hex/RGB/HSL values and arbitrary or palette color utilities such as `bg-[#...]` or `text-red-500`, unless the value is genuinely runtime data and the exception is documented.
- Keep layout, spacing, and responsive Tailwind utilities local to components; do not move component layout rules into the global theme.
- Any CLI fallback MUST include `-c Aplicacion/frontend`.

## Decision Gates

| Situation                     | Action                                           |
| ----------------------------- | ------------------------------------------------ |
| Suitable official item exists | Add, compose, and adapt it                       |
| Local customized item exists  | Diff first; preserve intentional behavior        |
| No suitable item exists       | Build the smallest accessible custom composition |
| Missing semantic visual role  | Add one global token, then consume that role      |
| Literal component color found | Replace it with the matching semantic token       |

## Execution Steps

1. Call `get_project_registries`.
2. Call `search_items_in_registries` for components and blocks that fit the route.
3. Call `view_items_in_registries` and `get_item_examples_from_registries` to preview and compare source, variants, dependencies, roles, and mobile behavior.
4. Inspect the local target and current diff before adding. Do not accept an overwrite without reviewing the customized source.
5. Call `get_add_command_for_items`; prefer the returned command. If MCP cannot add, use the CLI with `-c Aplicacion/frontend`.
6. Add or reuse semantic theme variables in `Aplicacion/frontend/src/app/globals.css` before styling components; preserve coherent light and dark mappings.
7. Compose and customize the added source within project presentation boundaries using semantic classes only.
8. Search the changed presentation files for hardcoded colors, inspect the generated diff, and call `get_audit_checklist` before completion.

## Output Contract

Return compared candidates, selected item and rationale, command used, affected files, global tokens added or reused, hardcoded-color audit, preserved customizations, and audit result.

## References

- `Aplicacion/frontend/components.json`
- `Aplicacion/frontend/src/app/globals.css`
- `Aplicacion/documentacion/07-guia-para-ui-ux.md`
- `contract/`
