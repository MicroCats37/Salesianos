import {
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import type { ParamsListaAdmin } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { parametrosConsultaAdmin } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import type { PaginatedResult } from "@/shared/schemas/pagination.schema";
import { auditoriaListadoEnvelope } from "../schemas/auditoria-admin.schema";
import type {
  AuditoriaItemOut,
  AuditoriaListadoOut,
} from "../types/auditoria-admin.types";

/**
 * The client of the ACTA of the sensitive actions (`RT-ADM-02`).
 *
 * It goes through the ONE client of the area (`pedirAdmin`), so the ledger
 * decides whether the route exists and the guard rejects the call BEFORE the
 * transport when it does not.
 *
 * ## The registration truth
 *
 * `AdminController` is NOT registered in `Aplicacion/backend/config/api.py`:
 * the route does NOT exist and the guard rejects the call before any
 * request leaves the browser. This function is the SEAM: the day A0
 * registers the controller, the binding is THIS file and nothing else.
 *
 * ## What the browser does NOT do
 *
 * It does not filter, it does not reformat and it does not decide which
 * action is suspicious: the acta is the list the server published.
 */
export async function listarAuditoriaAdmin(
  parametros: ParamsListaAdmin,
): Promise<PaginatedResult<AuditoriaItemOut>> {
  const pagina = await pedirAdmin(
    RUTAS_ADMIN.auditoria,
    auditoriaListadoEnvelope,
    { params: parametrosConsultaAdmin(parametros) },
  );

  return pagina as PaginatedResult<AuditoriaItemOut>;
}

/** The whole read of the acta, with the pagination the server published. */
export async function obtenerAuditoriaAdmin(
  parametros: ParamsListaAdmin,
): Promise<AuditoriaListadoOut> {
  return listarAuditoriaAdmin(parametros);
}
