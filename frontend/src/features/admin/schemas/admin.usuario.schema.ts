import { z } from "zod";
import { ADMIN_NIVELES } from "../utils/admin.capacidades";
import { AdminErrorSchema } from "./admin.comun.schema";
import { adminPaginadoSchema } from "./admin.paginacion.schema";

/**
 * Zod mirrors of the accounts (A13, A14).
 *
 * Source of truth: `backend/modules/administracion/presentation/schemas/admin_usuario_schemas.py`.
 *
 * The wrapper is READ-ONLY and declares NO credential: no password, no hash
 * and no token.
 *
 * The TIER of the account IS published (`is_staff`, `is_superuser`,
 * `nivel`): an account administrator must be able to see who holds the
 * break-glass tier. The surface is read-only: it never promotes, demotes nor
 * deactivates anyone.
 */

export const AdminUsuarioListItemSchema = z.object({
  id: z.string(),
  username: z.string(),
  email: z.string().nullable(),
  nombres: z.string(),
  apellidos: z.string(),
  persona_id: z.string(),
  persona_documento: z.string(),
  es_admin: z.boolean(),
  is_staff: z.boolean().default(false),
  is_superuser: z.boolean().default(false),
  nivel: z
    .enum([
      ADMIN_NIVELES.USUARIO,
      ADMIN_NIVELES.STAFF,
      ADMIN_NIVELES.SUPERUSUARIO,
    ])
    .default(ADMIN_NIVELES.USUARIO),
  is_active: z.boolean(),
  last_login: z.string().nullable(),
  created_at: z.string(),
});

export type AdminUsuarioListItem = z.infer<typeof AdminUsuarioListItemSchema>;

/** A registration owned by the account, inside the active event. */
export const AdminUsuarioInscripcionSchema = z.object({
  inscripcion_id: z.string(),
  estado: z.string(),
  created_at: z.string(),
});

export type AdminUsuarioInscripcion = z.infer<
  typeof AdminUsuarioInscripcionSchema
>;

/** The drilldown of an account (A14): the list wrapper plus its registrations. */
export const AdminUsuarioDetailSchema = AdminUsuarioListItemSchema.extend({
  personas: z.array(AdminUsuarioInscripcionSchema),
});

export type AdminUsuarioDetail = z.infer<typeof AdminUsuarioDetailSchema>;

/** Canonical paginated container of the accounts table (A13). */
export const AdminUsuarioListadoSchema = adminPaginadoSchema(
  AdminUsuarioListItemSchema,
);

export type AdminUsuarioListado = z.infer<typeof AdminUsuarioListadoSchema>;

export const AdminUsuarioListadoEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminUsuarioListadoSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminUsuarioListadoEnvelope = z.infer<
  typeof AdminUsuarioListadoEnvelopeSchema
>;

export const AdminUsuarioDetalleEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminUsuarioDetailSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminUsuarioDetalleEnvelope = z.infer<
  typeof AdminUsuarioDetalleEnvelopeSchema
>;
