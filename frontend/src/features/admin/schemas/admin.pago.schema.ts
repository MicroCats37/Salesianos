import { z } from "zod";
import { AdminErrorSchema } from "./admin.comun.schema";
import { adminPaginadoSchema } from "./admin.paginacion.schema";

/**
 * Zod mirrors of the payments (A5, A6).
 *
 * Source of truth: `backend/modules/administracion/presentation/schemas/admin_pago_schemas.py`.
 *
 * The wrapper is EXPLICIT field by field: the restricted blobs of the payment
 * module (`metadata`, `token_sesion`, `response_message`, `transaction_id`)
 * have NO place in it — they are not even declared, so they can never be
 * modelled, let alone serialized.
 */

export const AdminTransaccionListItemSchema = z.object({
  id: z.string(),
  status: z.string(),
  amount: z.number(),
  currency: z.string(),
  metodo_pago: z.string().nullable(),
  response_code: z.string().nullable(),
  created_at: z.string(),
});

export type AdminTransaccionListItem = z.infer<
  typeof AdminTransaccionListItemSchema
>;

export const AdminPagoListItemSchema = z.object({
  compra_id: z.string(),
  orden_pago_id: z.string().nullable(),
  numero_orden: z.string().nullable(),
  inscripcion_id: z.string(),
  responsable_nombre: z.string(),
  tipo: z.string(),
  cantidad: z.number(),
  precio_unitario: z.number(),
  total: z.number(),
  estado_compra: z.string(),
  estado_orden: z.string().nullable(),
  pagada_en: z.string().nullable(),
  created_at: z.string(),
});

export type AdminPagoListItem = z.infer<typeof AdminPagoListItemSchema>;

/** The drilldown of a payment order (A6): the list wrapper plus its attempts. */
export const AdminPagoDetailSchema = AdminPagoListItemSchema.extend({
  transacciones: z.array(AdminTransaccionListItemSchema),
});

export type AdminPagoDetail = z.infer<typeof AdminPagoDetailSchema>;

/** Canonical paginated container of the payments table (A5). */
export const AdminPagoListadoSchema = adminPaginadoSchema(
  AdminPagoListItemSchema,
);

export type AdminPagoListado = z.infer<typeof AdminPagoListadoSchema>;

export const AdminPagoListadoEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminPagoListadoSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminPagoListadoEnvelope = z.infer<
  typeof AdminPagoListadoEnvelopeSchema
>;

export const AdminPagoDetalleEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminPagoDetailSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminPagoDetalleEnvelope = z.infer<
  typeof AdminPagoDetalleEnvelopeSchema
>;
