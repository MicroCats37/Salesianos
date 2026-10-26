"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type {
  AdminAccesoListadoEnvelope,
  AdminAcreditacionDetalleEnvelope,
  AdminAcreditacionListadoEnvelope,
} from "../schemas";
import {
  getAdminAccesos,
  getAdminAcreditacionDetalle,
  getAdminAcreditaciones,
} from "../services/admin.operacion.service";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";

/** Page of the accreditations (A10). */
export const adminAcreditacionesQueryOptions = (estado: AdminEstadoLista) =>
  queryOptions<
    AdminAcreditacionListadoEnvelope,
    ApiQueryError,
    AdminAcreditacionListadoEnvelope,
    readonly ["admin", "acreditaciones", Record<string, string | number>]
  >({
    queryKey: ["admin", "acreditaciones", adminParametrosConsulta(estado)],
    queryFn: () => getAdminAcreditaciones(estado),
    staleTime: 30 * 1000,
  });

/** Drilldown of one accreditation (A11). */
export const adminAcreditacionDetalleQueryOptions = (acreditacionId: string) =>
  queryOptions<
    AdminAcreditacionDetalleEnvelope,
    ApiQueryError,
    AdminAcreditacionDetalleEnvelope,
    readonly ["admin", "acreditacion", string]
  >({
    queryKey: ["admin", "acreditacion", acreditacionId],
    queryFn: () => getAdminAcreditacionDetalle(acreditacionId),
    enabled: Boolean(acreditacionId),
    staleTime: 30 * 1000,
  });

/** Page of the access log (A12). */
export const adminAccesosQueryOptions = (estado: AdminEstadoLista) =>
  queryOptions<
    AdminAccesoListadoEnvelope,
    ApiQueryError,
    AdminAccesoListadoEnvelope,
    readonly ["admin", "accesos", Record<string, string | number>]
  >({
    queryKey: ["admin", "accesos", adminParametrosConsulta(estado)],
    queryFn: () => getAdminAccesos(estado),
    staleTime: 30 * 1000,
  });

export function useAdminAcreditaciones(estado: AdminEstadoLista) {
  return useQuery(adminAcreditacionesQueryOptions(estado));
}

export function useAdminAcreditacionDetalle(acreditacionId: string) {
  return useQuery(adminAcreditacionDetalleQueryOptions(acreditacionId));
}

export function useAdminAccesos(estado: AdminEstadoLista) {
  return useQuery(adminAccesosQueryOptions(estado));
}
