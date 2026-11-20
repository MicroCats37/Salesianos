import {
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import type { ParamsListaAdmin } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { parametrosConsultaAdmin } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import type { PaginatedResult } from "@/shared/schemas/pagination.schema";
import {
  equipoAdminDetalleDesdeWire,
  equipoAdminDetalleEnvelope,
  equipoAdminListaDesdeWire,
  listaEquiposAdminEnvelope,
} from "../schemas/equipo-admin.schema";
import type {
  AdminEquipoDetalleOut,
  AdminEquipoListItemOut,
} from "../types/equipos-admin.types";

/**
 * The client of the ADMINISTRATION OF THE TEAMS.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `RT-IN-09` | GET | `/administracion/equipos` | `PaginatedData[AdminEquipoListItemOut]` |
 * | `RT-IN-10` | GET | `/administracion/equipos/{equipo_id}` | `AdminEquipoDetalleOut` |
 *
 * ## The registration truth
 *
 * `AdminEquipoController` is NOT registered in
 * `Aplicacion/backend/config/api.py`: both routes DO NOT EXIST. The guard of
 * `pedirAdmin` REJECTS them before the transport (`A0-API04-05`).
 *
 * ## What the browser NEVER does
 *
 * It never compares the roster with the minimum of the discipline and it
 * never derives the readiness of a team: the `estado_operativo` of the
 * presenter is the only source of that verdict (`contratos/01` §7).
 */

/** The administrative list of the teams (`RT-IN-09`). */
export async function listarEquiposAdmin(
  parametros: ParamsListaAdmin,
): Promise<PaginatedResult<AdminEquipoListItemOut>> {
  const pagina = await pedirAdmin(
    RUTAS_ADMIN.equiposLista,
    listaEquiposAdminEnvelope,
    { params: parametrosConsultaAdmin(parametros) },
  );

  return {
    ...pagina,
    items: pagina.items.map(equipoAdminListaDesdeWire),
  };
}

/** The administrative detail of a team (`RT-IN-10`). */
export async function obtenerEquipoAdmin(
  equipoId: string,
): Promise<AdminEquipoDetalleOut> {
  const detalle = await pedirAdmin(
    RUTAS_ADMIN.equipoDetalle,
    equipoAdminDetalleEnvelope,
    { pathParams: { equipo_id: equipoId } },
  );

  return equipoAdminDetalleDesdeWire(detalle);
}
