"use client";

import { api } from "@/lib/api";
import type { ApiResponse } from "@/types/api.types";
import type { ParticipanteOut } from "./inscripcion.service";

// ── Phase 3: participant pool API ───────────────────────────────────────────────
//
// The pool endpoint is the ONLY source of eligibility: the backend decides
// whether a pre-registered person may join a team (`tiene_cupo_activo`) and
// exposes a UI-safe reason when it may not (`motivo_bloqueo`).
//
// The frontend NEVER derives eligibility on its own — it renders what the
// backend returned and lets the backend reject any invalid mutation.

/** Persona summary embedded in a pool entry (backend `PersonaSummarySchema`). */
export interface PoolPersonaOut {
  id: string;
  nombre: string;
  nombres: string;
  apellidos: string;
  numero_documento: string;
}

/** One pre-registered participant waiting for a team slot. */
export interface PoolEntryOut {
  /** `InscripcionPersona.id` — the id every pool mutation expects. */
  id: string;
  persona: PoolPersonaOut;
  /** `InscripcionPersona.estado` — "A" (active) | "R" (retired). */
  estado: string;
  created_at: string;
  /** Backend-authoritative eligibility. */
  tiene_cupo_activo: boolean;
  /**
   * Typed eligibility discriminator.
   *
   * `LISTO` | `ESPERANDO_PAGO` | `SIN_CAPACIDAD` | `CUPO_POR_ASIGNAR` — the
   * UI maps it to a visual state and never parses `motivo_bloqueo` to decide
   * what to render.
   */
  estado_pool: string;
  /** UI-safe blocked reason. `null` when the person is eligible. */
  motivo_bloqueo: string | null;
}

/** Response of `GET /inscripciones/{id}/pool`. */
export interface PoolOut {
  inscripcion_id: string;
  pool: PoolEntryOut[];
}

/** Payload of `POST /inscripciones/{id}/pool/asignar`. */
export interface AsignarAEquipoPayload {
  inscripcion_persona_id: string;
  equipo_id: string;
  rol?: string;
  talla_camiseta?: string;
  notas?: string;
}

/** Response of `POST /inscripciones/{id}/pool/asignar`. */
export interface AsignarAEquipoRespuesta {
  /** The `Participacion` created by the atomic mutation. */
  participante: ParticipanteOut;
}

/** Response of `GET /inscripciones/{id}/saldo`. */
export interface SaldoOut {
  inscripcion_id: string;
  /** Purchased capacity (paid + pending purchases, cancelled excluded). */
  contratados: number;
  /** Paid capacity. */
  pagados: number;
  /** Paid capacity already consumed by an `AsignacionCupo`. */
  asignados_pagados: number;
  /** Paid capacity still available — 0 means nobody can join a team yet. */
  disponibles_pagados: number;
}

/**
 * GET /inscripciones/{id}/pool
 *
 * Pre-registered participants without an active `Participacion`, each one with
 * its cup eligibility and a UI-safe blocked reason.
 */
export async function getPool(
  inscripcionId: string,
): Promise<ApiResponse<PoolOut>> {
  const { data } = await api.get<ApiResponse<PoolOut>>(
    `/inscripciones/${inscripcionId}/pool`,
  );
  return data;
}

/**
 * POST /inscripciones/{id}/pool/asignar
 *
 * The sole authority for assigning a pool participant to an equipo: the
 * backend creates the `Participacion` and enforces every gate (cup, R11,
 * roster, deadline) inside one transaction.
 */
export async function asignarPoolAEquipo(
  inscripcionId: string,
  payload: AsignarAEquipoPayload,
): Promise<ApiResponse<AsignarAEquipoRespuesta>> {
  const { data } = await api.post<ApiResponse<AsignarAEquipoRespuesta>>(
    `/inscripciones/${inscripcionId}/pool/asignar`,
    {
      inscripcion_persona_id: payload.inscripcion_persona_id,
      equipo_id: payload.equipo_id,
      rol: payload.rol ?? "J",
      talla_camiseta: payload.talla_camiseta ?? "",
      notas: payload.notas ?? "",
    },
  );
  return data;
}

/**
 * GET /inscripciones/{id}/saldo
 *
 * Cupo balance of the inscription — the source of truth for "is there still
 * paid capacity available to assign a team slot?".
 */
export async function getSaldoInscripcion(
  inscripcionId: string,
): Promise<ApiResponse<SaldoOut>> {
  const { data } = await api.get<ApiResponse<SaldoOut>>(
    `/inscripciones/${inscripcionId}/saldo`,
  );
  return data;
}

// ── Phase 5: pool preregistration ──────────────────────────────────────────────

/**
 * Payload of the pool preregistration.
 *
 * Mirrors the backend `AgregarPersonaIn` WITHOUT `equipo_id`: the backend
 * creates only the `InscripcionPersona` (pre-registration) and applies its own
 * contracted-capacity gate. Exactly one of `persona_id` / `persona_data` must
 * be provided — the backend resolves the XOR and rejects 422 otherwise.
 */
export interface PreregistrarEnPoolPayload {
  /** Existing persona to link (lookup path). */
  persona_id?: string;
  /** Inline persona data — the server upserts by `(tipo_documento, numero_documento)`. */
  persona_data?: {
    tipo_documento: "DNI" | "CE" | "PAS";
    numero_documento: string;
    nombres: string;
    apellidos: string;
    genero: "M" | "F";
    telefono?: string | null;
    whatsapp?: string | null;
  };
  /** Consent records created atomically with the preregistration. */
  aceptaciones?: Array<"BASES" | "APTITUD_FISICA" | "IMAGEN">;
}

/** The `InscripcionPersona` created by a preregistration. */
export interface PoolParticipanteInscripcionOut {
  /** `InscripcionPersona.id`. */
  id: string;
  inscripcion_id: string;
  persona: PoolPersonaOut;
  /** "A" (active) | "R" (retired). */
  estado: string;
  created_at: string;
}

/** Response of the pool preregistration. */
export interface PreregistrarEnPoolRespuesta {
  participante: PoolParticipanteInscripcionOut;
}

/**
 * POST /inscripciones/{id}/personas — preregistration (no `equipo_id`)
 *
 * Creates only the `InscripcionPersona`: the person waits in the pool without
 * a team and without any paid right. The backend owns the capacity gate
 * (`CUPO_CONTRATADO_EXCEDIDO`) and the deadline — the frontend never
 * re-implements them, it only surfaces the backend error.
 */
export async function preregistrarEnPool(
  inscripcionId: string,
  payload: PreregistrarEnPoolPayload,
): Promise<ApiResponse<PreregistrarEnPoolRespuesta>> {
  // NOTE: no `equipo_id` — that is what turns this call into a preregistration.
  const { data } = await api.post<ApiResponse<PreregistrarEnPoolRespuesta>>(
    `/inscripciones/${inscripcionId}/personas`,
    payload,
  );
  return data;
}
