import { z } from "zod";

/**
 * The exact mirror of the POOL of a registration.
 *
 * Backend: `Aplicacion/backend/modules/salesianos_fest/presentation/schemas/pool_schemas.py`
 * (packet DOM-02, freeze `FREEZE-PS-1.0.0`).
 *
 * The arithmetic of the pool is the answer of the SERVER (`RN-I03`): the
 * wrapper carries the THREE numbers (`cupos_pagados`, `cupos_asignados`,
 * `cupos_disponibles`) and the list of impediments. The client NEVER
 * subtracts them.
 */

/** A participation of the pool (mirrors `ParticipacionOut`). */
export const participacionSchema = z.object({
  id: z.string(),
  persona_id: z.string(),
  equipo_id: z.string(),
  equipo_nombre: z.string(),
  disciplina_id: z.string(),
  disciplina_nombre: z.string(),
  /** `JUGADOR`, `CAPITAN` or `DELEGADO`. */
  rol: z.string(),
  /** `ACTIVA` or `RETIRADA`. */
  estado: z.string(),
  /** Whether the participation occupies a cupo of the registration. */
  ocupa_cupo: z.boolean(),
  /** The moment of the removal, `null` when there was none. */
  retirada_en: z.string().nullable(),
});

export type Participacion = z.infer<typeof participacionSchema>;

/**
 * A concrete impediment of the pool (mirrors `ImpedimentoOut`).
 *
 * `mensaje` is the public prose of the backend and the frontend prints it
 * VERBATIM. The frontend never branches on `codigo`: the catalogue of public
 * codes is not closed, so a component that decided what a code means would
 * break with the next code the backend catalogues.
 */
export const impedimentoSchema = z.object({
  codigo: z.string(),
  mensaje: z.string(),
  /** The team involved, `null` when the impediment is not of a team. */
  equipo_id: z.string().nullable(),
});

export type Impedimento = z.infer<typeof impedimentoSchema>;

/** The pool of a registration (mirrors `PoolOut`). */
export const poolSchema = z.object({
  inscripcion_id: z.string(),
  cupos_pagados: z.number().int().nonnegative(),
  cupos_asignados: z.number().int().nonnegative(),
  cupos_disponibles: z.number().int().nonnegative(),
  participaciones: z.array(participacionSchema),
  impedimentos: z.array(impedimentoSchema),
  /** The operational cause of the answer. The domain declares it. */
  causa_operativa: z.string(),
});

export type Pool = z.infer<typeof poolSchema>;

// ── Entradas ─────────────────────────────────────────────────────────────────

/**
 * The payload of adding (or MOVING) a participant to the pool
 * (mirrors `ParticipanteAsignarIn`).
 *
 * The person is identified by `persona_id` **or** by document, never by both
 * and never by none: the server verifies it and answers 422 when the
 * identification is ambiguous.
 *
 * The number of cupos does NOT travel: a cupo is UNITARY and the server
 * assigns it (`RN-I03`).
 *
 * `reemplaza_participacion_id` is the MOVEMENT: the new person takes over the
 * cupo of the withdrawn one, in the SAME transaction (`FL-05` step 4,
 * `RN-I04`).
 */
export const participanteAsignarInSchema = z.object({
  /** The person of the register. */
  persona_id: z.string().nullish(),
  /** The type of the document to resolve the person. */
  tipo_documento: z.string().nullish(),
  /** The number of the document to resolve the person. */
  numero_documento: z.string().nullish(),
  /** The destination team inside the registration. */
  equipo_id: z.string(),
  /** The role of the person in the team. The server defaults it to `JUGADOR`. */
  rol: z.string().nullish(),
  /** The participation that is withdrawn to free its cupo. */
  reemplaza_participacion_id: z.string().nullish(),
});

export type ParticipanteAsignarIn = z.infer<typeof participanteAsignarInSchema>;
