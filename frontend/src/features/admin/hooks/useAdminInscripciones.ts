"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type {
  AdminInscripcionDetalleEnvelope,
  AdminInscripcionListadoEnvelope,
} from "../schemas";
import {
  getAdminInscripcionDetalle,
  getAdminInscripciones,
} from "../services/admin.inscripcion.service";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";

/**
 * TanStack Query v5 object syntax (REQUIRED by
 * `contract/next-app-architecture-contract.md` §4).
 *
 * The list key carries the whole state — page, page size, term, ordering and
 * filters — so two different filter combinations never share a cache entry.
 */
export const adminInscripcionesQueryOptions = (estado: AdminEstadoLista) =>
  queryOptions<
    AdminInscripcionListadoEnvelope,
    ApiQueryError,
    AdminInscripcionListadoEnvelope,
    readonly ["admin", "inscripciones", Record<string, string | number>]
  >({
    queryKey: ["admin", "inscripciones", adminParametrosConsulta(estado)],
    queryFn: () => getAdminInscripciones(estado),
    staleTime: 30 * 1000,
  });

export const adminInscripcionDetalleQueryOptions = (inscripcionId: string) =>
  queryOptions<
    AdminInscripcionDetalleEnvelope,
    ApiQueryError,
    AdminInscripcionDetalleEnvelope,
    readonly ["admin", "inscripcion", string]
  >({
    queryKey: ["admin", "inscripcion", inscripcionId],
    queryFn: () => getAdminInscripcionDetalle(inscripcionId),
    enabled: Boolean(inscripcionId),
    staleTime: 30 * 1000,
  });

/** Page of the registrations table (A3). */
export function useAdminInscripciones(estado: AdminEstadoLista) {
  return useQuery(adminInscripcionesQueryOptions(estado));
}

/** Drilldown of one registration (A4). */
export function useAdminInscripcionDetalle(inscripcionId: string) {
  return useQuery(adminInscripcionDetalleQueryOptions(inscripcionId));
}
