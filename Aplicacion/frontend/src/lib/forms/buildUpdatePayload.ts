/**
 * Build Update Payload Helper
 *
 * Constructs a partial-update payload from form values, initial data, and a Zod schema.
 *
 * Rules:
 * - Omits `undefined` values (field not touched)
 * - For fields with metadata `kind: "file"`:
 *   - string URL value → omitted (no change)
 *   - File value → included (replace)
 *   - null value → included (clear/remove)
 *   - undefined → omitted (no change)
 * - For the other fields, when the mapping is STRICT (the default), a value
 *   that is EQUAL to the one in `initialData` is omitted: the user did not
 *   touch it, and an update never repeats the state it already has.
 *
 * Zod v4 note: We use a Symbol-keyed property to detect file-kind schemas.
 * See `imageField.ts` for the metadata convention.
 */

import type { z } from "zod";
import {
  getFieldSchema,
  getTopLevelShape,
  isDeclaredField,
  isFileKindSchema,
} from "./schemaShape";
import { isSameFormValue } from "./valueEquality";

// ── Main function ─────────────────────────────────────────────────────────────

export interface BuildUpdatePayloadOptions {
  /**
   * When `true` (the default), a value that is EQUAL to the one in
   * `initialData` is omitted: the field was not touched.
   *
   * When `false`, every defined value travels, including the ones that did
   * not change.
   */
  strict?: boolean;
}

/**
 * Build a partial update payload from form values + initial data + schema.
 *
 * @param values   Current form values (may include File, string URLs, null, undefined)
 * @param initialData  Original data (for comparison)
 * @param schema   Zod schema (used to identify file-kind fields)
 * @param options  Optional configuration
 */
export function buildUpdatePayload<T extends Record<string, unknown>>(
  values: T,
  initialData: Partial<T> | undefined,
  schema: z.ZodType<T>,
  options: BuildUpdatePayloadOptions = {},
): Partial<T> {
  const strict = options.strict ?? true;
  const shape = getTopLevelShape(schema);
  const result: Partial<T> = {};

  for (const [key, value] of Object.entries(values)) {
    // Always omit undefined (field not touched)
    if (value === undefined) {
      continue;
    }

    // An undeclared field never travels.
    if (!isDeclaredField(shape, key)) {
      continue;
    }

    // Find corresponding schema entry
    const fieldSchema = getFieldSchema(shape, key);

    if (fieldSchema && isFileKindSchema(fieldSchema)) {
      // File-kind field handling
      if (typeof value === "string") {
        // string URL = no change, omit
        continue;
      }
      // File (replace) or null (clear) → include
      result[key as keyof T] = value as T[keyof T];
      continue;
    }

    // Non-file field: in the strict mapping, an untouched value is omitted.
    if (
      strict &&
      initialData &&
      Object.hasOwn(initialData, key) &&
      isSameFormValue(value, initialData[key])
    ) {
      continue;
    }

    result[key as keyof T] = value as T[keyof T];
  }

  return result;
}
