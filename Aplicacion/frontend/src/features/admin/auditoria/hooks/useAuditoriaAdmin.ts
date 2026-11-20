"use client";

import { useAdminQuery } from "@/features/admin/operaciones/hooks/useAdminQuery";
import { RUTAS_ADMIN } from "@/features/admin/operaciones/services/admin.service";
import type { ParamsListaAdmin } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { auditoriaListadoEnvelope } from "../schemas/auditoria-admin.schema";
import type { EstadoAuditoriaAdmin } from "../types/auditoria-admin.types";

/**
 * The read of the ACTA of the sensitive actions (`RT-ADM-02`).
 *
 * The `enabled` is the REGISTRATION TRUTH: `AdminController` is not
 * registered, so the route does not exist and the surface shows the honest
 * state (`sin-datos`) instead of a spinner that never ends.
 *
 * The acta is a READ: it never writes, and the browser never decides which
 * entry is relevant.
 */
export function useAuditoriaAdmin(
  parametros: ParamsListaAdmin = {},
): EstadoAuditoriaAdmin {
  const consulta = useAdminQuery({
    queryKey: adminClaves.auditoria.list,
    ruta: RUTAS_ADMIN.auditoria,
    envelope: auditoriaListadoEnvelope,
    filtros: parametros,
  });

  return estadoDesdeConsulta(consulta, RUTAS_ADMIN.auditoria.registrado);
}
