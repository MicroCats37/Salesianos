"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import { RUTAS_ADMIN } from "@/features/admin/operaciones/services/admin.service";
import { invalidarAdmin } from "@/features/admin/operaciones/utils/admin.cache.utils";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { parametrosListaAdminDesdeUrl } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import type { PayloadRetirarParticipanteAdmin } from "@/features/admin/operaciones/utils/admin.payload.utils";
import {
  obtenerInscripcionAdmin,
  listarInscripcionesAdmin,
  retirarParticipanteAdmin,
} from "../services/inscripcion-admin.service";
import type {
  EstadoDetalleInscripcionAdmin,
  EstadoListaInscripcionesAdmin,
} from "../types/inscripciones-admin.types";

/**
 * The reads and the commands of the ADMINISTRATION OF THE REGISTRATIONS.
 *
 * | Read | Route | Wrapper |
 * |---|---|---|
 * | the list (`ADM-05`) | `GET /administracion/inscripciones` (`RT-IN-07`) | `PaginatedData[AdminInscripcionListItemOut]` |
 * | the detail (`ADM-06`) | `GET /administracion/inscripciones/{id}` (`RT-IN-08`) | `AdminInscripcionDetalleOut` |
 *
 * ## The registration truth
 *
 * `AdminInscripcionController` is NOT registered: both routes DO NOT EXIST.
 * The reads are therefore DISABLED and the surface shows the honest state
 * (`sin-datos`). The day the controller is registered, the ONLY change is
 * `registrado: true` in `RUTAS_ADMIN`.
 *
 * ## The staleness
 *
 * The administrative lists are `listadoAdministrativo` (30 s): they change
 * with the edition and with the operations of the other operators, not with
 * the second.
 */

/** The administrative list of the registrations (`ADM-05`). */
export function useListaInscripcionesAdmin(
  parametros: Record<string, string> | undefined,
): EstadoListaInscripcionesAdmin {
  const consulta = useQuery({
    ...datasetQueryOptions({
      queryKey: adminClaves.inscripciones.listPage(
        parametrosListaAdminDesdeUrl(parametros),
      ),
      queryFn: () =>
        listarInscripcionesAdmin(parametrosListaAdminDesdeUrl(parametros)),
      kind: "listadoAdministrativo",
    }),
    enabled: RUTAS_ADMIN.inscripcionesLista.registrado,
  });

  return estadoDesdeConsulta(
    consulta,
    RUTAS_ADMIN.inscripcionesLista.registrado,
    (pagina) => pagina.items,
  );
}

/** The administrative detail of a registration (`ADM-06`). */
export function useDetalleInscripcionAdmin(
  inscripcionId: string | undefined,
): EstadoDetalleInscripcionAdmin {
  const consulta = useQuery({
    ...datasetQueryOptions({
      queryKey: adminClaves.inscripciones.detail(inscripcionId ?? ""),
      queryFn: () => obtenerInscripcionAdmin(inscripcionId ?? ""),
      kind: "listadoAdministrativo",
    }),
    enabled: Boolean(inscripcionId) && RUTAS_ADMIN.inscripcionDetalle.registrado,
  });

  return estadoDesdeConsulta(
    consulta,
    RUTAS_ADMIN.inscripcionDetalle.registrado,
  );
}

/**
 * The administrative withdrawal of a participant (the S-10 of `ADM-06`).
 *
 * The command is audited: it carries the reason. The invalidation lives
 * INSIDE the `mutationFn` (`FND-08` §3 regla 5): a component that unmounts
 * while the command is in flight would never run `onSettled` and the cache
 * would keep an answer the server never gave.
 *
 * The route does NOT exist: the command is rejected by the guard of the
 * service before the transport and the action stays DISABLED in the interface.
 */
export function useRetirarParticipanteAdmin() {
  const cliente = useQueryClient();

  return useMutation({
    mutationFn: async (payload: PayloadRetirarParticipanteAdmin) => {
      const resultado = await retirarParticipanteAdmin(payload);

      await invalidarAdmin(cliente, "inscripciones");

      return resultado;
    },
  });
}
