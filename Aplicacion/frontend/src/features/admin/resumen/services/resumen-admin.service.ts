import {
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import { resumenOperativoEnvelope } from "../schemas/resumen-admin.schema";
import type { ResumenOperativo } from "../types/resumen-admin.types";

/**
 * The service of the TRANSVERSAL summary (`RT-ADM-01`).
 *
 * It goes through the ONE client of the area (`pedirAdmin`), so the ledger
 * decides whether the route exists and the guard rejects the call BEFORE the
 * transport when it does not.
 *
 * The edition is a parameter of the READ, never a decision of the browser:
 * without it the backend resolves the edition with the frozen order
 * (`FREEZE-ED-1.0.0`).
 */
export async function obtenerResumenAdmin(
  edicionId?: string,
): Promise<ResumenOperativo> {
  return pedirAdmin(RUTAS_ADMIN.resumen, resumenOperativoEnvelope, {
    params: edicionId ? { edicion_id: edicionId } : undefined,
  });
}
