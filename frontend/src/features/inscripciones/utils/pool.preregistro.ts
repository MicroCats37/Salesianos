/**
 * Pool preregistration payload — pure builder, no runtime dependencies.
 *
 * The preregistration is the SAME endpoint as the team-scoped add
 * (`POST /inscripciones/{id}/personas`) but WITHOUT `equipo_id`: that absence
 * is what makes the backend create only the `InscripcionPersona` and park the
 * person in the pool until a paid cup is assigned to them.
 *
 * Keeping the builder pure (and free of the axios-backed service module at
 * runtime) lets the "no team id is submitted" rule be verified deterministically.
 */

import type { PreregistrarEnPoolPayload } from "../services/pool.service";

/** Identity fields collected by the participant form. */
export interface PreregistroPersonaInput {
  tipoDocumento: "DNI" | "CE" | "PAS";
  numeroDocumento: string;
  nombres: string;
  apellidos: string;
  genero: "M" | "F";
  telefono?: string | null;
  whatsapp?: string | null;
}

/**
 * Build the preregistration payload.
 *
 * The backend resolves the persona by `(tipo_documento, numero_documento)`
 * (upsert), so an already-known document reuses its `Persona` record instead
 * of creating a duplicate.
 *
 * NOTE: `equipo_id` is intentionally absent — do not add it here. With it, the
 * backend would create a `Participacion` instead of a preregistration, and the
 * backend guard would reject a brand-new person with
 * `PARTICIPANTE_DEBE_PREREGISTRARSE` (422).
 */
export function buildPreregistroPayload(
  input: PreregistroPersonaInput,
): PreregistrarEnPoolPayload {
  return {
    persona_data: {
      tipo_documento: input.tipoDocumento,
      numero_documento: input.numeroDocumento,
      nombres: input.nombres,
      apellidos: input.apellidos,
      genero: input.genero,
      telefono: input.telefono ?? null,
      whatsapp: input.whatsapp ?? null,
    },
  };
}

/**
 * Build the preregistration payload of an ALREADY registered person.
 *
 * This is the pool-first version of the old "Agregarme" shortcut: the
 * responsible preregisters THEMSELVES in the pool (no team, no `equipo_id`)
 * and is afterwards placed in a team through the selector. Nothing is ever
 * placed directly into a team.
 *
 * NOTE: `equipo_id` is intentionally absent — the person waits in the pool
 * until the responsable assigns them to a team.
 */
export function buildPreregistroSelfPayload(
  personaId: string,
): PreregistrarEnPoolPayload {
  return { persona_id: personaId };
}
