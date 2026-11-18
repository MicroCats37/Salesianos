---
name: salesianos-forms-smart-fields
description: "Trigger: Salesianos form, GenericForm, SmartField, FieldConfig, dependent select, wizard, edit hydration, validation, file field. Build correct forms."
license: Apache-2.0
metadata:
  author: "Salesianos"
  version: "1.0"
---

# Salesianos Forms Smart Fields

## Activation Contract

Use for forms, `GenericForm`, `SmartField`, `FieldConfig`, dependent/remote fields, wizards, edit hydration, server validation, or file fields. It does not own visual design, shadcn selection, or accessibility acceptance; use the three presentation skills for those concerns.

## Hard Rules

- Choose the `GenericForm` mode from `references/form-smart-field-matrix.md`; Zod owns validation and coercion truth.
- A Smart Field is a dumb-UI adapter: connect with `useController`, watch only named dependencies with `useWatch`, debounce remote work, guard stale responses, and never calculate business rules.
- Registry fields rely on the shared wrapper for label/error. A `customFields` field bypasses it and must render its own associated label, description, and error exactly once.
- Reset edit forms when `initialData` changes. Keep create and update mappings separate; `undefined` means untouched and `null` clears only nullable fields.
- Map backend 422 details to `fieldErrors` and RHF `setError`; components must not invent ad hoc API error parsing.
- Hand files to the mutation hook and load `salesianos-api-data`; never build multipart data in the form.

## Decision Gates

| Form need | Mode / pattern |
| --- | --- |
| Production form with custom layout | Mode 1 `children` |
| Multi-step wizard | Mode 4 `formMethods` |
| Small isolated admin dialog | Mode 2/3 only if current contract permits or deviation is explicit |
| Generic field reused by at least two consumers | Register globally |
| Domain-specific field | Inject through `customFields` |

| CURRENT BEHAVIOR | TARGET RULE | REQUIRED AGENT ACTION |
| --- | --- | --- |
| `GenericForm` misses reset; 422 parser misses `fieldErrors`; coercion differs by mode; `buildUpdatePayload` ignores `initialData`/`strict` and runs on creates | Reliable hydration, parsed field errors, explicit coercion, separate create/update mapping | Fix the in-scope divergence with tests, or explicitly avoid/work around it and report the deviation |

## Execution Steps

1. Identify mode, create/edit lifecycle, schema, initial data, dependencies, server errors, and file fields.
2. Define Zod coercion/nullability and distinct create/update mappings before UI wiring.
3. Implement dumb UI plus narrow RHF adapters; add debounce and stale-response guards for remote fields.
4. Wire reset and 422 field errors; hand file transport to `salesianos-api-data`.
5. Test validation failure, hydration/reset, coercion, exact submit mapping, server field errors, dependencies, and file handoff.

## Output Contract

Return form mode, schema/coercion/nullability, Smart Field ownership, hydration/error flow, create/update mapping, file handoff, tests, and explicit divergences.

## References

- `references/form-smart-field-matrix.md`
- `../../../contract/smart.md`
- `../../../contract/next-app-architecture-contract.md`
- `../salesianos-api-data/references/api-data-contract.md`
