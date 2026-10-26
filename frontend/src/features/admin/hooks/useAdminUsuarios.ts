"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type {
  AdminUsuarioDetalleEnvelope,
  AdminUsuarioListadoEnvelope,
} from "../schemas";
import {
  getAdminUsuarioDetalle,
  getAdminUsuarios,
} from "../services/admin.usuario.service";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";

/** Page of the accounts table (A13). */
export const adminUsuariosQueryOptions = (estado: AdminEstadoLista) =>
  queryOptions<
    AdminUsuarioListadoEnvelope,
    ApiQueryError,
    AdminUsuarioListadoEnvelope,
    readonly ["admin", "usuarios", Record<string, string | number>]
  >({
    queryKey: ["admin", "usuarios", adminParametrosConsulta(estado)],
    queryFn: () => getAdminUsuarios(estado),
    staleTime: 30 * 1000,
  });

/** Drilldown of one account (A14). */
export const adminUsuarioDetalleQueryOptions = (usuarioId: string) =>
  queryOptions<
    AdminUsuarioDetalleEnvelope,
    ApiQueryError,
    AdminUsuarioDetalleEnvelope,
    readonly ["admin", "usuario", string]
  >({
    queryKey: ["admin", "usuario", usuarioId],
    queryFn: () => getAdminUsuarioDetalle(usuarioId),
    enabled: Boolean(usuarioId),
    staleTime: 30 * 1000,
  });

export function useAdminUsuarios(estado: AdminEstadoLista) {
  return useQuery(adminUsuariosQueryOptions(estado));
}

export function useAdminUsuarioDetalle(usuarioId: string) {
  return useQuery(adminUsuarioDetalleQueryOptions(usuarioId));
}
