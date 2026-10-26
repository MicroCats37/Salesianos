"use client";

import {
  type AdminUsuarioDetalleEnvelope,
  AdminUsuarioDetalleEnvelopeSchema,
  type AdminUsuarioListadoEnvelope,
  AdminUsuarioListadoEnvelopeSchema,
} from "../schemas";
import type { AdminEstadoLista } from "../utils/admin.lista.utils";
import { adminParametrosConsulta } from "../utils/admin.lista.utils";
import { adminGet } from "./admin.http.service";

/**
 * AdminUsuarioService — the accounts table (A13) and its drilldown (A14).
 *
 * Endpoints:
 * - GET /api/administracion/usuarios         (A13)
 * - GET /api/administracion/usuarios/{id}    (A14)
 *
 * The surface is READ-ONLY: the response NEVER carries the password, its
 * hash, any token, nor `is_superuser`. The accounts are global identities;
 * the registrations of the drilldown ARE scoped to the active event.
 */

/** Page of the accounts. */
export async function getAdminUsuarios(
  estado: AdminEstadoLista,
): Promise<AdminUsuarioListadoEnvelope> {
  return adminGet(
    "/administracion/usuarios",
    AdminUsuarioListadoEnvelopeSchema,
    adminParametrosConsulta(estado),
  );
}

/** Drilldown of one account. */
export async function getAdminUsuarioDetalle(
  usuarioId: string,
): Promise<AdminUsuarioDetalleEnvelope> {
  return adminGet(
    `/administracion/usuarios/${usuarioId}`,
    AdminUsuarioDetalleEnvelopeSchema,
  );
}
