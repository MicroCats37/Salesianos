"use client";

import { api } from "@/lib/api";
import type { ApiResponse } from "@/types/api.types";

// ── Team-scoped participant selector API ───────────────────────────────────────
//
// The backend is the ONLY authority on eligibility: it reports the paid-cup
// eligibility, the disciplines where the person already plays and the verdict
// for the target team (`asignable`). The frontend NEVER re-derives it — it
// renders exactly what it receives.
//
// The `/pool` contract is untouched: the pool still means "waiting in the
// pool" (no active participation). This endpoint is the team-scoped read that
// makes multi-discipline possible: one paid cup authorises the person in
// EVERY contracted discipline, but never twice in the SAME one (R11).

/** Persona summary embedded in a candidate (backend `PersonaSummarySchema`). */
export interface ElegiblePersonaOut {
  id: string;
  nombre: string;
  nombres: string | null;
  apellidos: string | null;
  numero_documento: string;
}

/** Disciplina summary (backend `DisciplinaSummarySchema`). */
export interface ElegibleDisciplinaOut {
  id: string;
  nombre: string;
  sigla: string;
}

/** A discipline where the person already holds an active participation. */
export interface DisciplinaAsignadaOut {
  disciplina: ElegibleDisciplinaOut;
  equipo_id: string;
  equipo_nombre: string;
}

/** One candidate of the team-scoped participant selector. */
export interface ElegibleOut {
  /** `InscripcionPersona.id` — the id the assignment endpoint expects. */
  id: string;
  persona: ElegiblePersonaOut;
  /** `InscripcionPersona.estado` — "A" (active) | "R" (retired). */
  estado: string;
  created_at: string;
  /** Backend-authoritative paid-cup eligibility. */
  tiene_cupo_activo: boolean;
  /**
   * Typed commercial discriminator (same contract as the pool):
   * LISTO | ESPERANDO_PAGO | SIN_CAPACIDAD | CUPO_POR_ASIGNAR.
   */
  estado_pool: string;
  /** UI-safe reason why there is no paid cup. `null` when the cup is active. */
  motivo_bloqueo: string | null;
  /** Disciplines where the person already plays (one cup, several teams). */
  disciplinas_asignadas: DisciplinaAsignadaOut[];
  /** Typed R11 flag: the person already plays in the TARGET discipline. */
  ya_en_disciplina: boolean;
  /** Backend verdict for the target team: the person may be added right now. */
  asignable: boolean;
  /** UI-safe reason when `asignable` is false. `null` when it is true. */
  motivo_no_asignable: string | null;
}

/** Response of `GET /inscripciones/{id}/equipos/{equipo_id}/elegibles`. */
export interface ElegiblesEquipoOut {
  inscripcion_id: string;
  equipo_id: string;
  equipo_nombre: string;
  disciplina: ElegibleDisciplinaOut;
  elegibles: ElegibleOut[];
}

/**
 * GET /inscripciones/{id}/equipos/{equipo_id}/elegibles
 *
 * The candidate list of ONE team. Each candidate carries its own verdict, so
 * the selector modal never has to compute eligibility.
 */
export async function getElegiblesEquipo(
  inscripcionId: string,
  equipoId: string,
): Promise<ApiResponse<ElegiblesEquipoOut>> {
  const { data } = await api.get<ApiResponse<ElegiblesEquipoOut>>(
    `/inscripciones/${inscripcionId}/equipos/${equipoId}/elegibles`,
  );
  return data;
}
