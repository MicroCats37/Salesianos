"use client";

import { useAdminQuery } from "@/features/admin/operaciones/hooks/useAdminQuery";
import { RUTAS_ADMIN } from "@/features/admin/operaciones/services/admin.service";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { resumenOperativoEnvelope } from "../schemas/resumen-admin.schema";
import type { EstadoResumenAdmin } from "../types/resumen-admin.types";

/**
 * The read of the TRANSVERSAL summary (`RT-ADM-01`).
 *
 * The `enabled` is the REGISTRATION TRUTH: `AdminController` is not
 * registered, so the route does not exist and the surface shows the honest
 * state (`sin-datos`) instead of a spinner that never ends.
 *
 * The summary is a READ: it never writes, and no figure of it is computed in
 * the browser.
 */
export function useResumenAdmin(edicionId?: string): EstadoResumenAdmin {
  const consulta = useAdminQuery({
    queryKey: adminClaves.resumen.detail(edicionId ?? ""),
    ruta: RUTAS_ADMIN.resumen,
    envelope: resumenOperativoEnvelope,
    filtros: edicionId ? { edicion_id: edicionId } : undefined,
  });

  return estadoDesdeConsulta(consulta, RUTAS_ADMIN.resumen.registrado);
}
