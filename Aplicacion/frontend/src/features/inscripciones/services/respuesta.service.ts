import { z } from "zod";

import { apiResponseSchema } from "@/types/api.types";

/**
 * The reading of the envelope of the target backend.
 *
 * The envelope is the ONE shape of `FREEZE-ENV-1.0.0`:
 *
 *     success -> { success: true,  data: T | null, error: null, message: str | null }
 *     error   -> { success: false, data: null, error: { code, message, details, field_errors } }
 *
 * The shape itself lives in ONE house (`src/types/api.types.ts`); this module
 * only knows how to OPEN it and how to insist that it carries data.
 *
 * The answer that does not match the envelope is a FAILURE: `parse` throws,
 * and the caller never receives a partially trusted value.
 */
export interface Respuesta<T> {
  /** The payload of the answer. */
  data: T;
  /** The public message of the controller, when it declares one. */
  message: string | null;
}

/**
 * Opens the envelope and returns its payload.
 *
 * @param dataSchema the mirror of the wrapper the endpoint publishes.
 * @param body the body of the answer.
 * @param sinContenido the message of a body that carries no data.
 */
export function leerRespuesta<T>(
  dataSchema: z.ZodType<T>,
  body: unknown,
  sinContenido: string,
): Respuesta<T> {
  const envelope = apiResponseSchema(dataSchema).parse(body);

  if (!envelope.success || envelope.data === null) {
    throw new Error(envelope.message ?? sinContenido);
  }

  return { data: envelope.data, message: envelope.message ?? null };
}
