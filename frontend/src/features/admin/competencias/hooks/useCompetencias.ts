"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type {
  AgendaEnvelope,
  CompetenciaDetalleEnvelope,
  CompetenciasListaEnvelope,
  CuadroEnvelope,
} from "../schemas";
import {
  getAgendaCompetencias,
  getCompetenciaCuadro,
  getCompetenciaDetalle,
  getCompetencias,
} from "../services";
import {
  claveAgendaCompetencias,
  claveCompetenciaCuadro,
  claveCompetenciaDetalle,
  claveCompetenciasLista,
} from "../utils/competencias.claves.utils";

/**
 * The hooks of the module — TanStack Query owns EVERY piece of server state.
 *
 * There is no Zustand store for the competitions: the data lives in the query
 * cache, the filters live in the URL, and the components only render
 * (`contract/next-app-architecture-contract.md` §4).
 */

/** The competitions of the administrative scope. */
export const competenciasListaQueryOptions = (
  filtros: Record<string, string>,
) =>
  queryOptions<
    CompetenciasListaEnvelope,
    ApiQueryError,
    CompetenciasListaEnvelope,
    readonly ["admin", "competencias", "lista", Record<string, string>]
  >({
    queryKey: claveCompetenciasLista(filtros),
    queryFn: () => getCompetencias(filtros),
    staleTime: 30 * 1000,
  });

/** The detail of ONE competition. */
export const competenciaDetalleQueryOptions = (competenciaId: string) =>
  queryOptions<
    CompetenciaDetalleEnvelope,
    ApiQueryError,
    CompetenciaDetalleEnvelope,
    readonly ["admin", "competencias", "detalle", string]
  >({
    queryKey: claveCompetenciaDetalle(competenciaId),
    queryFn: () => getCompetenciaDetalle(competenciaId),
    enabled: competenciaId.length > 0,
    staleTime: 30 * 1000,
  });

/** The bracket of ONE competition. */
export const competenciaCuadroQueryOptions = (competenciaId: string) =>
  queryOptions<
    CuadroEnvelope,
    ApiQueryError,
    CuadroEnvelope,
    readonly ["admin", "competencias", "cuadro", string]
  >({
    queryKey: claveCompetenciaCuadro(competenciaId),
    queryFn: () => getCompetenciaCuadro(competenciaId),
    enabled: competenciaId.length > 0,
    staleTime: 30 * 1000,
  });

/** The agenda of ONE day. */
export const agendaCompetenciasQueryOptions = (
  filtros: Record<string, string>,
) =>
  queryOptions<
    AgendaEnvelope,
    ApiQueryError,
    AgendaEnvelope,
    readonly ["admin", "competencias", "agenda", Record<string, string>]
  >({
    queryKey: claveAgendaCompetencias(filtros),
    queryFn: () => getAgendaCompetencias(filtros),
    staleTime: 30 * 1000,
  });

export function useCompetenciasLista(filtros: Record<string, string>) {
  return useQuery(competenciasListaQueryOptions(filtros));
}

export function useCompetenciaDetalle(competenciaId: string) {
  return useQuery(competenciaDetalleQueryOptions(competenciaId));
}

export function useCompetenciaCuadro(competenciaId: string) {
  return useQuery(competenciaCuadroQueryOptions(competenciaId));
}

export function useAgendaCompetencias(filtros: Record<string, string>) {
  return useQuery(agendaCompetenciasQueryOptions(filtros));
}
