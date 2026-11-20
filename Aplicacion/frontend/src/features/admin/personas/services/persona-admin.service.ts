import {
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import type { ParamsListaAdmin } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { parametrosConsultaAdmin } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import type { PaginatedResult } from "@/shared/schemas/pagination.schema";
import {
  adminPersonaDetalleEnvelope,
  listaPersonasAdminEnvelope,
} from "../schemas/persona-admin.schema";
import type {
  AdminPersonaDetalleOut,
  AdminPersonaListItemOut,
} from "../types/personas-admin.types";

/**
 * The client of the administrative search of PEOPLE (`RT-ID-07` · `RT-ID-08`).
 *
 * It goes through the ONE client of the area (`pedirAdmin`), so the ledger
 * decides whether the route exists and the guard rejects the call BEFORE the
 * transport when it does not.
 *
 * ## The registration truth
 *
 * `AdminPersonaController` is NOT registered in
 * `Aplicacion/backend/config/api.py`: both routes do NOT exist. This file is
 * the SEAM: the day A0 registers the controller, the binding is THIS file
 * and nothing else.
 *
 * ## What the browser does NOT do
 *
 * It does not decide that a person may or may not take part: the conflict
 * and the verdict are the ones the backend published.
 */

/** The administrative search of people (`RT-ID-07`). */
export async function listarPersonasAdmin(
  parametros: ParamsListaAdmin,
): Promise<PaginatedResult<AdminPersonaListItemOut>> {
  const pagina = await pedirAdmin(
    RUTAS_ADMIN.personasLista,
    listaPersonasAdminEnvelope,
    { params: parametrosConsultaAdmin(parametros) },
  );

  return pagina as PaginatedResult<AdminPersonaListItemOut>;
}

/** The detail of a person (`RT-ID-08`). */
export async function obtenerPersonaAdmin(
  personaId: string,
  edicionId?: string,
): Promise<AdminPersonaDetalleOut> {
  return pedirAdmin(RUTAS_ADMIN.personaDetalle, adminPersonaDetalleEnvelope, {
    pathParams: { persona_id: personaId },
    params: edicionId ? { edicion_id: edicionId } : undefined,
  });
}
