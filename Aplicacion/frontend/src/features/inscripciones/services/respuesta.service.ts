import type { z } from "zod";

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
 * The Zod mirror of the envelope, as a schema that OPENS it.
 *
 * It is the SAME rule that `leerRespuesta` applies, expressed as a schema:
 * a hook that calls the endpoint through the generic family declares the
 * mirror as its `schema` and the envelope is opened HERE, in the only house
 * that owns it.
 *
 * The answer that does not match the contract is a FAILURE: `parse` throws
 * (a `ZodError`), and a body that opens but carries no data throws the
 * message of the server when it declares one.
 *
 * @param dataSchema the mirror of the wrapper the endpoint publishes.
 * @param sinContenido the message of a body that carries no data.
 */
export function respuestaSchema<T>(
  dataSchema: z.ZodType<T>,
  sinContenido: string,
): z.ZodType<Respuesta<T>, unknown> {
  return apiResponseSchema(dataSchema).transform((envelope) => {
    if (!envelope.success || envelope.data === null) {
      throw new Error(envelope.message ?? sinContenido);
    }

    return { data: envelope.data, message: envelope.message ?? null };
  });
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
  return respuestaSchema(dataSchema, sinContenido).parse(body);
}
