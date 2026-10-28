import { z } from "zod";
import { AdminErrorSchema } from "./admin.comun.schema";

/**
 * AdminResumenResponseSchema — mirror 1:1 of the backend
 * `AdminResumenOut` (`modules/administracion/presentation/schemas/admin_resumen_schemas.py`).
 *
 * Endpoint: GET /api/administracion/resumen  (A1)
 *
 * ONE explicitly named wrapper per block — never a generic `data`/`contexto`
 * envelope (`contract/api-wrapper-presenter-contract.md` §5). Every number is
 * computed by the backend; the frontend never re-derives counts, balances or
 * eligibility (`contract/api-wrapper-presenter-contract.md` §7).
 *
 * The blocks are COMPOSED (not inherited), mirroring the backend intent of
 * `contract/SCHEMA_DRY_INTENTION.md`.
 *
 * Date and datetime fields are typed as strings on purpose: the backend
 * serializes `date` as `YYYY-MM-DD` and `datetime` as ISO-8601, and a naive
 * backend datetime carries no timezone offset — a strict ISO validator would
 * reject valid payloads.
 */

export const EventoResumenSchema = z.object({
  id: z.string(),
  nombre: z.string(),
  fecha_inicio: z.string(),
  fecha_fin: z.string(),
  esta_activo: z.boolean(),
  fecha_limite_modificacion: z.string().nullable(),
  puede_modificar: z.boolean(),
});

export type EventoResumen = z.infer<typeof EventoResumenSchema>;

export const AdminInscripcionesResumenSchema = z.object({
  total: z.number(),
  por_estado: z.record(z.string(), z.number()),
  creadas_ultimos_7_dias: z.number(),
});

export type AdminInscripcionesResumen = z.infer<
  typeof AdminInscripcionesResumenSchema
>;

export const AdminPagosResumenSchema = z.object({
  compras_total: z.number(),
  compras_pagadas: z.number(),
  compras_pendientes: z.number(),
  compras_canceladas: z.number(),
  monto_pagado: z.number(),
  monto_pendiente: z.number(),
  ordenes_vencidas: z.number(),
  compras_pagadas_sin_liquidar: z.number(),
});

export type AdminPagosResumen = z.infer<typeof AdminPagosResumenSchema>;

export const AdminCuposResumenSchema = z.object({
  contratado: z.number(),
  pagado: z.number(),
  asignado_activo: z.number(),
  disponible_pagado: z.number(),
  inscripciones_con_capacidad_exhaustada: z.number(),
});

export type AdminCuposResumen = z.infer<typeof AdminCuposResumenSchema>;

/**
 * The party passes of the event — a SEPARATE block.
 *
 * The pass revenue never contaminates the sports purchase or cupo metrics:
 * they are different products and they are reported apart.
 */
export const AdminPasesResumenSchema = z.object({
  /** Passes of the purchases that were not cancelled. */
  pases_vendidos: z.number(),
  /** Passes of the PAID purchases. */
  pases_pagados: z.number(),
  /** Amount of the paid passes. */
  monto_pases_pagado: z.number(),
  /** Rights that still grant access (a revoked right keeps its slot). */
  beneficiarios_activos: z.number(),
});

export type AdminPasesResumen = z.infer<typeof AdminPasesResumenSchema>;

export const AdminDisciplinaConteoSchema = z.object({
  disciplina_id: z.string(),
  sigla: z.string(),
  nombre: z.string(),
  total: z.number(),
});

export type AdminDisciplinaConteo = z.infer<typeof AdminDisciplinaConteoSchema>;

export const AdminEquiposResumenSchema = z.object({
  total: z.number(),
  completos: z.number(),
  incompletos: z.number(),
  por_disciplina: z.array(AdminDisciplinaConteoSchema),
});

export type AdminEquiposResumen = z.infer<typeof AdminEquiposResumenSchema>;

export const AdminParticipantesResumenSchema = z.object({
  personas_distintas: z.number(),
  participaciones_activas: z.number(),
  en_pool: z.number(),
  sin_cupo_activo: z.number(),
});

export type AdminParticipantesResumen = z.infer<
  typeof AdminParticipantesResumenSchema
>;

export const AdminAcreditacionesResumenSchema = z.object({
  total: z.number(),
  por_estado: z.record(z.string(), z.number()),
  con_acceso_fiesta: z.number(),
  bloqueadas_por_admin: z.number(),
});

export type AdminAcreditacionesResumen = z.infer<
  typeof AdminAcreditacionesResumenSchema
>;

export const AdminAccesosResumenSchema = z.object({
  permitidos: z.number(),
  denegados: z.number(),
  ultimo_acceso: z.string().nullable(),
});

export type AdminAccesosResumen = z.infer<typeof AdminAccesosResumenSchema>;

/** The nine blocks of the operational overview. */
export const AdminResumenResponseSchema = z.object({
  evento: EventoResumenSchema,
  inscripciones: AdminInscripcionesResumenSchema,
  pagos: AdminPagosResumenSchema,
  cupos: AdminCuposResumenSchema,
  pases: AdminPasesResumenSchema,
  equipos: AdminEquiposResumenSchema,
  participantes: AdminParticipantesResumenSchema,
  acreditaciones: AdminAcreditacionesResumenSchema,
  accesos: AdminAccesosResumenSchema,
});

export type AdminResumenResponse = z.infer<typeof AdminResumenResponseSchema>;

/** Mirror 1:1 of the backend `core.responses.ApiResponse` envelope. */
export const AdminResumenEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminResumenResponseSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminResumenEnvelope = z.infer<typeof AdminResumenEnvelopeSchema>;
