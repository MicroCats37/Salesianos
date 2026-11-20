"use client";

import { useAdminQuery } from "@/features/admin/operaciones/hooks/useAdminQuery";
import { RUTAS_ADMIN } from "@/features/admin/operaciones/services/admin.service";
import type { ParamsListaAdmin } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { listaPersonasAdminEnvelope } from "../schemas/persona-admin.schema";
import type { EstadoPersonasAdmin } from "../types/personas-admin.types";

/**
 * The read of the administrative search of PEOPLE (`RT-ID-07`).
 *
 * The `enabled` is the REGISTRATION TRUTH: `AdminPersonaController` is not
 * registered, so the route does not exist and the surface shows the honest
 * state (`sin-datos`) instead of a spinner that never ends.
 */
export function usePersonasAdmin(
  parametros: ParamsListaAdmin = {},
): EstadoPersonasAdmin {
  const consulta = useAdminQuery({
    queryKey: adminClaves.personas.list,
    ruta: RUTAS_ADMIN.personasLista,
    envelope: listaPersonasAdminEnvelope,
    filtros: parametros,
  });

  return estadoDesdeConsulta(consulta, RUTAS_ADMIN.personasLista.registrado);
}
