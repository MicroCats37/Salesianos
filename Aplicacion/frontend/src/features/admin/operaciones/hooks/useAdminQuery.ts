"use client";

import type { QueryKey } from "@tanstack/react-query";
import type { ZodType } from "zod";
import { useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import { type RutaAdmin, urlDeRutaAdmin } from "../services/admin.service";
import type { ParamsListaAdmin } from "../utils/admin.claves.utils";
import { parametrosConsultaAdmin } from "../utils/admin.filtros.utils";

export interface UseAdminQueryProps<T, R = T> {
  /** The key of the read: the family of the dataset. */
  queryKey: QueryKey;
  /** The route of the ledger. It is the ONLY source of the URL. */
  ruta: RutaAdmin;
  /** The mirror of the wrapper the route publishes. */
  envelope: ZodType<{ success: boolean; data: T | null }>;
  /** The parameters that fill the path of the route. */
  parametros?: Record<string, string>;
  /** The filters of the URL: they travel to the server as a query. */
  filtros?: ParamsListaAdmin;
  /** Whether the read may run. */
  enabled?: boolean;
  /** The projection of the answer of the server. */
  select?: (datos: T) => R;
}

/**
 * useAdminQuery - the read of the administration area.
 *
 * It is the generic read (`useApiQuery`) with the TWO rules of the area:
 *
 * - the URL comes from the LEDGER (`RUTAS_ADMIN`), never from a component;
 * - a route that is NOT registered is never called: the read is disabled and
 *   the surface shows the honest state (`sin-datos`).
 */
export function useAdminQuery<T, R = T>({
  queryKey,
  ruta,
  envelope,
  parametros,
  filtros,
  enabled = true,
  select,
}: UseAdminQueryProps<T, R>) {
  const activo = enabled && ruta.registrado;
  const url = activo ? urlDeRutaAdmin(ruta, parametros) : null;

  return useApiQuery<T, R>({
    queryKey,
    url,
    schema: datosDelEnvelope(envelope),
    params: filtros ? parametrosConsultaAdmin(filtros) : undefined,
    queryOptions: {
      enabled: activo,
      staleTime: STALE_TIME.listadoAdministrativo,
      gcTime: gcTimeFor(STALE_TIME.listadoAdministrativo),
      select: select as ((datos: T) => R) | undefined,
    },
  });
}
