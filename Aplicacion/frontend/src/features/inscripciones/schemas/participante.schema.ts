import { z } from "zod";

/**
 * The client-side validation of the assignment of a participant.
 *
 * It is NOT a wire mirror: the wire mirror is `participanteAsignarInSchema`
 * (`schemas/pool.schema.ts`). This schema only validates what the operator
 * typed before the request leaves the browser.
 *
 * The vocabularies are the CLOSED ones of the backend:
 *
 * - `TipoDocumentoChoices` (`modules/usuarios`): `DNI`, `CE`, `PAS`;
 * - `RolParticipante` (`modules/salesianos_fest/domain/constants.py`):
 *   `JUGADOR`, `CAPITAN`, `DELEGADO`.
 *
 * The eligibility of the person, the capacity of the team and the number of
 * cupos belong to the server (`RN-I03`, `RN-I04`): the browser never derives
 * them and the 422 of the server reaches the control that owns the field.
 */

/** The types of document that the backend recognizes. */
export const TIPOS_DOCUMENTO = ["DNI", "CE", "PAS"] as const;

/** The roles that a participant can have in a team. */
export const ROLES_PARTICIPANTE = ["JUGADOR", "CAPITAN", "DELEGADO"] as const;

/**
 * The form of the assignment.
 *
 * The person travels by DOCUMENT: the server resolves her from the register
 * (`RT-IN-05`), so the browser never resolves a person and never invents an
 * identifier.
 */
export const FormularioParticipanteSchema = z.object({
  tipo_documento: z.string().min(1, "Elige el tipo de documento"),
  numero_documento: z
    .string()
    .trim()
    .min(1, "Escribe el número del documento")
    .max(20, "El número del documento es demasiado largo"),
  equipo_id: z.string().min(1, "Elige el equipo"),
  rol: z.string().min(1, "Elige el rol"),
});

export type FormularioParticipanteFormData = z.infer<
  typeof FormularioParticipanteSchema
>;
