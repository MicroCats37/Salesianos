// features/tramites/schemas/finalizar-solicitud.schema.ts
// Schema Zod para el formulario de Finalizar Solicitud (respuesta formal).
// Endpoint: POST /api/solicitudes/{solicitud_id}/finalizar
// Backend: FinalizarSolicitudIn (FormData dual payload)

import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

// ── Tipo Respuesta ───────────────────────────────────────────────────────────────

/**
 * Tipos de respuesta formal para una Solicitud.
 * Coincide con TipoRespuesta de backend (modules/asignaciones/domain/constants.py).
 */
export const TIPO_RESPUESTA = [
  "INFORME",
  "OBSERVACION",
  "CONFORMIDAD",
  "DESCARGO",
  "OTRO",
] as const;

export type TipoRespuesta = (typeof TIPO_RESPUESTA)[number];

// ── Archivo Adjunto (response) ───────────────────────────────────────────────────

/**
 * Archivo adjunto en la respuesta del backend.
 * Backend: ArchivoAdjuntoOut
 */
export const ArchivoAdjuntoOutSchema = z.object({
  id: z.string().uuid(),
  nombre_original: z.string(),
  mime_type: z.string().nullable().optional(),
  tamano_bytes: z.number().nullable().optional(),
});

export type ArchivoAdjuntoOut = z.infer<typeof ArchivoAdjuntoOutSchema>;

// ── SolicitudRespuestaOut (response) ───────────────────────────────────────────

/**
 * Schema de salida para una SolicitudRespuesta.
 * Backend: SolicitudRespuestaOut
 */
export const SolicitudRespuestaOutSchema = z.object({
  id: z.string().uuid(),
  solicitud_id: z.string().uuid(),
  area_id: z.string().uuid(),
  area_nombre: z.string(),
  periodo_id: z.string().uuid().nullable().optional(),
  tipo_respuesta: z.string(),
  contenido: z.string().nullable().optional(),
  es_final: z.boolean(),
  fecha_emision: z.string().datetime(),
  emitido_por_id: z.string().uuid(),
  emitido_por_nombre: z.string(),
  archivos: z.array(ArchivoAdjuntoOutSchema).default([]),
  created_at: z.string().datetime(),
});

export type SolicitudRespuestaOut = z.infer<typeof SolicitudRespuestaOutSchema>;

// ── SolicitudRespuestaFinalizarOut (full response wrapper) ─────────────────────

/**
 * Response wrapper para POST /solicitudes/{id}/finalizar.
 * Backend: SolicitudRespuestaFinalizarOut
 */
export const SolicitudRespuestaFinalizarOutSchema = z.object({
  solicitud_respuesta: SolicitudRespuestaOutSchema,
  solicitud_estado: z.string(),
  fecha_cierre: z.string().datetime().nullable().optional(),
  conversacion_id: z.string().uuid().nullable().optional(),
});

export type SolicitudRespuestaFinalizarOut = z.infer<
  typeof SolicitudRespuestaFinalizarOutSchema
>;

// ── API Response ────────────────────────────────────────────────────────────────

export const FinalizarSolicitudResponseSchema = apiResponseSchema(
  SolicitudRespuestaFinalizarOutSchema,
);
export type FinalizarSolicitudResponse = z.infer<
  typeof FinalizarSolicitudResponseSchema
>;

// ── Form Data Schema (UI → API payload) ────────────────────────────────────────

/**
 * Schema del formulario de finalizar solicitud.
 * El payload se envía como FormData (dual payload pattern).
 *
 * Campos del formulario:
 * - tipo_respuesta: requerido, select
 * - contenido: requerido, textarea
 * - archivos: opcional, file input múltiple
 *
 * La transformación a FormData la realiza buildApiPayload en el hook.
 */
export const FinalizarSolicitudFormSchema = z.object({
  tipo_respuesta: z.enum(TIPO_RESPUESTA, {
    message: "Selecciona un tipo de respuesta",
  }),
  contenido: z
    .string()
    .min(1, "El contenido es requerido")
    .max(5000, "El contenido no puede exceder 5000 caracteres"),
  archivos: z
    .array(
      z.object({
        file: z.instanceof(File),
        nombre_original: z.string(),
        mime_type: z.string().nullable().optional(),
        tamano_bytes: z.number().nullable().optional(),
      }),
    )
    .default([]),
});

export type FinalizarSolicitudFormData = z.infer<
  typeof FinalizarSolicitudFormSchema
>;

// ── Helpers ─────────────────────────────────────────────────────────────────────

/** Etiquetas para los tipos de respuesta */
export const TIPO_RESPUESTA_LABELS: Record<TipoRespuesta, string> = {
  INFORME: "Informe",
  OBSERVACION: "Observación",
  CONFORMIDAD: "Conformidad",
  DESCARGO: "Descargo",
  OTRO: "Otro",
};
