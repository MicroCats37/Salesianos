"use client";

import { queryOptions, useQuery } from "@tanstack/react-query";
import type { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import type { AdminEquipoListadoEnvelope } from "../schemas";
import { getAdminEquipos } from "../services/admin.operacion.service";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";

/** Page of the teams table (A7). */
export const adminEquiposQueryOptions = (estado: AdminEstadoLista) =>
  queryOptions<
    AdminEquipoListadoEnvelope,
    ApiQueryError,
    AdminEquipoListadoEnvelope,
    readonly ["admin", "equipos", Record<string, string | number>]
  >({
    queryKey: ["admin", "equipos", adminParametrosConsulta(estado)],
    queryFn: () => getAdminEquipos(estado),
    staleTime: 30 * 1000,
  });

export function useAdminEquipos(estado: AdminEstadoLista) {
  return useQuery(adminEquiposQueryOptions(estado));
}
