/**
 * The client-side validation of the alta.
 *
 * It is NOT a wire mirror and it declares NO wire shape: it only validates
 * what the visitor typed before the request leaves the browser. The exact Zod
 * mirror of the wire lives in `inscripcion.schema.ts` (`inscripcionInicialInSchema`)
 * and the payload that travels is built from it in
 * `utils/inscripcion.payloads.utils.ts`.
 *
 * The rules below are FORM rules, not business rules:
 *
 * - a team needs a discipline and a name, because a team without them is not
 *   a team;
 * - the name is at most 160 characters, which is the limit that the server
 *   declares on the name of a team (a declared limit, mirrored and never
 *   widened).
 *
 * The number of teams a registration may declare, the price, the eligibility,
 * the cupos and the payment belong to the server (RN-I02, RN-I03, RN-C02):
 * the browser never derives them. The server answers 422 with its field
 * error when one of them is not respected, and that error reaches the control
 * that owns the field.
 */

import { z } from "zod";

const EquipoAltaShape = {
  disciplina_id: z.string().min(1, "Elige la disciplina del equipo"),
  nombre: z
    .string()
    .trim()
    .min(1, "Ponle un nombre al equipo")
    .max(160, "El nombre del equipo es demasiado largo"),
};

export const EquipoAltaSchema = z.object(EquipoAltaShape);

const AltaInscripcionShape = {
  paquete_id: z.string().min(1, "Elige el paquete que se contrata"),
  equipos: z.array(EquipoAltaSchema).min(1, "Declara al menos un equipo"),
};

export const AltaInscripcionSchema = z.object(AltaInscripcionShape);

export type AltaInscripcionFormData = z.infer<typeof AltaInscripcionSchema>;
export type EquipoAltaFormData = z.infer<typeof EquipoAltaSchema>;
