import { z } from "zod";
import { handleApiError } from "@/errors";
import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";

/**
 * Shared transport of the pass feature.
 *
 * Every request of the feature travels through `pedir`: the answer is
 * validated with the Zod mirror of the backend wrapper and the failures are
 * reported with the SAME error type (`ApiQueryError`), so no component ever
 * knows the transport (`contract/next-app-architecture-contract.md` §5).
 */

/** The public message of a drifted contract. */
export const MENSAJE_CONTRATO_PASES =
  "La respuesta del servidor no coincide con el contrato de los pases de fiesta.";

/**
 * Send ONE request and validate its answer.
 *
 * A drifted contract and a failed request are reported with the SAME error
 * type, so the view never has to know the transport.
 */
export async function pedir<T>(
  peticion: () => Promise<{ data: unknown }>,
  parsear: (datos: unknown) => T,
): Promise<T> {
  try {
    const respuesta = await peticion();
    return parsear(respuesta.data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ApiQueryError(MENSAJE_CONTRATO_PASES, undefined);
    }
    const { message, status } = handleApiError(error);
    throw new ApiQueryError(message, status);
  }
}
