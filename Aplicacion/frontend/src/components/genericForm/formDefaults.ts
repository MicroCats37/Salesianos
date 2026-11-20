// genericForm/formDefaults.ts
//
// The DEFAULTS of a form: the values it is hydrated with, and the values it
// is RESET to when the record it edits changes.
//
// The same builder is used for the first hydration (`useForm`) and for every
// reset, so the two can never disagree.

import type {
  DefaultValues,
  FieldValues,
  Path,
  PathValue,
} from "react-hook-form";
import type { FormField } from "./GenericInput";

/**
 * Builds the default values of a form.
 *
 * The `initialData` of the record wins; a field that the record does not
 * carry falls back to the `defaultValue` declared in its configuration.
 */
export function buildFormDefaults<T extends FieldValues>(
  initialData: DefaultValues<T> | undefined,
  fields: readonly FormField[],
): DefaultValues<T> {
  const defaults = { ...(initialData ?? {}) } as DefaultValues<T>;

  for (const field of fields) {
    const name = field.name as Path<T>;
    if (Object.hasOwn(defaults, name)) continue;
    if (field.defaultValue === undefined) continue;

    defaults[name] = (
      field.type === "radio" || field.type === "select"
        ? String(field.defaultValue)
        : field.defaultValue
    ) as PathValue<T, Path<T>>;
  }

  return defaults;
}
