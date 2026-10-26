"use client";

import { adminGet } from "@/features/admin/services";
import {
  type AgendaEnvelope,
  AgendaEnvelopeSchema,
  type CompetenciaDetalleEnvelope,
  CompetenciaDetalleEnvelopeSchema,
  type CompetenciasListaEnvelope,
  CompetenciasListaEnvelopeSchema,
  type CuadroEnvelope,
  CuadroEnvelopeSchema,
} from "../schemas";

/**
 * CompetenciasService — the ONLY place where the frontend talks to the API of
 * the module.
 *
 * The components NEVER call `fetch` and never build a URL: they receive the
 * data from the hooks, and the hooks receive it from here
 * (`contract/next-app-architecture-contract.md` §4 and §8).
 *
 * Endpoints (administrative surface, `RequireAdmin`):
 * - GET /api/administracion/competencias
 * - GET /api/administracion/competencias/{id}
 * - GET /api/administracion/competencias/{id}/cuadro
 * - GET /api/administracion/competencias/agenda
 *
 * Every payload is validated against its 1:1 Zod mirror BEFORE it leaves this
 * module: a contract drift fails loudly instead of rendering `undefined` deep
 * inside a table.
 */

/** The competitions of the administrative scope, with their filters. */
export async function getCompetencias(
  filtros: Record<string, string>,
): Promise<CompetenciasListaEnvelope> {
  return adminGet(
    "/administracion/competencias",
    CompetenciasListaEnvelopeSchema,
    filtros,
  );
}

/** The detail of ONE competition (its teams and its rounds). */
export async function getCompetenciaDetalle(
  competenciaId: string,
): Promise<CompetenciaDetalleEnvelope> {
  return adminGet(
    `/administracion/competencias/${competenciaId}`,
    CompetenciaDetalleEnvelopeSchema,
  );
}

/**
 * The bracket of ONE competition.
 *
 * An EMPTY or PARTIAL bracket is a valid answer: the rounds and the
 * encounters that exist are returned as they are and NOTHING is invented.
 */
export async function getCompetenciaCuadro(
  competenciaId: string,
): Promise<CuadroEnvelope> {
  return adminGet(
    `/administracion/competencias/${competenciaId}/cuadro`,
    CuadroEnvelopeSchema,
  );
}

/** The agenda of ONE day. A day without encounters is an empty agenda. */
export async function getAgendaCompetencias(
  filtros: Record<string, string>,
): Promise<AgendaEnvelope> {
  return adminGet(
    "/administracion/competencias/agenda",
    AgendaEnvelopeSchema,
    filtros,
  );
}
