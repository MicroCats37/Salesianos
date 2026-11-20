"use client";

import { useQuery } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import { RUTAS_ADMIN } from "@/features/admin/operaciones/services/admin.service";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { parametrosListaAdminDesdeUrl } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import {
  listarEquiposAdmin,
  obtenerEquipoAdmin,
} from "../services/equipo-admin.service";
import type {
  EstadoDetalleEquipoAdmin,
  EstadoListaEquiposAdmin,
} from "../types/equipos-admin.types";

/**
 * The reads of the ADMINISTRATION OF THE TEAMS.
 *
 * | Read | Route | Wrapper |
 * |---|---|---|
 * | the list (`ADM-07`) | `GET /administracion/equipos` (`RT-IN-09`) | `PaginatedData[AdminEquipoListItemOut]` |
 * | the detail (`ADM-08`) | `GET /administracion/equipos/{id}` (`RT-IN-10`) | `AdminEquipoDetalleOut` |
 *
 * ## The registration truth
 *
 * `AdminEquipoController` is NOT registered: both routes DO NOT EXIST. The
 * reads are DISABLED and the surfaces show the honest state (`sin-datos`).
 *
 * ## What the browser NEVER does
 *
 * It never compares the roster with the minimum of the discipline: the
 * readiness of a team is the `estado_operativo` of the presenter
 * (`contratos/01` §7).
 */

/** The administrative list of the teams (`ADM-07`). */
export function useListaEquiposAdmin(
  parametros: Record<string, string> | undefined,
): EstadoListaEquiposAdmin {
  const consulta = useQuery({
    ...datasetQueryOptions({
      queryKey: adminClaves.equipos.listPage(
        parametrosListaAdminDesdeUrl(parametros),
      ),
      queryFn: () =>
        listarEquiposAdmin(parametrosListaAdminDesdeUrl(parametros)),
      kind: "listadoAdministrativo",
    }),
    enabled: RUTAS_ADMIN.equiposLista.registrado,
  });

  return estadoDesdeConsulta(
    consulta,
    RUTAS_ADMIN.equiposLista.registrado,
    (pagina) => pagina.items,
  );
}

/** The administrative detail of a team (`ADM-08`). */
export function useDetalleEquipoAdmin(
  equipoId: string | undefined,
): EstadoDetalleEquipoAdmin {
  const consulta = useQuery({
    ...datasetQueryOptions({
      queryKey: adminClaves.equipos.detail(equipoId ?? ""),
      queryFn: () => obtenerEquipoAdmin(equipoId ?? ""),
      kind: "listadoAdministrativo",
    }),
    enabled: Boolean(equipoId) && RUTAS_ADMIN.equipoDetalle.registrado,
  });

  return estadoDesdeConsulta(consulta, RUTAS_ADMIN.equipoDetalle.registrado);
}
