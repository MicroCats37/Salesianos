"use client";

import { useQuery } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import { RUTAS_ADMIN } from "@/features/admin/operaciones/services/admin.service";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { parametrosListaAdminDesdeUrl } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import { listarParticipantesAdmin } from "../services/participante-admin.service";
import type { EstadoParticipantesAdmin } from "../types/participantes-admin.types";

/**
 * The read of the ADMINISTRATION OF THE PARTICIPANTS.
 *
 * | Read | Route | Wrapper |
 * |---|---|---|
 * | the search (`ADM-09`) | `GET /administracion/participantes` (`RT-IN-11`) | `PaginatedData[AdminParticipanteListItemOut]` |
 *
 * ## The registration truth
 *
 * `AdminParticipanteController` is NOT registered: the route DOES NOT EXIST.
 * The read is DISABLED and the surface shows the honest state.
 *
 * The search itself (`q`) is the free text of the URL: it travels to the
 * server and the browser NEVER filters a list on its own.
 */

/** The administrative search of the participants (`ADM-09`). */
export function useListaParticipantesAdmin(
  parametros: Record<string, string> | undefined,
): EstadoParticipantesAdmin {
  const consulta = useQuery({
    ...datasetQueryOptions({
      queryKey: adminClaves.participantes.listPage(
        parametrosListaAdminDesdeUrl(parametros),
      ),
      queryFn: () =>
        listarParticipantesAdmin(parametrosListaAdminDesdeUrl(parametros)),
      kind: "listadoAdministrativo",
    }),
    enabled: RUTAS_ADMIN.participantesLista.registrado,
  });

  return estadoDesdeConsulta(
    consulta,
    RUTAS_ADMIN.participantesLista.registrado,
    (pagina) => pagina.items,
  );
}
