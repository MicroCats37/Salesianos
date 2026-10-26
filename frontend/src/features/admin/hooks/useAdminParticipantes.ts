"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type {
  AdminParticipacionListadoEnvelope,
  AdminParticipanteListadoEnvelope,
} from "../schemas";
import {
  getAdminParticipaciones,
  getAdminParticipantes,
} from "../services/admin.operacion.service";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";

/**
 * The people (A8) and the roster rows (A9) are TWO different surfaces.
 *
 * One paid cup authorises a person in EVERY contracted discipline, so a
 * person can hold several participations without holding several cupos. The
 * two lists are never mixed and their counters are never reconciled in the
 * browser.
 */

/** Page of the registered people — the POOL surface (A8). */
export const adminParticipantesQueryOptions = (estado: AdminEstadoLista) =>
  queryOptions<
    AdminParticipanteListadoEnvelope,
    ApiQueryError,
    AdminParticipanteListadoEnvelope,
    readonly ["admin", "participantes", Record<string, string | number>]
  >({
    queryKey: ["admin", "participantes", adminParametrosConsulta(estado)],
    queryFn: () => getAdminParticipantes(estado),
    staleTime: 30 * 1000,
  });

/** Page of the roster rows (A9). */
export const adminParticipacionesQueryOptions = (estado: AdminEstadoLista) =>
  queryOptions<
    AdminParticipacionListadoEnvelope,
    ApiQueryError,
    AdminParticipacionListadoEnvelope,
    readonly ["admin", "participaciones", Record<string, string | number>]
  >({
    queryKey: ["admin", "participaciones", adminParametrosConsulta(estado)],
    queryFn: () => getAdminParticipaciones(estado),
    staleTime: 30 * 1000,
  });

export function useAdminParticipantes(estado: AdminEstadoLista) {
  return useQuery(adminParticipantesQueryOptions(estado));
}

export function useAdminParticipaciones(estado: AdminEstadoLista) {
  return useQuery(adminParticipacionesQueryOptions(estado));
}
