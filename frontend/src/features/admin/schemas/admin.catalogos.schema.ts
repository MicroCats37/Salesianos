import { z } from "zod";
import { AdminErrorSchema } from "./admin.comun.schema";

/**
 * AdminCatalogosResponseSchema — mirror 1:1 of the backend
 * `AdminCatalogosOut`
 * (`modules/administracion/presentation/schemas/admin_catalogos_schemas.py`).
 *
 * Endpoint: GET /api/administracion/catalogos  (A2)
 *
 * The catalogs expose OPTION LISTS only: identifiers, display names and the
 * state vocabularies of the owning modules. No PII, no credential, no payment
 * detail and no QR ever travels through this wrapper.
 */

export const AdminCatalogoItemSchema = z.object({
  id: z.string(),
  nombre: z.string(),
  sigla: z.string().nullable(),
});

export type AdminCatalogoItem = z.infer<typeof AdminCatalogoItemSchema>;

export const AdminCatalogoPaqueteSchema = z.object({
  id: z.string(),
  nombre: z.string(),
  tipo: z.string(),
});

export type AdminCatalogoPaquete = z.infer<typeof AdminCatalogoPaqueteSchema>;

export const AdminEstadosCatalogosSchema = z.object({
  inscripcion: z.array(z.string()),
  compra: z.array(z.string()),
  orden_pago: z.array(z.string()),
  asignacion_cupo: z.array(z.string()),
  equipo: z.array(z.string()),
  acreditacion: z.array(z.string()),
  autorizacion_fiesta: z.array(z.string()),
  acceso: z.array(z.string()),
  pool: z.array(z.string()),
  rol_participante: z.array(z.string()),
});

export type AdminEstadosCatalogos = z.infer<typeof AdminEstadosCatalogosSchema>;

export const AdminCatalogosResponseSchema = z.object({
  evento_id: z.string(),
  evento_nombre: z.string(),
  disciplinas: z.array(AdminCatalogoItemSchema),
  paquetes: z.array(AdminCatalogoPaqueteSchema),
  promociones: z.array(AdminCatalogoItemSchema),
  categorias: z.array(AdminCatalogoItemSchema),
  puntos_acceso: z.array(z.string()),
  estados: AdminEstadosCatalogosSchema,
});

export type AdminCatalogosResponse = z.infer<
  typeof AdminCatalogosResponseSchema
>;

/** Mirror 1:1 of the backend `core.responses.ApiResponse` envelope. */
export const AdminCatalogosEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminCatalogosResponseSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminCatalogosEnvelope = z.infer<
  typeof AdminCatalogosEnvelopeSchema
>;
