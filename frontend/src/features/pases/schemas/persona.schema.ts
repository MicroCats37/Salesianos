/**
 * TypeScript mirror of the backend exact identity lookup.
 *
 * Source of truth (backend):
 *   - `modules/usuarios/presentation/schemas/persona_resolucion_schemas.py`
 *   - `modules/usuarios/presentation/controllers/persona_resolucion_controller.py`
 *
 * The mirror is EXACT: the wrapper carries ONLY the fields needed to confirm
 * the identity and to assign an existing right. The account state, the
 * contacts and the QR credential NEVER travel
 * (`contract/api-wrapper-presenter-contract.md` §6).
 */

import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The person that matches the consulted civil identity EXACTLY.
 *
 * `numero_documento` is the document the caller already supplied: it comes
 * back unaltered so the client can confirm the match.
 */
export const personaResueltaSchema = z.object({
  /** `Persona.id` — the id the assignment endpoint expects. */
  persona_id: z.string(),
  /** Display name of the person. */
  nombre_completo: z.string(),
  /** Document type (DNI, CE, PAS). */
  tipo_documento: z.string(),
  /** Document number the caller supplied. */
  numero_documento: z.string(),
});

export type PersonaResuelta = z.infer<typeof personaResueltaSchema>;

/** Envelope of the exact lookup — backend `ApiResponse[PersonaResueltaOut]`. */
export const personaResueltaEnvelopeSchema = apiResponseSchema(
  personaResueltaSchema,
);

export type PersonaResueltaEnvelope = z.infer<
  typeof personaResueltaEnvelopeSchema
>;
