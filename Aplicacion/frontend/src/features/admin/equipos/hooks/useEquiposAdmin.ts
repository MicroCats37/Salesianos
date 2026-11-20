"use client";

import { useAdminQuery } from "@/features/admin/operaciones/hooks/useAdminQuery";
import { RUTAS_ADMIN } from "@/features/admin/operaciones/services/admin.service";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { parametrosListaAdminDesdeUrl } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import {
  equipoAdminDetalleDesdeWire,
  equipoAdminDetalleEnvelope,
  equipoAdminListaDesdeWire,
  listaEquiposAdminEnvelope,
} from "../schemas/equipo-admin.schema";
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
  const consulta = useAdminQuery({
    queryKey: adminClaves.equipos.list,
    ruta: RUTAS_ADMIN.equiposLista,
    envelope: listaEquiposAdminEnvelope,
    filtros: parametrosListaAdminDesdeUrl(parametros),
    select: (pagina) => pagina.items.map(equipoAdminListaDesdeWire),
  });

  return estadoDesdeConsulta(consulta, RUTAS_ADMIN.equiposLista.registrado);
}

/** The administrative detail of a team (`ADM-08`). */
export function useDetalleEquipoAdmin(
  equipoId: string | undefined,
): EstadoDetalleEquipoAdmin {
  const consulta = useAdminQuery({
    queryKey: adminClaves.equipos.detail(equipoId ?? ""),
    ruta: RUTAS_ADMIN.equipoDetalle,
    envelope: equipoAdminDetalleEnvelope,
    parametros: equipoId ? { equipo_id: equipoId } : undefined,
    enabled: Boolean(equipoId),
    select: (detalle) => equipoAdminDetalleDesdeWire(detalle),
  });

  return estadoDesdeConsulta(consulta, RUTAS_ADMIN.equipoDetalle.registrado);
}
