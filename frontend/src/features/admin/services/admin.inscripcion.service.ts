"use client";

import {
  type AdminInscripcionDetalleEnvelope,
  AdminInscripcionDetalleEnvelopeSchema,
  type AdminInscripcionListadoEnvelope,
  AdminInscripcionListadoEnvelopeSchema,
} from "../schemas";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";
import { adminGet } from "./admin.http.service";

/**
 * AdminInscripcionService — the registrations table (A3) and its drilldown
 * (A4).
 *
 * Endpoints:
 * - GET /api/administracion/inscripciones        (A3)
 * - GET /api/administracion/inscripciones/{id}   (A4)
 *
 * The service NEVER recomputes an operational counter: the teams, the people,
 * the roster rows, the cup balance and the amounts are computed by the
 * backend (`contract/api-wrapper-presenter-contract.md` §7).
 */

/** Page of the registrations table of the active event. */
export async function getAdminInscripciones(
  estado: AdminEstadoLista,
): Promise<AdminInscripcionListadoEnvelope> {
  return adminGet(
    "/administracion/inscripciones",
    AdminInscripcionListadoEnvelopeSchema,
    adminParametrosConsulta(estado),
  );
}

/** Drilldown of one registration of the active event. */
export async function getAdminInscripcionDetalle(
  inscripcionId: string,
): Promise<AdminInscripcionDetalleEnvelope> {
  return adminGet(
    `/administracion/inscripciones/${inscripcionId}`,
    AdminInscripcionDetalleEnvelopeSchema,
  );
}
