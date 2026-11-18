# Form And Smart Field Decision Matrix

## GenericForm Modes

| Situation | Use | Avoid |
| --- | --- | --- |
| Production form with bespoke layout | Mode 1 `children` | Hand-rolled form state or automatic layout by convenience |
| Multi-step wizard | Mode 4 `formMethods` | One oversized form component |
| Small, single-purpose admin dialog | Mode 2 `fields` or Mode 3 `formSections` only with explicit contract compatibility | Quietly treating a current usage as canonical production policy |
| Editable record | `initialData` plus `methods.reset(initialData)` on identity/data change | Assuming `useForm` default values rehydrate |
| Create submit | Full validated create mapper | `buildUpdatePayload` diffing |
| Update submit | Strict update mapper using initial data | Sending untouched fields |
| Server 422 | Parse details -> `fieldErrors` -> `setError` | Component-level `try/catch` error invention |
| File field | Form emits `File`; mutation delegates to `salesianos-api-data` | Hand-built `FormData` in UI |

## Smart Field Recipe

1. Keep the visual control dumb: `value`, `onChange`, `onBlur`, disabled/loading, and visual error state.
2. Adapt it with `useController({ name, control })`.
3. Use `useWatch({ name: dependency, control })` only for required dependencies; never subscribe to the whole form.
4. Let Zod validate and coerce. Do not duplicate length, required, domain, price, eligibility, or capacity rules.
5. Let `DefaultFieldWrapper` own label/description/error for registered fields. A custom field must render its own associated markup because it bypasses that wrapper.
6. Debounce remote lookups and compare the response request key/sequence before `setValue` so stale responses cannot overwrite current input.
7. Populate options from a query hook, expose loading/empty/error states, and clear invalid dependent values deliberately.

## Value And Lifecycle Rules

| Value | Meaning |
| --- | --- |
| `undefined` | Untouched/omitted from update |
| `null` | Explicit clear, only for nullable backend fields |
| `""` | Preserve only when the API contract distinguishes it; do not assume it equals null |
| number/boolean/date | Coerce in Zod for Mode 1/4; do not rely on `FieldConfig.type` |
| `File` | Keep as `File` until mutation payload construction |

Reset when asynchronously loaded edit data arrives or when the edited record changes. Avoid reset loops: key the reset to stable record identity/data, and define whether dirty user input may be overwritten.

## Known Divergences

| CURRENT BEHAVIOR | TARGET RULE | REQUIRED AGENT ACTION |
| --- | --- | --- |
| `GenericForm` initializes from `initialData` once and does not reset | Edit forms rehydrate deterministically | Add reset behavior and hydration tests when in scope; otherwise reset in the owning form and report it |
| Error handling has no effective Django 422 `fieldErrors` parser | Backend field details reach RHF `setError` | Add/test the parser when in scope; otherwise do not claim server field mapping works |
| FieldConfig coercion runs only in automatic modes while production policy favors Mode 1 | Coercion is explicit and mode-independent through Zod | Use Zod coercion and test the submitted type |
| `buildUpdatePayload` ignores `initialData`/`strict` and GenericForm applies it to creates | Create and update have separate exact mappings | Bypass/fix the generic mapper with exact wire-shape tests; report remaining generic defect |

Evidence: `frontend/src/components/genericForm/GenericForm.tsx`, `frontend/src/components/genericForm/inputs/types.ts`, `frontend/src/components/genericForm/inputs/registry.ts`, `frontend/src/errors/error-handler.ts`, `frontend/src/lib/forms/`, `frontend/src/utils/payload-builder.ts`, and `contract/smart.md`.
