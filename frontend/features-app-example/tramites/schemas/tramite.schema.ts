import { z } from "zod";

// ── Shared Pagination Schema ────────────────────────────────────────────────────

/**
 * Standard paginated response schema.
 * Matches the backend contract: ApiResponse[PaginatedData[T]]
 */
export const PaginacionSchema = z.object({
  items: z.array(z.unknown()),
  total: z.number(),
  page: z.number(),
  page_size: z.number(),
  total_pages: z.number(),
});

export type PaginacionData = z.infer<typeof PaginacionSchema>;

// ── TipoDocumento Schema (backend output contract) ─────────────────────────────────

/**
 * TipoDocumentoSchema — tipo de documento como se presenta en respuestas GET.
 * Backend: TipoDocumentoOut = { id: uuid, nombre: str, descripcion: str }
 * Used as nested object in ExpedienteItemSchema / ExpedienteDetailSchema.
 */
export const TipoDocumentoSchema = z.object({
  id: z.string().uuid(),
  nombre: z.string(),
  descripcion: z.string(),
});

export type TipoDocumento = z.infer<typeof TipoDocumentoSchema>;

// ── Expediente Schemas ─────────────────────────────────────────────────────────

/**
 * ExpedienteArchivoSchema — archivo adjunto de expediente.
 * Backend: ExpedienteArchivoOut
 */
export const ExpedienteArchivoSchema = z.object({
  id: z.string().uuid(),
  tipo_archivo: z.enum(["PRINCIPAL", "ANEXO"]),
  nombre_original: z.string(),
  url: z.string(),
});

export type ExpedienteArchivo = z.infer<typeof ExpedienteArchivoSchema>;

/**
 * ExpedienteBaseSchema — shared root fields for Expediente create and item schemas.
 * Derived from ExpedienteItemSchema.pick(...) to ensure consistency.
 * Uses z.coerce.number() for numero to handle backend string serialization.
 *
 * NOTE: tipo_documento is an object { id, nombre, descripcion } matching
 * backend TipoDocumentoOut, NOT a plain string. The create payload uses
 * tipo_documento_id (UUID) instead.
 */
const ExpedienteBaseSchema = z.object({
  tipo_persona: z.enum(["NATURAL", "JURIDICA", "COLEGIADO"]),
  dni: z.string().nullable(),
  ruc: z.string().nullable(),
  cip: z.string().nullable(),
  razon_social: z.string().nullable(),
  nombres: z.string().nullable(),
  apellidos: z.string().nullable(),
  correo: z.string().nullable(),
  telefono: z.string().nullable(),
  tipo_documento: TipoDocumentoSchema,
  numero_documento: z.string().nullable(),
  numero_folios: z.number().int().min(0),
  asunto: z.string(),
  observaciones: z.string().nullable(),
});

/**
 * ExpedienteItemSchema — fields for list display.
 * Matches backend: ExpedienteItemOut
 * Includes all expediente fields needed for list and detail screens.
 *
 * NOTE: numero uses z.coerce.number() because the backend may serialize it as
 * a string in some response envelopes (same pattern as liquidaciones num() helper).
 */
export const ExpedienteItemSchema = z.object({
  id: z.string().uuid(),
  numero: z.coerce.number(),
  id_publico: z.string(),
  ...ExpedienteBaseSchema.shape,
  fecha_registro: z.string().datetime(),
  archivos: z.array(ExpedienteArchivoSchema).default([]),
});

export type ExpedienteItem = z.infer<typeof ExpedienteItemSchema>;

/**
 * ExpedienteAntecedenteSchema — antecedente vinculado a un expediente.
 * Backend: ExpedienteAntecedenteOut
 */
export const ExpedienteAntecedenteSchema = z.object({
  id_publico: z.string(),
  categoria: z.string().nullable(),
  observaciones: z.string().nullable(),
});

export type ExpedienteAntecedente = z.infer<typeof ExpedienteAntecedenteSchema>;

/**
 * ExpedienteDetailSchema — full detail with archivos, antecedentes, creado_por, solicitud.
 * Matches backend: ExpedienteDetailOut
 */
export const ExpedienteDetailSchema = ExpedienteItemSchema.extend({
  antecedentes: z.array(ExpedienteAntecedenteSchema).default([]),
  creado_por_nombres: z.string().nullable(),
  solicitud_id: z.string().uuid().nullable(),
  solicitud_estado: z.string().nullable(),
  solicitud_prioridad: z.string().nullable(),
});

export type ExpedienteDetail = z.infer<typeof ExpedienteDetailSchema>;

// ── Solicitud Schemas ──────────────────────────────────────────────────────────

/**
 * AreaActivaSchema — área activa con estado de período.
 * Backend: AreaActivaOut
 */
export const AreaActivaSchema = z.object({
  area_id: z.string().uuid(),
  area_nombre: z.string(),
  tipo_participacion: z.enum(["PRINCIPAL", "ADJUNTA"]),
  estado_periodo: z.enum(["PENDIENTE", "EN_GESTION", "CERRADO"]),
});

export type AreaActiva = z.infer<typeof AreaActivaSchema>;

/**
 * SolicitudItemSchema — fields for list display.
 * Matches backend: SolicitudItemOut
 *
 * NOTE: The backend nests the expediente object entirely.
 * For card display, we flatten expediente fields via selectors.
 */
export const SolicitudItemSchema = z.object({
  id: z.string().uuid(),
  expediente: ExpedienteItemSchema,
  estado: z.enum(["REGISTRADA", "EN_GESTION", "FINALIZADA", "ANULADA"]),
  prioridad: z.enum(["BAJA", "MEDIA", "ALTA", "URGENTE"]),
  fecha_registro: z.string().datetime(),
  fecha_inicio_gestion: z.string().datetime().nullable(),
  fecha_limite: z.string().datetime().nullable(),
  areas_activas: z.array(AreaActivaSchema).default([]),
  conteo_pendiente: z.number().default(0),
  conteo_en_gestion: z.number().default(0),
});

export type SolicitudItem = z.infer<typeof SolicitudItemSchema>;

// ── Conversacion Summary (from SolicitudDetail backend) ─────────────────────────

/**
 * ConversacionSummarySchema — resumen de conversación vinculada a una solicitud.
 * Backend: ConversacionSummaryOut
 * Matches: backend/modules/tramites/presentation/schemas/solicitud_list_out.py::ConversacionSummaryOut
 */
export const ConversacionSummarySchema = z.object({
  id: z.string().uuid(),
  titulo: z.string().nullable().optional(),
  estado: z.string(),
  fecha_inicio: z.string().datetime(),
});

export type ConversacionSummary = z.infer<typeof ConversacionSummarySchema>;

// ── Detail Schemas (para páginas de detalle) ────────────────────────────────────

/**
 * ParticipanteDetalleSchema — participante activo o histórico de un período.
 * Backend: ParticipanteDetalleOut
 */
export const ParticipanteDetalleSchema = z.object({
  usuario_id: z.string().uuid(),
  usuario_nombres: z.string(),
  rol: z.string().nullable(),
  fecha_inicio: z.string().datetime(),
  fecha_fin: z.string().datetime().nullable(),
  activo: z.boolean(),
});

export type ParticipanteDetalle = z.infer<typeof ParticipanteDetalleSchema>;

/**
 * RespuestaDetalleSchema — respuesta de una asignación período.
 * Backend: RespuestaDetalleOut
 */
export const RespuestaDetalleSchema = z.object({
  id: z.string().uuid(),
  tipo_respuesta: z.string(),
  contenido: z.string().nullable(),
  estado: z.string(),
  fecha_emision: z.string().datetime().nullable(),
  emitido_por_nombres: z.string().nullable(),
});

export type RespuestaDetalle = z.infer<typeof RespuestaDetalleSchema>;

/**
 * PeriodoDetalleSchema — período de asignación con historial de estados.
 * Backend: PeriodoDetalleOut
 */
export const PeriodoDetalleSchema = z.object({
  id: z.string().uuid(),
  numero_ciclo: z.number(),
  tipo_participacion: z.string(),
  estado: z.string(),
  fecha_inicio: z.string().datetime(),
  fecha_fin: z.string().datetime().nullable(),
  tipo_cierre: z.string().nullable(),
  iniciado_por_nombres: z.string().nullable(),
  historial_estados: z.array(z.record(z.string(), z.unknown())).default([]),
});

export type PeriodoDetalle = z.infer<typeof PeriodoDetalleSchema>;

/**
 * AsignacionDetalleSchema — asignación completa con períodos, participantes y respuestas.
 * Backend: AsignacionDetalleOut
 */
export const AsignacionDetalleSchema = z.object({
  id: z.string().uuid(),
  area_id: z.string().uuid(),
  area_nombre: z.string(),
  bloquea_cierre: z.boolean(),
  fecha_incorporacion: z.string().datetime(),
  observacion: z.string().nullable(),
  periodos: z.array(PeriodoDetalleSchema).default([]),
  participantes: z.array(ParticipanteDetalleSchema).default([]),
  respuestas: z.array(RespuestaDetalleSchema).default([]),
});

export type AsignacionDetalle = z.infer<typeof AsignacionDetalleSchema>;

/**
 * HistorialEstadoGlobalSchema — entrada del historial global de cambios de estado.
 * Backend: HistorialEstadoGlobalOut
 */
export const HistorialEstadoGlobalSchema = z.object({
  estado_anterior: z.string().nullable(),
  estado_nuevo: z.string(),
  fecha_cambio: z.string().datetime(),
  cambiado_por_nombres: z.string(),
  origen: z.string().nullable(),
  observacion: z.string().nullable(),
});

export type HistorialEstadoGlobal = z.infer<typeof HistorialEstadoGlobalSchema>;

/**
 * SolicitudDetailSchema — detalle integral de solicitud.
 * Matches backend: SolicitudDetailOut
 */
export const SolicitudDetailSchema = z.object({
  id: z.string().uuid(),
  estado: z.enum(["REGISTRADA", "EN_GESTION", "FINALIZADA", "ANULADA"]),
  prioridad: z.enum(["BAJA", "MEDIA", "ALTA", "URGENTE"]),
  fecha_registro: z.string().datetime(),
  fecha_inicio_gestion: z.string().datetime().nullable(),
  fecha_limite: z.string().datetime().nullable(),
  fecha_cierre: z.string().datetime().nullable(),
  observacion: z.string().nullable(),
  expediente: ExpedienteDetailSchema,
  historial_global: z.array(HistorialEstadoGlobalSchema).default([]),
  asignaciones: z.array(AsignacionDetalleSchema).default([]),
  conversacion: ConversacionSummarySchema.nullable().optional(),
});

export type SolicitudDetail = z.infer<typeof SolicitudDetailSchema>;

// ── Create Tramite Schema (Hybrid Payload) ─────────────────────────────────────

/**
 * CreateTramiteSchema — the full hybrid payload for POST /api/solicitudes/crear-completo.
 * Combines expediente data + areas_distribucion + archivos.
 * Sent as multipart/form-data with data (JSON string) and files parts.
 */
export const ArchivoSchema = z.object({
  tipo_archivo: z.enum(["PRINCIPAL", "ANEXO"]),
  nombre_original: z.string(),
  descripcion: z.string().nullable().optional(),
  archivo: z.instanceof(File).optional(), // File object for local handling
  token: z.string().optional(), // token from buildApiPayload for upload
});

/**
 * ExpedienteCreateSchema — payload for POST /tramites/expedientes/crear.
 *
 * Schema sharing: comparte raíz de campos planos con ExpedienteItemSchema
 * (tipo_persona, dni, ruc, cip, nombres, apellidos, razon_social, correo,
 * telefono, tipo_documento, numero_documento, numero_folios, asunto, observaciones).
 * La diferencia es: create tiene archivos (agrupado por tipo) y validators más estrictos
 * en algunos campos (max lengths, email, enum tipo_documento).
 *
 * Para derivar desde ExpedienteItemSchema en el futuro:
 *   ExpedienteBaseSchema = ExpedienteItemSchema.pick({...campos compartidos...})
 *   ExpedienteCreateSchema = ExpedienteBaseSchema.extend({ archivos: ..., ...validators })
 */
export const ExpedienteCreateSchema = z.object({
  tipo_persona: z.enum(["NATURAL", "JURIDICA", "COLEGIADO"]),
  dni: z.string().max(8).nullable(),
  ruc: z.string().max(11).nullable(),
  cip: z.string().max(20).nullable(),
  razon_social: z.string().max(255).nullable(),
  nombres: z.string().max(150).nullable(),
  apellidos: z.string().max(150).nullable(),
  correo: z.string().email().nullable(),
  telefono: z.string().max(20).nullable(),
  tipo_documento_id: z
    .string()
    .uuid({ message: "Selecciona un tipo de documento" })
    .nullable()
    .optional(),
  numero_documento: z.string().max(50).nullable(),
  numero_folios: z.number().int().min(0),
  asunto: z.string().min(1),
  observaciones: z.string().nullable(),
  archivos: z.object({
    principal: z.array(ArchivoSchema),
    anexo: z.array(ArchivoSchema),
  }),
});

export const AreaDistribucionSchema = z.object({
  area_id: z.string().uuid(),
  tipo_participacion: z.enum(["PRINCIPAL", "ADJUNTA"]),
  observacion: z.string().nullable().optional(),
});

export const CreateTramiteSchema = z.object({
  prioridad: z.enum(["BAJA", "MEDIA", "ALTA", "URGENTE"]),
  observacion: z.string().nullable(),
  areas_distribucion: z
    .array(AreaDistribucionSchema)
    .min(1, "Al menos un área es requerida"),
  expediente: ExpedienteCreateSchema,
});

export type CreateTramiteData = z.infer<typeof CreateTramiteSchema>;
export type ExpedienteCreateData = z.infer<typeof ExpedienteCreateSchema>;
export type AreaDistribucionData = z.infer<typeof AreaDistribucionSchema>;
export type ArchivoData = z.infer<typeof ArchivoSchema>;

// ── API Response Schemas ───────────────────────────────────────────────────────

/**
 * Paginated response wrapper for Expediente list.
 */
export const ExpedienteListResponseSchema = z.object({
  success: z.boolean(),
  data: z
    .object({
      items: z.array(ExpedienteItemSchema),
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

export type ExpedienteListResponse = z.infer<
  typeof ExpedienteListResponseSchema
>;

export const ExpedienteDetailResponseSchema = z.object({
  success: z.boolean(),
  data: ExpedienteDetailSchema.nullable(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .nullable()
    .optional(),
});

export type ExpedienteDetailResponse = z.infer<
  typeof ExpedienteDetailResponseSchema
>;

/**
 * Paginated response wrapper for Solicitud list.
 */
export const SolicitudListResponseSchema = z.object({
  success: z.boolean(),
  data: z
    .object({
      items: z.array(SolicitudItemSchema),
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

export type SolicitudListResponse = z.infer<typeof SolicitudListResponseSchema>;

export const SolicitudDetailResponseSchema = z.object({
  success: z.boolean(),
  data: SolicitudDetailSchema.nullable(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .nullable()
    .optional(),
});

export type SolicitudDetailResponse = z.infer<
  typeof SolicitudDetailResponseSchema
>;

// ── Legacy Tramite (basic CRUD - being phased out) ───────────────────────────

/**
 * Legacy TramiteResponse — minimal shape for basic /tramites/ CRUD.
 * These endpoints are being superseded by Solicitudes + Expedientes.
 */
export const TramiteResponseSchema = z.object({
  id: z.string().uuid(),
  estado: z.string(),
  prioridad: z.enum(["BAJA", "MEDIA", "ALTA", "URGENTE"]),
  fecha_registro: z.string().datetime(),
});

export type TramiteResponse = z.infer<typeof TramiteResponseSchema>;

export const UpdateTramiteSchema = TramiteResponseSchema.partial();

export type UpdateTramiteData = z.infer<typeof UpdateTramiteSchema>;
