import { getErrorMessage } from "@/errors";
import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";

/**
 * The errors of the registration area.
 *
 * Two rules travel here:
 *
 * 1. The TEXT of a failure lives in `error.message` of the frozen envelope
 *    and it is the PUBLIC prose of the backend catalog. The frontend prints
 *    it verbatim and never invents a translation of it.
 * 2. The frontend branches on the HTTP STATUS, never on the machine code:
 *    the catalogue of public codes is not closed (33 codes are still open),
 *    so a component that decided what a code means would break with the next
 *    code the backend catalogues (contract/api-wrapper-presenter-contract.md
 *    §8).
 */

/**
 * The HTTP status of a failure, when the error carries one.
 *
 * `ApiQueryError` exposes it directly; an axios error carries it inside
 * `response`.
 */
export function statusDeError(error: unknown): number | undefined {
  const candidate = error as
    | { status?: number; response?: { status?: number } }
    | undefined;

  return candidate?.status ?? candidate?.response?.status;
}

/**
 * Turns a failure of a READ into an `ApiQueryError`.
 *
 * The read carries the status so that the view can tell a PERMISSION answer
 * (403) from a recoverable failure, and the message so that the view can
 * print the words of the server.
 *
 * A MUTATION never goes through this helper: it must propagate the ORIGINAL
 * error, because the 422 field errors travel in it and the form needs them
 * to mark the control that owns the field.
 */
export async function leerConEstado<T>(
  operacion: () => Promise<T>,
): Promise<T> {
  try {
    return await operacion();
  } catch (error) {
    throw new ApiQueryError(getErrorMessage(error), statusDeError(error));
  }
}
