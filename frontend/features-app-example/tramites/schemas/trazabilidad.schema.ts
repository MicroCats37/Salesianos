import { z } from "zod";

// ── Nested traceability schemas (mirror backend hierarchy) ──────────────────────

/**
 * PeriodoEstadoHistorialSchema — state transition record for a periodo (etapa).
 * Mirrors: backend PeriodoEstadoHistorialOut
 */
export const PeriodoEstadoHistorialSchema = z.object({
  estado_anterior: z.string().nullable(),
  estado_nuevo: z.string(),
  fecha_cambio: z.string().datetime(),
  cambiado_por_id: z.string().uuid().nullable(),
  cambiado_por_nombres: z.string(),
  origen: z.string().nullable(),
  motivo: z.string().nullable(),
});

export type PeriodoEstadoHistorial = z.infer<
  typeof PeriodoEstadoHistorialSchema
>;

/**
 * ParticipanteTrazabilidadSchema — participant assigned to a periodo.
 * Includes audit fields for assignment and removal.
 * Mirrors: backend ParticipanteTrazabilidadOut
 */
export const ParticipanteTrazabilidadSchema = z.object({
  usuario_id: z.string().uuid(),
  usuario_nombres: z.string(),
  rol: z.string().nullable(),
  fecha_inicio: z.string().datetime(),
  fecha_fin: z.string().datetime().nullable(),
  activo: z.boolean(),
  asignado_por_id: z.string().uuid().nullable(),
  asignado_por_nombres: z.string().nullable(),
  retirado_por_id: z.string().uuid().nullable(),
  retirado_por_nombres: z.string().nullable(),
  motivo_retiro: z.string().nullable(),
});

export type ParticipanteTrazabilidad = z.infer<
  typeof ParticipanteTrazabilidadSchema
>;

/**
 * RespuestaTrazabilidadSchema — formal response emitted during a periodo.
 * Mirrors: backend RespuestaTrazabilidadOut
 */
export const RespuestaTrazabilidadSchema = z.object({
  id: z.string().uuid(),
  tipo_respuesta: z.string(),
  contenido: z.string().nullable(),
  estado: z.string(),
  fecha_emision: z.string().datetime(),
  emitido_por_id: z.string().uuid().nullable(),
  emitido_por_nombres: z.string().nullable(),
});

export type RespuestaTrazabilidad = z.infer<typeof RespuestaTrazabilidadSchema>;

/**
 * PeriodoTrazabilidadSchema — period (etapa) within an area assignment.
 * Mirrors: backend PeriodoTrazabilidadOut
 */
export const PeriodoTrazabilidadSchema = z.object({
  id: z.string().uuid(),
  numero_ciclo: z.number().int(),
  tipo_participacion: z.string(),
  estado: z.string(),
  fecha_inicio: z.string().datetime(),
  fecha_fin: z.string().datetime().nullable(),
  tipo_cierre: z.string().nullable(),
  iniciado_por_id: z.string().uuid().nullable(),
  iniciado_por_nombres: z.string().nullable(),
  finalizado_por_id: z.string().uuid().nullable(),
  finalizado_por_nombres: z.string().nullable(),
  motivo_cierre: z.string().nullable(),
  historial_estados: z.array(PeriodoEstadoHistorialSchema).default([]),
  participantes: z.array(ParticipanteTrazabilidadSchema).default([]),
  respuestas: z.array(RespuestaTrazabilidadSchema).default([]),
});

export type PeriodoTrazabilidad = z.infer<typeof PeriodoTrazabilidadSchema>;

/**
 * AsignacionTrazabilidadSchema — area assignment within a Solicitud.
 * Uses `etapas` (not `periodos`) to match backend naming.
 * Mirrors: backend AsignacionTrazabilidadOut
 */
export const AsignacionTrazabilidadSchema = z.object({
  id: z.string().uuid(),
  area_id: z.string().uuid(),
  area_nombre: z.string(),
  bloquea_cierre: z.boolean(),
  fecha_incorporacion: z.string().datetime(),
  incorporado_por_id: z.string().uuid().nullable(),
  incorporado_por_nombres: z.string().nullable(),
  observacion: z.string().nullable(),
  tipo_actual: z.string().nullable(),
  etapas: z.array(PeriodoTrazabilidadSchema).default([]),
});

export type AsignacionTrazabilidad = z.infer<
  typeof AsignacionTrazabilidadSchema
>;

/**
 * HistorialEstadoGlobalTrazabilidadSchema — global state transition record for the parent Solicitud.
 * Mirrors: backend HistorialEstadoGlobalOut
 *
 * Note: Renamed from HistorialEstadoGlobal to avoid conflict with the detail schema's
 * HistorialEstadoGlobal (which lacks cambiado_por_id).
 */
export const HistorialEstadoGlobalTrazabilidadSchema = z.object({
  estado_anterior: z.string().nullable(),
  estado_nuevo: z.string(),
  fecha_cambio: z.string().datetime(),
  cambiado_por_id: z.string().uuid(),
  cambiado_por_nombres: z.string(),
  origen: z.string().nullable(),
  observacion: z.string().nullable(),
});

export type HistorialEstadoGlobalTrazabilidad = z.infer<
  typeof HistorialEstadoGlobalTrazabilidadSchema
>;

/**
 * TimelineEventSchema — single event in the chronological timeline projection.
 * Uses typed event fields (event_area_id, event_periodo_id, etc.) instead of
 * a generic dict to maintain type safety without z.any().
 * Mirrors: backend TimelineEventOut
 */
export const TimelineEventSchema = z.object({
  timestamp: z.string().datetime(),
  tipo: z.string(),
  descripcion: z.string(),
  actor_nombres: z.string().nullable(),
  actor_id: z.string().uuid().nullable(),
  event_area_id: z.string().uuid().nullable(),
  event_periodo_id: z.string().uuid().nullable(),
  event_participante_id: z.string().uuid().nullable(),
  event_respuesta_id: z.string().uuid().nullable(),
  event_estado_anterior: z.string().nullable(),
  event_estado_nuevo: z.string().nullable(),
});

export type TimelineEvent = z.infer<typeof TimelineEventSchema>;

/**
 * SolicitudTrazabilidadSchema — root schema for GET /solicitudes/{id}/trazabilidad.
 * Minimal root: only structural identifiers (solicitud_id), no duplication of
 * SolicitudDetail fields (estado, prioridad, expediente, etc.).
 * Mirrors: backend SolicitudTrazabilidadOut
 */
export const SolicitudTrazabilidadSchema = z.object({
  solicitud_id: z.string().uuid(),
  historial_estados: z
    .array(HistorialEstadoGlobalTrazabilidadSchema)
    .default([]),
  areas: z.array(AsignacionTrazabilidadSchema).default([]),
  timeline: z.array(TimelineEventSchema).default([]),
});

export type SolicitudTrazabilidad = z.infer<typeof SolicitudTrazabilidadSchema>;

// ── API Response Wrapper ──────────────────────────────────────────────────────

/**
 * SolicitudTrazabilidadResponseSchema — standard API wrapper for traceability endpoint.
 * Mirrors the backend success_response envelope: { success, data, error }.
 */
export const SolicitudTrazabilidadResponseSchema = z.object({
  success: z.boolean(),
  data: SolicitudTrazabilidadSchema.nullable(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .nullable()
    .optional(),
});

export type SolicitudTrazabilidadResponse = z.infer<
  typeof SolicitudTrazabilidadResponseSchema
>;
