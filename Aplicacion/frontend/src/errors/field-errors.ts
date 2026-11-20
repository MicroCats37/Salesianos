/**
 * Field-level error parsing.
 *
 * The Salesianos error envelope (`FREEZE-ENV-1.0.0`, evidence
 * `evidence/contracts/FR-01-envelope-error-pagination.md`) declares ONE
 * channel for field-level errors:
 *
 *     error.field_errors: [ { field, code, message } ]
 *
 * `field` is a DOTTED path (`beneficiarios.0.documento`) and `error.details`
 * carries NON-field context only.
 *
 * Two OTHER wire formats answer a 422 in this codebase and are read here as
 * well, because they are DIFFERENT wire formats, not a second use of the
 * `details` channel:
 *
 * - Django Ninja / Pydantic: `{ detail: [{ loc: ["body", "field"], msg }] }`.
 * - DRF-style flat mapping: `{ errors: { field: ["message"] } }` and the
 *   legacy `{ details: { field: "message" } }` produced by the old
 *   `format_errors()` helper.
 *
 * `non_field_errors` is NOT a field: it belongs to the form-level message and
 * never becomes a control error.
 *
 * The output is the `{ field: message }` map that React Hook Form's
 * `setError` consumes, so NO component has to parse an API error on its own.
 */

export interface FieldErrorEntry {
  /** Dotted path of the field, the shape React Hook Form expects. */
  field: string;
  /** Stable machine-readable code, when the server sent one. */
  code?: string;
  /** Public, safe message for the field. */
  message: string;
}

/** The key that marks a form-level (non-field) error. */
export const NON_FIELD_ERRORS_KEY = "non_field_errors";

/** Separator used when a field carries more than one message. */
const MULTIPLE_MESSAGES_SEPARATOR = " • ";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readMessage(value: unknown): string | undefined {
  if (typeof value === "string" && value.trim().length > 0) return value;
  if (Array.isArray(value)) {
    const messages = value
      .map(readMessage)
      .filter((message): message is string => Boolean(message));
    if (messages.length > 0) return messages.join(MULTIPLE_MESSAGES_SEPARATOR);
  }
  return undefined;
}

/**
 * Builds the dotted path of a field from a Django/Pydantic `loc` array.
 *
 * The first segment is the SOURCE of the error (`body`, `query`, `path`) and
 * is not part of the field path.
 */
export function fieldPathFromLocation(location: unknown): string | undefined {
  if (!Array.isArray(location)) return undefined;

  const segments = location.filter(
    (segment) =>
      segment !== "body" &&
      segment !== "query" &&
      segment !== "path" &&
      segment !== "form",
  );

  if (segments.length === 0) return undefined;

  const path = segments
    .map((segment) =>
      typeof segment === "number" ? String(segment) : String(segment),
    )
    .join(".");

  return path.length > 0 ? path : undefined;
}

/**
 * Reads the frozen `field_errors[]` channel.
 */
function entriesFromFieldErrorList(list: unknown): FieldErrorEntry[] {
  if (!Array.isArray(list)) return [];

  const entries: FieldErrorEntry[] = [];

  for (const item of list) {
    if (!isRecord(item)) continue;

    const field = typeof item.field === "string" ? item.field.trim() : "";
    if (!field || field === NON_FIELD_ERRORS_KEY) continue;

    const message = readMessage(item.message);
    if (!message) continue;

    const code = typeof item.code === "string" ? item.code : undefined;
    entries.push({ field, message, ...(code ? { code } : {}) });
  }

  return entries;
}

/**
 * Reads the Django Ninja / Pydantic `detail[]` channel.
 */
function entriesFromDetailList(list: unknown): FieldErrorEntry[] {
  if (!Array.isArray(list)) return [];

  const entries: FieldErrorEntry[] = [];

  for (const item of list) {
    if (typeof item === "string") {
      // A plain string carries no field: it is a form-level message.
      continue;
    }
    if (!isRecord(item)) continue;

    const field = fieldPathFromLocation(item.loc);
    if (!field) continue;

    const message = readMessage(item.msg);
    if (!message) continue;

    const code = typeof item.type === "string" ? item.type : undefined;
    entries.push({ field, message, ...(code ? { code } : {}) });
  }

  return entries;
}

/**
 * Reads a flat `{ field: message }` mapping (DRF style and the legacy
 * `format_errors()` shape).
 */
function entriesFromFlatMap(map: unknown): FieldErrorEntry[] {
  if (!isRecord(map)) return [];

  const entries: FieldErrorEntry[] = [];

  for (const [key, value] of Object.entries(map)) {
    const field = key.trim();
    if (!field || field === NON_FIELD_ERRORS_KEY) continue;

    const message = readMessage(value);
    if (!message) continue;

    entries.push({ field, message });
  }

  return entries;
}

/**
 * Reads EVERY field-level error carried by a response body.
 *
 * The channels are read in the order of the contract, and the FIRST channel
 * that carries errors wins: the frozen envelope is authoritative, the legacy
 * shapes are the fallback for the endpoints that still answer in the old
 * format.
 */
export function parseFieldErrorEntries(data: unknown): FieldErrorEntry[] {
  if (!isRecord(data)) return [];

  const error = isRecord(data.error) ? data.error : undefined;

  // 1. The frozen channel: `error.field_errors[]`.
  const frozen = entriesFromFieldErrorList(error?.field_errors);
  if (frozen.length > 0) return frozen;

  // A body that carries the channel at the root.
  const rootFrozen = entriesFromFieldErrorList(data.field_errors);
  if (rootFrozen.length > 0) return rootFrozen;

  // 2. Django Ninja / Pydantic: `detail[]`.
  const detail = entriesFromDetailList(data.detail);
  if (detail.length > 0) return detail;

  // 3. DRF style: `errors{}`.
  const drf = entriesFromFlatMap(data.errors);
  if (drf.length > 0) return drf;

  // 4. The legacy flat mapping that the old backend produced.
  const legacy = entriesFromFlatMap(error?.details);
  if (legacy.length > 0) return legacy;

  const rootLegacy = entriesFromFlatMap(data.details);
  if (rootLegacy.length > 0) return rootLegacy;

  return [];
}

/**
 * Normalizes the field-level errors of a response body into the
 * `{ field: message }` map that React Hook Form's `setError` consumes.
 *
 * A field that carries several messages keeps all of them, joined by the
 * same separator the backend uses for its own aggregates.
 */
export function parseFieldErrors(
  data: unknown,
): Record<string, string> | undefined {
  const entries = parseFieldErrorEntries(data);
  if (entries.length === 0) return undefined;

  const fieldErrors: Record<string, string> = {};

  for (const entry of entries) {
    const previous = fieldErrors[entry.field];
    fieldErrors[entry.field] = previous
      ? `${previous}${MULTIPLE_MESSAGES_SEPARATOR}${entry.message}`
      : entry.message;
  }

  return fieldErrors;
}
