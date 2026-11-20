import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The Zod mirrors of the SHARED operational vocabulary of the administration
 * area.
 *
 * They are the 1:1 mirror of the pieces the frozen envelope publishes
 * (`FREEZE-ENV-1.0.0` §5) and that every administrative presenter reuses:
 *
 * - `EstadoOperativo` — the machine code, the plain label and the explanation.
 * - The action the presenter projects (`acciones_disponibles`).
 * - The three cupos, as three facts.
 * - The cause with its public prose.
 *
 * ## What these mirrors are NOT
 *
 * They are NOT the verdict of the view. The verdict of the view is
 * `{ estado, rol }`: the `estado` is what the backend says and the `rol` is
 * the VISUAL bucket that the adapter decides (`D-UI04-03`). The bucket is
 * presentational and it NEVER travels on the wire: a presenter that published
 * it would publish a decision of the interface.
 *
 * ## The error envelope
 *
 * `adminErrorEnvelopeSchema` is the exact shape of the frozen ERROR answer
 * (`core/responses.py` -> `error_response`): `error.field_errors` is the ONLY
 * channel of field-level errors and `error.details` carries non-field context
 * only. The shared `apiErrorSchema` of `src/types/api.types.ts` does not
 * declare `field_errors` and rejects a `null` `details`, so the administration
 * area declares its OWN mirror of the error (A0-API04-03).
 */

/** The machine code, the plain label and the explanation of a fact. */
export const estadoOperativoSchema = z.object({
  codigo: z.string().min(1),
  etiqueta: z.string(),
  descripcion: z.string(),
});

/**
 * An action the presenter projects.
 *
 * It is a PROJECTION and not an authorisation (`contratos/01` §6): the
 * interface may use it to hide an affordance, but the 403 of the backend
 * remains the control.
 */
export const accionOperativaSchema = z.object({
  codigo: z.string().min(1),
  etiqueta: z.string(),
  href: z.string().optional(),
});

/** The three cupos of a record, as three different facts. */
export const cuposOperativosSchema = z.object({
  adquiridos: z.number().int().nonnegative(),
  asignados: z.number().int().nonnegative(),
  disponibles: z.number().int().nonnegative(),
});

/** A cause with its machine code and its public prose. */
export const causaSchema = z.object({
  codigo: z.string().min(1),
  mensaje: z.string(),
});

/** One field-level error of the frozen envelope. */
export const fieldErrorSchema = z.object({
  field: z.string(),
  code: z.string(),
  message: z.string(),
});

/** The detail of an error of the frozen envelope. */
export const adminErrorDetailSchema = z.object({
  code: z.string(),
  message: z.string(),
  details: z.record(z.string(), z.unknown()).nullable().optional(),
  field_errors: z.array(fieldErrorSchema).nullable().optional(),
});

/**
 * The ERROR envelope of the target (`core/responses.py` -> `error_response`).
 *
 * `success` is `false` and `data` is `null`: an error NEVER carries a payload.
 */
export const adminErrorEnvelopeSchema = z.object({
  success: z.literal(false),
  data: z.null(),
  error: adminErrorDetailSchema,
  message: z.string().nullable().optional(),
});

/**
 * The SUCCESS envelope of a paginated answer.
 *
 * The pagination has the ONE shape of the target and it lives INSIDE `data`:
 * `{ items, total, page, page_size, total_pages }` (`FREEZE-ENV-1.0.0` §4.3).
 */
export function envelopeAdminPaginado<T>(itemSchema: z.ZodType<T>) {
  return apiResponseSchema(
    z.object({
      items: z.array(itemSchema),
      total: z.number().int().nonnegative(),
      page: z.number().int().positive(),
      page_size: z.number().int().positive(),
      total_pages: z.number().int().nonnegative(),
    }),
  );
}

/** The SUCCESS envelope of an answer that is not paginated. */
export function envelopeAdmin<T>(dataSchema: z.ZodType<T>) {
  return apiResponseSchema(dataSchema);
}
