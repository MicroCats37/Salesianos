/**
 * Deterministic serialization used to detect a CHANGE of the data a form is
 * hydrated with.
 *
 * The edit lifecycle needs to know whether `initialData` really changed. A
 * reference comparison is not enough: a parent that rebuilds the object on
 * every render would look like a new record and would reset the form on every
 * keystroke. A content comparison is enough, and it must be STABLE: two
 * objects with the same content have to serialize to the same string, no
 * matter the order in which their keys were written.
 */

/**
 * Normalizes a value into a JSON-safe structure with sorted keys.
 */
function normalize(value: unknown): unknown {
  if (value === null) return null;

  if (value instanceof Date) {
    return { __type: "date", value: value.toISOString() };
  }

  if (typeof File !== "undefined" && value instanceof File) {
    return {
      __type: "file",
      name: value.name,
      size: value.size,
      type: value.type,
      lastModified: value.lastModified,
    };
  }

  if (typeof Blob !== "undefined" && value instanceof Blob) {
    return { __type: "blob", size: value.size, type: value.type };
  }

  if (Array.isArray(value)) {
    return value.map(normalize);
  }

  if (typeof value === "object") {
    const source = value as Record<string, unknown>;
    const result: Record<string, unknown> = {};

    for (const key of Object.keys(source).sort()) {
      const entry = source[key];
      if (entry === undefined) continue;
      result[key] = normalize(entry);
    }

    return result;
  }

  if (typeof value === "function" || typeof value === "symbol") {
    return undefined;
  }

  return value;
}

/**
 * Serializes a value into a deterministic string.
 *
 * The output only changes when the CONTENT changes.
 */
export function stableSerialize(value: unknown): string {
  const normalized = normalize(value);
  if (normalized === undefined) return "undefined";
  return JSON.stringify(normalized) ?? "undefined";
}
