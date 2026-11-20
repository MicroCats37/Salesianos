import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The envelope of the answer of the pass domain, OPENED.
 *
 * The envelope is the ONE shape of `FREEZE-ENV-1.0.0`:
 *
 *     success -> { success: true,  data: T | null, error: null, message: str | null }
 *     error   -> { success: false, data: null, error: { code, message, details } }
 *
 * The shape itself lives in ONE house (`src/types/api.types.ts`); this module
 * only knows how to OPEN it and how to insist that it carries data.
 */
export interface Respuesta<T> {
  /** The payload of the answer. */
  data: T;
  /** The public message of the controller, when it declares one. */
  message: string | null;
}

/**
 * Opens the envelope of an answer.
 *
 * The answer that does not match the contract is a FAILURE: the body is never
 * partially trusted, and the failure is loud.
 *
 * @param dataSchema the mirror of the wrapper the endpoint publishes.
 * @param body the body of the answer.
 * @param sinContrato the message of a body that does not comply.
 */
function abrir<T>(
  dataSchema: z.ZodType<T>,
  body: unknown,
  sinContrato: string,
): Respuesta<T> {
  const envelope = apiResponseSchema(dataSchema).safeParse(body);

  if (!envelope.success) throw new Error(sinContrato);

  if (!envelope.data.success || envelope.data.data === null) {
    throw new Error(
      envelope.data.error?.message ??
        envelope.data.message ??
        "El servidor respondió sin datos.",
    );
  }

  return {
    data: envelope.data.data,
    message: envelope.data.message ?? null,
  };
}

/**
 * The envelope of the answer, as the DATA it carries.
 *
 * It is the `schema` of the generic family: the hook opens the answer with it
 * and receives the payload of the endpoint, never the envelope.
 */
export function respuestaSchema<T>(
  dataSchema: z.ZodType<T>,
  sinContrato: string,
): z.ZodType<T, unknown> {
  return z
    .unknown()
    .transform((body) => abrir(dataSchema, body, sinContrato).data);
}

/**
 * The envelope of the answer, with its DATA and its MESSAGE.
 *
 * The message is the public prose of the controller: it is read, never
 * invented (`contract/api-wrapper-presenter-contract.md` §8).
 */
export function respuestaConMensaje<T>(
  dataSchema: z.ZodType<T>,
  sinContrato: string,
): z.ZodType<Respuesta<T>, unknown> {
  return z.unknown().transform((body) => abrir(dataSchema, body, sinContrato));
}
