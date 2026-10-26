"use client";

import {
  type AdminAccesoListadoEnvelope,
  AdminAccesoListadoEnvelopeSchema,
  type AdminAcreditacionDetalleEnvelope,
  AdminAcreditacionDetalleEnvelopeSchema,
  type AdminAcreditacionListadoEnvelope,
  AdminAcreditacionListadoEnvelopeSchema,
  type AdminEquipoListadoEnvelope,
  AdminEquipoListadoEnvelopeSchema,
  type AdminParticipacionListadoEnvelope,
  AdminParticipacionListadoEnvelopeSchema,
  type AdminParticipanteListadoEnvelope,
  AdminParticipanteListadoEnvelopeSchema,
} from "../schemas";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";
import { adminGet } from "./admin.http.service";

/**
 * AdminOperacionService — the teams (A7), the people (A8), the roster rows
 * (A9), the accreditations (A10, A11) and the access log (A12).
 *
 * Endpoints:
 * - GET /api/administracion/equipos
 * - GET /api/administracion/participantes
 * - GET /api/administracion/participaciones
 * - GET /api/administracion/acreditaciones
 * - GET /api/administracion/acreditaciones/{id}
 * - GET /api/administracion/accesos
 *
 * The people and the roster rows are TWO different surfaces: one paid cup
 * authorises a person in EVERY contracted discipline, so the counts are never
 * interchangeable. Both are computed by the backend.
 */

/** Page of the teams of the active event. */
export async function getAdminEquipos(
  estado: AdminEstadoLista,
): Promise<AdminEquipoListadoEnvelope> {
  return adminGet(
    "/administracion/equipos",
    AdminEquipoListadoEnvelopeSchema,
    adminParametrosConsulta(estado),
  );
}

/** Page of the registered people of the active event (the POOL surface). */
export async function getAdminParticipantes(
  estado: AdminEstadoLista,
): Promise<AdminParticipanteListadoEnvelope> {
  return adminGet(
    "/administracion/participantes",
    AdminParticipanteListadoEnvelopeSchema,
    adminParametrosConsulta(estado),
  );
}

/** Page of the roster rows of the active event. */
export async function getAdminParticipaciones(
  estado: AdminEstadoLista,
): Promise<AdminParticipacionListadoEnvelope> {
  return adminGet(
    "/administracion/participaciones",
    AdminParticipacionListadoEnvelopeSchema,
    adminParametrosConsulta(estado),
  );
}

/** Page of the accreditations of the active event. */
export async function getAdminAcreditaciones(
  estado: AdminEstadoLista,
): Promise<AdminAcreditacionListadoEnvelope> {
  return adminGet(
    "/administracion/acreditaciones",
    AdminAcreditacionListadoEnvelopeSchema,
    adminParametrosConsulta(estado),
  );
}

/** Drilldown of one accreditation of the active event. */
export async function getAdminAcreditacionDetalle(
  acreditacionId: string,
): Promise<AdminAcreditacionDetalleEnvelope> {
  return adminGet(
    `/administracion/acreditaciones/${acreditacionId}`,
    AdminAcreditacionDetalleEnvelopeSchema,
  );
}

/** Page of the access log of the active event. */
export async function getAdminAccesos(
  estado: AdminEstadoLista,
): Promise<AdminAccesoListadoEnvelope> {
  return adminGet(
    "/administracion/accesos",
    AdminAccesoListadoEnvelopeSchema,
    adminParametrosConsulta(estado),
  );
}
