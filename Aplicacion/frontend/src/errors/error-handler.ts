import type { AxiosError } from "axios";

import { parseFieldErrors } from "./field-errors";
import type { ApiError, ErrorParser } from "./types";

// =====================================================================
// BUILT-IN PARSERS (core — extensible via addErrorParser)
// =====================================================================

/**
 * Django Ninja / Pydantic (422 Unprocessable Entity)
 * Format: { detail: [{ loc: ["body", "field"], msg: "...", type: "..." }] }
 *
 * The per-field messages of this shape are read by `field-errors.ts`, which
 * normalizes every channel of the envelope into the `{ field: message }` map
 * that React Hook Form consumes.
 */

/**
 * Generic REST fallback
 * Format: { message: "..." } or { detail: "..." } or { error: { message, details } }
 * Also handles nested details: { error: { code, message, details: { non_field_errors, ... } } }
 */
const genericRestParser: ErrorParser = (_status, data: any) => {
  // Prefer the server-built, human-readable top-level `error.message`
  // when present (backend now concatenates NonFieldErrors + field errors with " • ").
  if (data?.error?.message && typeof data.error.message === "string" && data.error.message.length > 0) {
    return { message: data.error.message, status: _status };
  }

  // Django Ninja / Pydantic 422: `detail` is an ARRAY of per-field entries,
  // so the top-level string lookup below cannot read it.
  if (Array.isArray(data?.detail)) {
    const summary = data.detail
      .map((entry: any) => {
        const message =
          typeof entry?.msg === "string"
            ? entry.msg
            : typeof entry === "string"
              ? entry
              : undefined;
        if (!message) return "";
        const location = Array.isArray(entry?.loc)
          ? entry.loc.filter((part: unknown) => part !== "body")
          : [];
        const label = location.map((part: unknown) => String(part)).join(".");
        return label ? `${label}: ${message}` : message;
      })
      .filter((part: string) => part.length > 0)
      .join("; ");
    if (summary.length > 0) {
      return { message: summary, status: _status };
    }
  }

  // Handle nested error structure: { success: false, error: { code, message, details: { ... } } }
  if (data?.error?.details) {
    const details = data.error.details;
    // If details is an object with string values (e.g., { non_field_errors: "..." })
    // flatten them into a single display message
    if (typeof details === "object" && !Array.isArray(details)) {
      const detailMessages = Object.entries(details)
        .filter(([, v]) => typeof v === "string" && v.length > 0)
        .map(([k, v]) => {
          // Format key as readable label: non_field_errors -> Non field errors
          const label = k
            .replace(/_/g, " ")
            .replace(/\b\w/g, (c) => c.toUpperCase());
          return `${label}: ${v}`;
        });
      if (detailMessages.length > 0) {
        return { message: detailMessages.join("; "), status: _status };
      }
    }
    // If details is a string itself
    if (typeof details === "string" && details.length > 0) {
      return { message: details, status: _status };
    }
  }

  // Standard top-level message fields
  const msg =
    data?.errors?.message || data?.message || data?.detail || data?.error;
  if (typeof msg === "string") {
    return { message: msg, status: _status };
  }

  return null;
};

// =====================================================================
// PARSER CHAIN
// =====================================================================

const parsers: ErrorParser[] = [genericRestParser];

/**
 * Add a custom error parser to the chain.
 * Custom parsers are added to the FRONT of the chain (highest priority).
 *
 * @example
 * // In your project-specific setup:
 * addErrorParser((status, data: any) => {
 *   if (data?.code === "STRIPE_ERROR") {
 *     return { message: data.decline_message, status };
 *   }
 *   return null;
 * });
 */
export function addErrorParser(parser: ErrorParser) {
  parsers.unshift(parser);
}

// =====================================================================
// MAIN HANDLER
// =====================================================================

const DEFAULT_MESSAGES = {
  network: "Could not connect to the server. Please check your connection.",
  unknown: "An unexpected error occurred.",
  fallback: "An error occurred while processing the request.",
  validation: "Please correct the highlighted fields.",
};

/**
 * Processes any error (typically Axios) into a standardized ApiError.
 * Runs through the parser chain — first match wins.
 *
 * The field-level errors of the response are attached to EVERY result, no
 * matter which parser produced the message: the field channel of the frozen
 * envelope (`error.field_errors[]`) is read by `field-errors.ts` and travels
 * as `fieldErrors`, the map that React Hook Form's `setError` consumes.
 */
export function handleApiError(error: unknown): ApiError {
  const axiosError = error as AxiosError<unknown>;

  // No response at all (network error)
  if (!axiosError.response) {
    if (axiosError.request) {
      return { message: DEFAULT_MESSAGES.network, raw: error };
    }
    return {
      message: (axiosError as any)?.message || DEFAULT_MESSAGES.unknown,
      raw: error,
    };
  }

  const { status, data } = axiosError.response;

  const fieldErrors = parseFieldErrors(data);

  // Run parser chain
  for (const parser of parsers) {
    const result = parser(status, data);
    if (result) {
      return {
        ...result,
        ...(fieldErrors ? { fieldErrors } : {}),
        raw: error,
      };
    }
  }

  // Nothing matched
  return {
    message:
      fieldErrors && status === 422
        ? DEFAULT_MESSAGES.validation
        : DEFAULT_MESSAGES.fallback,
    status,
    ...(fieldErrors ? { fieldErrors } : {}),
    raw: error,
  };
}

/**
 * Convenience: always returns a string message.
 */
export function getErrorMessage(error: unknown): string {
  return handleApiError(error).message;
}
