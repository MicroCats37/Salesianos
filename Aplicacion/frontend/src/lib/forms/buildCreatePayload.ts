/**
 * Create payload mapping.
 *
 * The CREATE mapping is the FULL validated mapping: every declared field that
 * carries a value travels to the API.
 *
 * Rules:
 * - `undefined` → OMITTED. The field was never filled: it is absent, not null.
 * - `null` → INCLUDED. It is an explicit value, and for a nullable field it is
 *   the explicit "no value" the API expects.
 * - `File` → INCLUDED. The transport owns the multipart construction
 *   (`buildApiPayload`), never the form.
 * - A field that the schema does NOT declare → OMITTED. An undeclared field
 *   never travels.
 * - A FILE field whose value is a string → OMITTED. A string in a file field
 *   is the URL of the file that is ALREADY stored: there is nothing to upload.
 *
 * The create mapping NEVER diffs against the initial data: a create has no
 * previous state.
 */

import type { z } from "zod";
import {
  getFieldSchema,
  getTopLevelShape,
  isDeclaredField,
  isFileKindSchema,
} from "./schemaShape";

export function buildCreatePayload<T extends Record<string, unknown>>(
  values: T,
  schema: z.ZodType<T>,
): Partial<T> {
  const shape = getTopLevelShape(schema);
  const result: Partial<T> = {};

  for (const [key, value] of Object.entries(values)) {
    // Absent: the field was never filled.
    if (value === undefined) continue;

    // Undeclared: never travels.
    if (!isDeclaredField(shape, key)) continue;

    const fieldSchema = getFieldSchema(shape, key);
    if (fieldSchema && isFileKindSchema(fieldSchema)) {
      // An existing URL in a file field means "no change": nothing to upload.
      if (typeof value === "string") continue;
    }

    // `null` and `File` are values: they travel.
    result[key as keyof T] = value as T[keyof T];
  }

  return result;
}
