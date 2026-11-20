/**
 * Shared helpers to read a Zod schema from the form layer.
 *
 * The form layer needs to know two things about a schema:
 *
 * 1. Which fields it DECLARES. A payload never carries an undeclared field.
 * 2. Which of those fields are FILE fields (see `imageField.ts`), because a
 *    file field has its own payload semantics: a `File` is a replacement, a
 *    `null` is a clear and a plain string is an existing URL, that is, no
 *    change at all.
 *
 * This module reads the schema WITHOUT evaluating it and WITHOUT throwing:
 * a malformed schema must never break the submit path.
 */

import type { z } from "zod";
import { isFileKindSchema } from "./imageField";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ZodTypeAny = z.ZodType<any, any, any>;

export { isFileKindSchema };

/**
 * Unwraps the wrappers that hide the object schema: `optional`, `nullable`,
 * `default`, `catch`, `pipe` and the effect wrappers.
 *
 * Returns the schema itself when it is not wrapped.
 */
function unwrapSchema(schema: unknown): unknown {
  let current = schema;

  // A bounded loop: a self-referencing schema must not spin forever.
  for (let depth = 0; depth < 8; depth += 1) {
    if (!current || typeof current !== "object") return current;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const def = (current as any)._def;
    if (!def) return current;

    // It is already an object schema.
    if (def.shape) return current;

    const inner =
      typeof def.innerType === "function" ? def.innerType() : def.innerType;
    if (inner && inner !== current) {
      current = inner;
      continue;
    }

    const unwrapped =
      typeof def.unwrap === "function" ? def.unwrap() : def.unwrap;
    if (unwrapped && unwrapped !== current) {
      current = unwrapped;
      continue;
    }

    const piped = typeof def.in === "function" ? def.in() : def.in;
    if (piped && piped !== current) {
      current = piped;
      continue;
    }

    return current;
  }

  return current;
}

/**
 * Resolves the TOP-LEVEL shape of a Zod schema.
 *
 * Returns an empty map when the schema is not an object schema: the callers
 * treat that as "the schema does not declare anything", never as "the payload
 * must be empty".
 */
export function getTopLevelShape(
  schema: unknown,
): Record<string, ZodTypeAny> {
  const resolved = unwrapSchema(schema);
  if (!resolved || typeof resolved !== "object") return {};

  // The public getter is the most reliable source across Zod versions.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const publicShape = (resolved as any).shape;
  if (publicShape && typeof publicShape === "object") {
    return publicShape as Record<string, ZodTypeAny>;
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const def = (resolved as any)._def;
  const shape = def?.shape;
  if (typeof shape === "function") {
    try {
      const value = shape();
      if (value && typeof value === "object") {
        return value as Record<string, ZodTypeAny>;
      }
    } catch {
      // A shape that cannot be resolved declares nothing.
    }
    return {};
  }

  if (shape && typeof shape === "object") {
    return shape as Record<string, ZodTypeAny>;
  }

  return {};
}

/**
 * Tells whether the schema declares a field with that name.
 *
 * A schema that declares NOTHING (it is not an object schema) does not
 * restrict the payload: every defined value travels.
 */
export function isDeclaredField(
  shape: Record<string, ZodTypeAny>,
  key: string,
): boolean {
  const declaredKeys = Object.keys(shape);
  if (declaredKeys.length === 0) return true;
  return Object.prototype.hasOwnProperty.call(shape, key);
}

/**
 * Returns the schema of a declared field, when the schema declares it.
 */
export function getFieldSchema(
  shape: Record<string, ZodTypeAny>,
  key: string,
): ZodTypeAny | undefined {
  if (!Object.prototype.hasOwnProperty.call(shape, key)) return undefined;
  return shape[key];
}
