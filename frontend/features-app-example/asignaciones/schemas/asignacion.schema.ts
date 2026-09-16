import { z } from "zod";

// ── Legacy Asignacion Schemas ─────────────────────────────────────────────────

/**
 * Asignacion form schema for creating/updating asignaciones.
 */
export const CreateAsignacionSchema = z.object({
  tramite_id: z.string().uuid("ID de trámite inválido"),
  usuario_id: z.string().uuid("ID de usuario inválido"),
  rol: z.string().min(1, "El rol es requerido"),
  observaciones: z.string().optional(),
});

export type CreateAsignacionData = z.infer<typeof CreateAsignacionSchema>;

export const UpdateAsignacionSchema = CreateAsignacionSchema.partial();

export type UpdateAsignacionData = z.infer<typeof UpdateAsignacionSchema>;

/**
 * API response schema for asignacion data from Django REST API.
 */
export const AsignacionResponseSchema = z.object({
  id: z.string().uuid(),
  tramite_id: z.string().uuid(),
  usuario_id: z.string().uuid(),
  rol: z.string(),
  observaciones: z.string().nullable(),
  estado: z.string(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

export type AsignacionResponse = z.infer<typeof AsignacionResponseSchema>;

// ── Incorporar Area Payload ──────────────────────────────────────────────────

/**
 * Payload for POST /api/solicitudes/{id}/areas
 * Backend: IncorporarAreaIn
 */
export const IncorporarAreaSchema = z.object({
  area_id: z.string().uuid({ message: "Selecciona un área" }),
  tipo_participacion: z.enum(["PRINCIPAL", "ADJUNTA"]).default("PRINCIPAL"),
  observacion: z.string().nullable().optional(),
});

export type IncorporarAreaData = z.infer<typeof IncorporarAreaSchema>;

// ── Bandeja / Periodo Schemas ────────────────────────────────────────────────

/**
 * Nested solicitud summary for PeriodoItemSchema.
 */
const PeriodoSolicitudSummarySchema = z.object({
  id: z.string().uuid(),
  id_publico: z.string(),
  asunto: z.string(),
});

export type PeriodoSolicitudSummary = z.infer<
  typeof PeriodoSolicitudSummarySchema
>;

/**
 * PeriodoItemSchema — fields for the bandeja (inbox) view.
 * Represents a period assigned to an area in the user's bandeja operativa.
 */
export const PeriodoItemSchema = z.object({
  id: z.string().uuid(),
  numero_ciclo: z.number(),
  tipo_participacion: z.enum(["PRINCIPAL", "ADJUNTA"]),
  estado: z.enum(["ABIERTO", "CERRADO"]),
  estado_institucional: z
    .enum(["PENDIENTE", "EN_GESTION", "FINALIZADO", "CANCELADO"])
    .nullable(),
  fecha_inicio: z.string().datetime().nullable(),
  fecha_fin: z.string().datetime().nullable(),
  area_nombre: z.string(),
  solicitud: PeriodoSolicitudSummarySchema,
  participo: z.boolean(),
});

export type PeriodoItem = z.infer<typeof PeriodoItemSchema>;

/**
 * Paginated bandeja response envelope.
 * Matches backend contract: ApiResponse[PaginatedData[PeriodoItem]]
 */
export const BandejaResponseSchema = z.object({
  success: z.boolean(),
  data: z
    .object({
      items: z.array(PeriodoItemSchema),
      total: z.number(),
      page: z.number(),
      page_size: z.number(),
      total_pages: z.number(),
    })
    .nullable(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .nullable()
    .optional(),
});

export type BandejaResponse = z.infer<typeof BandejaResponseSchema>;

// ── Periodo Operation Schemas ─────────────────────────────────────────────────

/**
 * Payload for POST /api/periodos/{id}/iniciar-gestion
 * Backend: IniciarGestionIn (empty body)
 */
export const IniciarGestionPeriodoSchema = z.object({});
export type IniciarGestionPeriodoData = z.infer<
  typeof IniciarGestionPeriodoSchema
>;

/**
 * Payload for POST /api/periodos/{id}/finalizar
 * Backend: FinalizarPeriodoIn
 */
export const FinalizarPeriodoSchema = z.object({
  tipo_cierre: z.enum(["NORMAL", "ERROR"], {
    message: "Selecciona el tipo de cierre",
  }),
  motivo_cierre: z.string().min(1, "El motivo de cierre es requerido"),
});
export type FinalizarPeriodoData = z.infer<typeof FinalizarPeriodoSchema>;

/**
 * Payload for POST /api/periodos/{id}/marcar-asignacion-erronea
 * Backend: MarcarAsignacionErroneaIn
 */
export const MarcarAsignacionErroneaSchema = z.object({
  motivo: z.string().min(1, "El motivo es requerido"),
});
export type MarcarAsignacionErroneaData = z.infer<
  typeof MarcarAsignacionErroneaSchema
>;

/**
 * Payload for POST /api/periodos/{id}/cambiar-participacion
 * Backend: CambiarParticipacionIn
 */
export const CambiarParticipacionSchema = z.object({
  tipo_participacion: z.enum(["PRINCIPAL", "ADJUNTA"], {
    message: "Selecciona el tipo de participación",
  }),
  motivo: z.string().optional(),
});
export type CambiarParticipacionData = z.infer<
  typeof CambiarParticipacionSchema
>;
