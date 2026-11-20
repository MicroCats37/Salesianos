import { CancelledError } from "@tanstack/react-query";

/**
 * Whether a failure is the CANCELLATION of the request.
 *
 * When the component unmounts (or React Strict Mode mounts it twice, or the
 * query changes) the transport aborts the request. That is NOT a failure of
 * the backend: it is the browser closing a door.
 */
export function esCancelacion(error: unknown): boolean {
  const candidato = error as { name?: string; code?: string } | undefined;
  return (
    candidato?.name === "CanceledError" || candidato?.code === "ERR_CANCELED"
  );
}

/**
 * Turns the cancellation of the transport into the cancellation of TanStack.
 *
 * A cancelled request NEVER shows a toast and NEVER becomes the error state
 * of a surface: there is nothing to tell the operator.
 */
export function relanzarSiCancelacion(error: unknown): void {
  if (esCancelacion(error)) {
    throw new CancelledError();
  }
}
