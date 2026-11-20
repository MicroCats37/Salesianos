import type { z } from "zod";

/**
 * The envelope of the API, unwrapped.
 *
 * The generic hooks parse the WHOLE body: the schema they receive decides
 * what the hook returns. A feature wants the DATA of the envelope, and an
 * answer that arrives without data is a loud failure, never a silent empty
 * value.
 */
export function datosDelEnvelope<T>(
  envelope: z.ZodType<{ success: boolean; data: T | null }>,
): z.ZodType<T> {
  return envelope.transform((valor) => {
    if (!valor.success || valor.data === null) {
      throw new Error("El servidor respondió sin datos.");
    }
    return valor.data;
  }) as unknown as z.ZodType<T>;
}
