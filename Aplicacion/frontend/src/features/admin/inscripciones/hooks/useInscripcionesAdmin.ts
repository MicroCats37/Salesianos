"use client";

import { useAdminQuery } from "@/features/admin/operaciones/hooks/useAdminQuery";
import { envelopeAdmin } from "@/features/admin/operaciones/schemas/operaciones.schema";
import {
  RUTAS_ADMIN,
  urlDeRutaAdmin,
} from "@/features/admin/operaciones/services/admin.service";
import { adminClaves } from "@/features/admin/operaciones/utils/admin.claves.utils";
import { estadoDesdeConsulta } from "@/features/admin/operaciones/utils/admin.estado.utils";
import { parametrosListaAdminDesdeUrl } from "@/features/admin/operaciones/utils/admin.filtros.utils";
import type { PayloadRetirarParticipanteAdmin } from "@/features/admin/operaciones/utils/admin.payload.utils";
import { useApiDelete } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import {
  inscripcionAdminDetalleDesdeWire,
  inscripcionAdminDetalleEnvelope,
  inscripcionAdminListaDesdeWire,
  listaInscripcionesAdminEnvelope,
  poolDeInscripcionSchema,
} from "../schemas/inscripcion-admin.schema";
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
  const consulta = useAdminQuery({
    queryKey: adminClaves.inscripciones.list,
    ruta: RUTAS_ADMIN.inscripcionesLista,
    envelope: listaInscripcionesAdminEnvelope,
    filtros: parametrosListaAdminDesdeUrl(parametros),
    select: (pagina) => pagina.items.map(inscripcionAdminListaDesdeWire),
  });

  return estadoDesdeConsulta(
    consulta,
    RUTAS_ADMIN.inscripcionesLista.registrado,
  );
}

/** The administrative detail of a registration (`ADM-06`). */
export function useDetalleInscripcionAdmin(
  inscripcionId: string | undefined,
): EstadoDetalleInscripcionAdmin {
  const consulta = useAdminQuery({
    queryKey: adminClaves.inscripciones.detail(inscripcionId ?? ""),
    ruta: RUTAS_ADMIN.inscripcionDetalle,
    envelope: inscripcionAdminDetalleEnvelope,
    parametros: inscripcionId ? { inscripcion_id: inscripcionId } : undefined,
    enabled: Boolean(inscripcionId),
    select: (detalle) => inscripcionAdminDetalleDesdeWire(detalle),
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
 * INSIDE the mutation (`FND-08` §3 regla 5): a component that unmounts
 * while the command is in flight would never invalidate and the cache would
 * keep an answer the server never gave.
 */
export function useRetirarParticipanteAdmin() {
  return useApiDelete({
    getUrl: (variables: PayloadRetirarParticipanteAdmin) =>
      urlDeRutaAdmin(RUTAS_ADMIN.retirarParticipante, {
        inscripcion_id: variables.inscripcion_id,
        participacion_id: variables.participacion_id,
      }),
    schema: datosDelEnvelope(envelopeAdmin(poolDeInscripcionSchema)),
    invalidateKeys: [adminClaves.inscripciones.all],
  });
}
