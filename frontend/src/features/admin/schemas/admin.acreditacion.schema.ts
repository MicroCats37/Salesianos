import { z } from "zod";
import { AdminErrorSchema } from "./admin.comun.schema";
import { adminPaginadoSchema } from "./admin.paginacion.schema";

/**
 * Zod mirrors of the accreditations and of the access log (A10, A11, A12).
 *
 * Source of truth: `backend/modules/administracion/presentation/schemas/admin_acreditacion_schemas.py`.
 *
 * `codigo_qr` is ABSENT from every wrapper: it is a live bearer credential
 * and must never travel in a read payload. It is not even declared here, so
 * the client cannot model it.
 */

export const AdminAccesoListItemSchema = z.object({
  id: z.string(),
  acreditacion_id: z.string(),
  persona_nombre: z.string(),
  persona_documento: z.string(),
  resultado: z.string(),
  punto_acceso: z.string().nullable(),
  operador_nombre: z.string().nullable(),
  fecha_hora: z.string(),
});

export type AdminAccesoListItem = z.infer<typeof AdminAccesoListItemSchema>;

export const AdminAcreditacionListItemSchema = z.object({
  id: z.string(),
  persona_id: z.string(),
  persona_nombre: z.string(),
  persona_documento: z.string(),
  estado: z.string(),
  acceso_fiesta: z.boolean(),
  acceso_box: z.boolean().nullable(),
  autorizacion_fiesta: z.string(),
  habilitado: z.boolean().nullable(),
  observacion: z.string(),
  accesos_permitidos: z.number(),
  ultimo_acceso: z.string().nullable(),
});

export type AdminAcreditacionListItem = z.infer<
  typeof AdminAcreditacionListItemSchema
>;

/** The drilldown of an accreditation (A11): the list wrapper plus its accesses. */
export const AdminAcreditacionDetailSchema =
  AdminAcreditacionListItemSchema.extend({
    accesos: z.array(AdminAccesoListItemSchema),
  });

export type AdminAcreditacionDetail = z.infer<
  typeof AdminAcreditacionDetailSchema
>;

/** Canonical paginated container of the accreditations table (A10). */
export const AdminAcreditacionListadoSchema = adminPaginadoSchema(
  AdminAcreditacionListItemSchema,
);

export type AdminAcreditacionListado = z.infer<
  typeof AdminAcreditacionListadoSchema
>;

export const AdminAcreditacionListadoEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminAcreditacionListadoSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminAcreditacionListadoEnvelope = z.infer<
  typeof AdminAcreditacionListadoEnvelopeSchema
>;

export const AdminAcreditacionDetalleEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminAcreditacionDetailSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminAcreditacionDetalleEnvelope = z.infer<
  typeof AdminAcreditacionDetalleEnvelopeSchema
>;

/** Canonical paginated container of the access log (A12). */
export const AdminAccesoListadoSchema = adminPaginadoSchema(
  AdminAccesoListItemSchema,
);

export type AdminAccesoListado = z.infer<typeof AdminAccesoListadoSchema>;

export const AdminAccesoListadoEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminAccesoListadoSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminAccesoListadoEnvelope = z.infer<
  typeof AdminAccesoListadoEnvelopeSchema
>;
