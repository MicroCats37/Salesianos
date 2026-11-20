/**
 * Value equality used by the strict update mapping.
 *
 * The strict update mapper omits the values that the user did NOT touch. A
 * touched value is a value that is DIFFERENT from the one the record was
 * hydrated with, so the comparison has to understand the three value kinds a
 * form carries:
 *
 * - Primitives: compared by value (`Object.is`).
 * - `Date`: compared by instant, not by reference.
 * - `File`: compared by IDENTITY. Two different `File` objects with the same
 *   name and size are two different uploads.
 * - Plain objects and arrays: compared structurally.
 */

function isPlainObject(value: unknown): value is Record<string, unknown> {
  if (typeof value !== "object" || value === null) return false;
  if (Array.isArray(value)) return false;
  if (value instanceof Date) return false;
  if (typeof File !== "undefined" && value instanceof File) return false;
  if (typeof Blob !== "undefined" && value instanceof Blob) return false;
  const proto = Object.getPrototypeOf(value);
  return proto === Object.prototype || proto === null;
}

/**
 * Tells whether two form values mean the same thing.
 */
export function isSameFormValue(a: unknown, b: unknown): boolean {
  if (Object.is(a, b)) return true;

  if (a instanceof Date || b instanceof Date) {
    if (!(a instanceof Date) || !(b instanceof Date)) return false;
    return a.getTime() === b.getTime();
  }

  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b)) return false;
    if (a.length !== b.length) return false;
    return a.every((item, index) => isSameFormValue(item, b[index]));
  }

  if (isPlainObject(a) && isPlainObject(b)) {
    const aKeys = Object.keys(a).filter((key) => a[key] !== undefined);
    const bKeys = Object.keys(b).filter((key) => b[key] !== undefined);
    if (aKeys.length !== bKeys.length) return false;
    return aKeys.every(
      (key) => Object.hasOwn(b, key) && isSameFormValue(a[key], b[key]),
    );
  }

  return false;
}
