/**
 * Typed errors of the checkout preparation.
 *
 * The operator must read the PUBLIC message that the backend publishes in its
 * error catalog — never a raw HTTP status string ("Request failed with status
 * code 409"). The stable code travels with the message so the failure can be
 * identified without exposing any internal identifier.
 *
 * Dependency-light on purpose: the module resolves the message through the
 * shared error handler (`@/errors`) so the checkout never parses a response
 * body on its own.
 */

import { handleApiError } from "@/errors";
import type { ApiError } from "@/types/api.types";

/**
 * A typed preparation error: the public message of the API plus the stable
 * code that identifies it.
 */
export interface ErrorPreparacion {
  /** Stable code of the backend error (`error.code`) — null when unknown. */
  code: string | null;
  /** Public message of the API — NEVER a raw HTTP status string. */
  message: string;
}

/** Public message used when the API does not publish one. */
export const MENSAJE_PREPARACION_POR_DEFECTO =
  "No se pudo iniciar el pago. Inténtalo nuevamente en unos minutos.";

/**
 * Reads the stable code of an error thrown by the API client.
 *
 * The code lives in the body of the response (`error.code`); the shared error
 * handler only publishes the message, so the code is read from the raw error.
 */
function codigoDeError(error: unknown): string | null {
  const respuesta = (error as { response?: { data?: unknown } })?.response
    ?.data;
  const codigo = (respuesta as { error?: { code?: unknown } } | undefined)
    ?.error?.code;
  return typeof codigo === "string" && codigo.length > 0 ? codigo : null;
}

/**
 * Builds the typed error of a preparation that failed with an HTTP error.
 *
 * The message comes from the shared error handler: it resolves the public
 * message of the API and falls back to a safe generic message. It NEVER
 * returns the raw status text of the HTTP client.
 */
export function errorDeExcepcion(error: unknown): ErrorPreparacion {
  const apiError = handleApiError(error);
  const mensaje = apiError.message?.trim() ?? "";

  return {
    code: codigoDeError(apiError.raw ?? error),
    message: mensaje || MENSAJE_PREPARACION_POR_DEFECTO,
  };
}

/**
 * Builds the typed error of a preparation that failed INSIDE the envelope.
 *
 * The envelope carries the error of the API already typed (`code` + `message`):
 * nothing is parsed here, the values are used as they arrive.
 */
export function errorDeEnvoltura(
  error: ApiError | null | undefined,
): ErrorPreparacion | null {
  if (!error) return null;

  const mensaje = typeof error.message === "string" ? error.message.trim() : "";
  if (!mensaje) return null;

  return {
    code:
      typeof error.code === "string" && error.code.length > 0
        ? error.code
        : null,
    message: mensaje,
  };
}
