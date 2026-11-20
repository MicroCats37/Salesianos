import type { PaginatedResult } from "@/shared/schemas/pagination.schema";
import {
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import type { ParamsListaAdmin } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { parametrosConsultaAdmin } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import {
  listaParticipantesAdminEnvelope,
  participanteAdminDesdeWire,
} from "../schemas/participante-admin.schema";
import type { ParticipanteAdminOut } from "../types/participantes-admin.types";

/**
 * The client of the ADMINISTRATION OF THE PARTICIPANTS.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `RT-IN-11` | GET | `/administracion/participantes` | `PaginatedData[AdminParticipanteListItemOut]` |
 *
 * ## The registration truth
 *
 * `AdminParticipanteController` is NOT registered in
 * `Aplicacion/backend/config/api.py`: the route DOES NOT EXIST. The guard of
 * `pedirAdmin` REJECTS it before the transport (`A0-API04-05`).
 *
 * ## What the browser NEVER does
 *
 * It never decides that two participations collide: the conflict and its
 * reason are DECLARED by the backend (`GOV-02-RB-04b`).
 */

/** The administrative list of the participants (`RT-IN-11`). */
export async function listarParticipantesAdmin(
  parametros: ParamsListaAdmin,
): Promise<PaginatedResult<ParticipanteAdminOut>> {
  const pagina = await pedirAdmin(
    RUTAS_ADMIN.participantesLista,
    listaParticipantesAdminEnvelope,
    { params: parametrosConsultaAdmin(parametros) },
  );

  return {
    ...pagina,
    items: pagina.items.map(participanteAdminDesdeWire),
  };
}
