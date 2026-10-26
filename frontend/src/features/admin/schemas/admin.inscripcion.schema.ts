import { z } from "zod";
import { AdminErrorSchema } from "./admin.comun.schema";
import { adminPaginadoSchema } from "./admin.paginacion.schema";
import { AdminPagoListItemSchema } from "./admin.pago.schema";

/**
 * Zod mirrors of the registrations, the teams and the participants
 * (A3, A4, A7, A8, A9).
 *
 * Source of truth: `backend/modules/administracion/presentation/schemas/admin_inscripcion_schemas.py`.
 *
 * The wrappers are COMPOSED, never duplicated: the team block and the
 * participant block are shared by the list and the drilldown endpoints, and
 * the drilldown wrapper INHERITS the list wrapper instead of repeating its
 * fields (`contract/SCHEMA_DRY_INTENTION.md`).
 *
 * Every wrapper is explicit: no generic `data` / `contexto` envelope
 * (`contract/api-wrapper-presenter-contract.md` §5).
 *
 * `date` and `datetime` fields are typed as strings on purpose: the backend
 * serializes `date` as `YYYY-MM-DD` and `datetime` as a naive ISO-8601
 * instant, and a strict ISO validator would reject valid payloads.
 */

export const AdminEquipoListItemSchema = z.object({
  id: z.string(),
  nombre: z.string(),
  disciplina_sigla: z.string(),
  disciplina_nombre: z.string(),
  categoria_nombre: z.string().nullable(),
  inscripcion_id: z.string(),
  inscripcion_ref: z.string(),
  estado: z.string(),
  jugadores_registrados: z.number(),
  minimo_deportivo: z.number(),
  faltantes: z.number(),
  estado_roster: z.string(),
  created_at: z.string(),
});

export type AdminEquipoListItem = z.infer<typeof AdminEquipoListItemSchema>;

export const AdminParticipacionListItemSchema = z.object({
  id: z.string(),
  inscripcion_persona_id: z.string(),
  persona_nombre: z.string(),
  persona_documento: z.string(),
  equipo_nombre: z.string(),
  disciplina_sigla: z.string(),
  inscripcion_id: z.string(),
  rol: z.string(),
  talla_camiseta: z.string(),
  estado: z.string(),
  created_at: z.string(),
});

export type AdminParticipacionListItem = z.infer<
  typeof AdminParticipacionListItemSchema
>;

/** The drilldown of a team: the list wrapper plus its roster rows. */
export const AdminEquipoDetalleSchema = AdminEquipoListItemSchema.extend({
  participaciones: z.array(AdminParticipacionListItemSchema),
});

export type AdminEquipoDetalle = z.infer<typeof AdminEquipoDetalleSchema>;

export const AdminParticipanteListItemSchema = z.object({
  inscripcion_persona_id: z.string(),
  persona_id: z.string(),
  persona_nombre: z.string(),
  persona_documento: z.string(),
  inscripcion_id: z.string(),
  estado: z.string(),
  estado_pool: z.string(),
  motivo_bloqueo: z.string().nullable(),
  tiene_cupo_activo: z.boolean(),
  disciplinas: z.array(z.string()),
  created_at: z.string(),
});

export type AdminParticipanteListItem = z.infer<
  typeof AdminParticipanteListItemSchema
>;

export const AdminAsignacionListItemSchema = z.object({
  id: z.string(),
  persona_nombre: z.string(),
  estado: z.string(),
  motivo: z.string().nullable(),
  liberada_en: z.string().nullable(),
  compra_id: z.string(),
  created_at: z.string(),
});

export type AdminAsignacionListItem = z.infer<
  typeof AdminAsignacionListItemSchema
>;

export const AdminAceptacionListItemSchema = z.object({
  persona_id: z.string(),
  tipo_aceptacion: z.string(),
  documento_version: z.string(),
  aceptado_en: z.string(),
  medio: z.string(),
});

export type AdminAceptacionListItem = z.infer<
  typeof AdminAceptacionListItemSchema
>;

export const AdminSaldoSchema = z.object({
  contratados: z.number(),
  pagados: z.number(),
  asignados_pagados: z.number(),
  disponibles_pagados: z.number(),
});

export type AdminSaldo = z.infer<typeof AdminSaldoSchema>;

export const AdminInscripcionListItemSchema = z.object({
  id: z.string(),
  evento_nombre: z.string(),
  responsable_nombre: z.string(),
  responsable_documento: z.string(),
  paquete_nombre: z.string(),
  promocion_nombre: z.string(),
  estado: z.string(),
  equipos_total: z.number(),
  equipos_completos: z.number(),
  personas: z.number(),
  participaciones: z.number(),
  cupos_contratados: z.number(),
  cupos_pagados: z.number(),
  cupos_disponibles: z.number(),
  monto_pagado: z.number(),
  created_at: z.string(),
});

export type AdminInscripcionListItem = z.infer<
  typeof AdminInscripcionListItemSchema
>;

/**
 * The drilldown of a registration (A4): the list wrapper plus the SIX
 * documented blocks — teams (with their roster), participants, purchases,
 * cup assignments, legal acceptances and the cup balance.
 */
export const AdminInscripcionDetailSchema =
  AdminInscripcionListItemSchema.extend({
    delegado_nombre: z.string().nullable(),
    observacion: z.string(),
    fecha_limite_modificacion: z.string().nullable(),
    equipos: z.array(AdminEquipoDetalleSchema),
    participantes: z.array(AdminParticipanteListItemSchema),
    compras: z.array(AdminPagoListItemSchema),
    asignaciones: z.array(AdminAsignacionListItemSchema),
    aceptaciones: z.array(AdminAceptacionListItemSchema),
    saldo: AdminSaldoSchema,
  });

export type AdminInscripcionDetail = z.infer<
  typeof AdminInscripcionDetailSchema
>;

/** Canonical paginated container of the registrations table (A3). */
export const AdminInscripcionListadoSchema = adminPaginadoSchema(
  AdminInscripcionListItemSchema,
);

export type AdminInscripcionListado = z.infer<
  typeof AdminInscripcionListadoSchema
>;

export const AdminInscripcionListadoEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminInscripcionListadoSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminInscripcionListadoEnvelope = z.infer<
  typeof AdminInscripcionListadoEnvelopeSchema
>;

export const AdminInscripcionDetalleEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminInscripcionDetailSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminInscripcionDetalleEnvelope = z.infer<
  typeof AdminInscripcionDetalleEnvelopeSchema
>;

/** Canonical paginated container of the teams table (A7). */
export const AdminEquipoListadoSchema = adminPaginadoSchema(
  AdminEquipoListItemSchema,
);

export type AdminEquipoListado = z.infer<typeof AdminEquipoListadoSchema>;

export const AdminEquipoListadoEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminEquipoListadoSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminEquipoListadoEnvelope = z.infer<
  typeof AdminEquipoListadoEnvelopeSchema
>;

/** Canonical paginated container of the registered people (A8). */
export const AdminParticipanteListadoSchema = adminPaginadoSchema(
  AdminParticipanteListItemSchema,
);

export type AdminParticipanteListado = z.infer<
  typeof AdminParticipanteListadoSchema
>;

export const AdminParticipanteListadoEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminParticipanteListadoSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminParticipanteListadoEnvelope = z.infer<
  typeof AdminParticipanteListadoEnvelopeSchema
>;

/** Canonical paginated container of the roster rows (A9). */
export const AdminParticipacionListadoSchema = adminPaginadoSchema(
  AdminParticipacionListItemSchema,
);

export type AdminParticipacionListado = z.infer<
  typeof AdminParticipacionListadoSchema
>;

export const AdminParticipacionListadoEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminParticipacionListadoSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminParticipacionListadoEnvelope = z.infer<
  typeof AdminParticipacionListadoEnvelopeSchema
>;
