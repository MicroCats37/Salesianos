import type { PaginatedResult } from "@/shared/schemas/pagination.schema";
import {
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import type { ParamsListaAdmin } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { parametrosConsultaAdmin } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import {
  inscripcionAdminDetalleDesdeWire,
  inscripcionAdminDetalleEnvelope,
  inscripcionAdminListaDesdeWire,
  listaInscripcionesAdminEnvelope,
  poolDeInscripcionDesdeWire,
  poolDeInscripcionSchema,
} from "../schemas/inscripcion-admin.schema";
import { envelopeAdmin } from "@/features/admin/operaciones/schemas/operaciones.schema";
import type { PayloadRetirarParticipanteAdmin } from "@/features/admin/operaciones/utils/admin.payload.utils";
import type {
  AdminInscripcionDetalleOut,
  AdminInscripcionListItemOut,
  PoolDeInscripcionOut,
} from "../types/inscripciones-admin.types";

/**
 * The client of the ADMINISTRATION OF THE REGISTRATIONS.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `RT-IN-07` | GET | `/administracion/inscripciones` | `PaginatedData[AdminInscripcionListItemOut]` |
 * | `RT-IN-08` | GET | `/administracion/inscripciones/{inscripcion_id}` | `AdminInscripcionDetalleOut` |
 *
 * ## The registration truth
 *
 * `AdminInscripcionController` is NOT registered in
 * `Aplicacion/backend/config/api.py`: both routes DO NOT EXIST. The guard of
 * `pedirAdmin` REJECTS them before the transport, so no request ever leaves
 * the browser for an URL that answers 404. The functions below are the SEAM:
 * the day A0 registers the controller, the binding is THIS file and nothing
 * else.
 *
 * ## The service returns the VIEW model
 *
 * The wire is parsed with the Zod mirror and then PROJECTED: the view never
 * sees the wire and never decides what a verdict is.
 */

/** The administrative list of the registrations (`RT-IN-07`). */
export async function listarInscripcionesAdmin(
  parametros: ParamsListaAdmin,
): Promise<PaginatedResult<AdminInscripcionListItemOut>> {
  const pagina = await pedirAdmin(
    RUTAS_ADMIN.inscripcionesLista,
    listaInscripcionesAdminEnvelope,
    { params: parametrosConsultaAdmin(parametros) },
  );

  return {
    ...pagina,
    items: pagina.items.map(inscripcionAdminListaDesdeWire),
  };
}

/** The administrative detail of a registration (`RT-IN-08`). */
export async function obtenerInscripcionAdmin(
  inscripcionId: string,
): Promise<AdminInscripcionDetalleOut> {
  const detalle = await pedirAdmin(
    RUTAS_ADMIN.inscripcionDetalle,
    inscripcionAdminDetalleEnvelope,
    { pathParams: { inscripcion_id: inscripcionId } },
  );

  return inscripcionAdminDetalleDesdeWire(detalle);
}

/**
 * The administrative withdrawal of a participant.
 *
 * ## The route DOES NOT EXIST
 *
 * The ledger declares no administrative withdrawal (`A0-UI04-04`): the
 * registered `DELETE /inscripciones/{id}/participantes/{participacion_id}`
 * (`RT-IN-06`) belongs to the RESPONSIBLE of his own inscription and the
 * module does NOT let the administrator group substitute for that
 * titularidad (`PoolOrchestrator._verificar_responsable`). It also carries no
 * reason, so it could not answer the audited action of the S-10.
 *
 * The guard of `pedirAdmin` REJECTS the command before the transport: the
 * browser never sends it.
 *
 * ## The effect is declared, never computed
 *
 * Withdrawing frees the cupo of THAT registration and it does NOT cancel the
 * purchase, does NOT return money and does NOT touch the inventory
 * (`RN-I04` · `DEC-06`). The answer is the UPDATED pool.
 */
export async function retirarParticipanteAdmin(
  payload: PayloadRetirarParticipanteAdmin,
): Promise<PoolDeInscripcionOut> {
  const pool = await pedirAdmin(
    RUTAS_ADMIN.retirarParticipante,
    envelopeAdmin(poolDeInscripcionSchema),
    {
      pathParams: {
        inscripcion_id: payload.inscripcion_id,
        participacion_id: payload.participacion_id,
      },
      payload: {
        motivo: payload.motivo,
        ...(payload.version === undefined ? {} : { version: payload.version }),
      },
    },
  );

  return poolDeInscripcionDesdeWire(pool);
}
