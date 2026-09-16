import { z } from "zod";

// ── Estado Individual de Notificación ──────────────────────────────────────────

/**
 * Backend: NO_VISTA | VISTA | ABIERTA | DESCARTADA
 * Representa el estado individual de la interacción del usuario con la notificación.
 */
export const ESTADO_NOTIFICACION_VALUES = [
  "NO_VISTA",
  "VISTA",
  "ABIERTA",
  "DESCARTADA",
] as const;

export type EstadoNotificacionIndividual =
  (typeof ESTADO_NOTIFICACION_VALUES)[number];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function deriveEstadoIndividual(
  item: Record<string, unknown>,
): EstadoNotificacionIndividual {
  // Priority: descartada > abierta > vista > fallback
  if (item.descartada === true) {
    return "DESCARTADA";
  }
  if (item.abierta === true) {
    return "ABIERTA";
  }
  if (item.vista === true || item.estado_individual === "LEIDA") {
    return "VISTA";
  }
  // Only use existing estado_individual if it's a valid enum value
  if (
    typeof item.estado_individual === "string" &&
    (ESTADO_NOTIFICACION_VALUES as readonly string[]).includes(
      item.estado_individual,
    )
  ) {
    return item.estado_individual as EstadoNotificacionIndividual;
  }
  return "NO_VISTA";
}

/**
 * Normalizes a raw notification item from the API:
 * - Maps `expediente_id_publico` → `solicitud_id_publico` (public reference)
 * - Derives `estado_individual` from `descartada/abierta/vista` flags
 */
function normalizeNotificationItem(value: unknown): unknown {
  if (!isRecord(value)) return value;

  const item: Record<string, unknown> = { ...value };

  // expediente_id_publico → solicitud_id_publico (public reference used by UI)
  if (
    item.expediente_id_publico !== undefined &&
    item.solicitud_id_publico === undefined
  ) {
    item.solicitud_id_publico = item.expediente_id_publico;
  }

  // Derive estado_individual from flags — must succeed Zod enum validation
  item.estado_individual = deriveEstadoIndividual(item);

  return item;
}

/**
 * Extracts the `data` field from an ApiResponse wrapper and normalizes it.
 * Used for detail and action endpoints that return ApiResponse[NotificacionDetailOut].
 */
function normalizeApiResponseData<T>(value: unknown): T | null {
  if (!isRecord(value)) return null;
  const data = value.data;
  if (!isRecord(data)) return null;
  return normalizeNotificationItem(data) as T;
}

/**
 * Wraps bare paginated data (no ApiResponse envelope) into the standard
 * { success, data, error } envelope consumed by useApiQuery hooks.
 * Bare format: { items, total, page, page_size, total_pages }
 */
function normalizeNotificationListResponse(value: unknown): unknown {
  if (!isRecord(value)) return value;
  if (!("success" in value) && Array.isArray(value.items)) {
    return {
      success: true,
      data: value,
      error: null,
    };
  }
  return value;
}

// ── Notification List Item Schema (minimal — for global list) ───────────────────

/**
 * NotificationListItemObjectSchema — minimal fields returned by GET /api/notificaciones/.
 *
 * Contains only the 12 common fields: id, ambito, evento, prioridad, titulo,
 * mensaje, ocurrido_en, interactuada, vista, abierta, descartada, estado_individual.
 *
 * Contextual fields (solicitud_id, expediente_id_publico, area_nombre, periodo_id,
 * solicitud_asunto, periodo_ciclo, periodo_activo, participo, audiencia_tipo)
 * are NOT present in the list response and must be fetched via
 * GET /api/notificaciones/{id}/detalle.
 *
 * Matches backend: NotificacionListItemOut
 */
const NotificationListItemObjectSchema = z.object({
  id: z.string().uuid(),
  ambito: z.string(),
  evento: z.string(),
  prioridad: z.string(),
  titulo: z.string(),
  mensaje: z.string().optional(),
  ocurrido_en: z.string().datetime(),
  interactuada: z.boolean(),
  vista: z.boolean(),
  abierta: z.boolean(),
  descartada: z.boolean(),
  estado_individual: z.enum(ESTADO_NOTIFICACION_VALUES),
});

/**
 * Normalizes a raw list item from GET /api/notificaciones/.
 * Only derives estado_individual from flags (no field mapping needed for minimal schema).
 */
function normalizeListNotificationItem(value: unknown): unknown {
  if (!isRecord(value)) return value;
  const item: Record<string, unknown> = { ...value };
  item.estado_individual = deriveEstadoIndividual(item);
  return item;
}

export const NotificationListItemSchema = z.preprocess(
  normalizeListNotificationItem,
  NotificationListItemObjectSchema,
);

export type NotificationListItem = z.infer<typeof NotificationListItemSchema>;

// ── Notification Item Schema (full — for detail/mutations) ───────────────────

/**
 * NotificationItemObjectSchema — full item fields for detail display and mutations.
 * Includes contextual fields that are only present in detail responses
 * (solicitud_id, expediente_id_publico, area_nombre, periodo_id,
 * solicitud_asunto, periodo_ciclo, periodo_activo, participo, audiencia_tipo).
 *
 * Matches backend PaginatedData[NotificacionItem] payload fields exactly.
 */
const NotificationItemObjectSchema = z.object({
  id: z.string().uuid(),
  /** Backend sends ambito: SOLICITUD, SISTEMA */
  ambito: z.string(),
  /** Backend sends evento code within ambito */
  evento: z.string(),
  /** Backend sends prioridad: NORMAL, ALTA, CRITICA */
  prioridad: z.string(),
  titulo: z.string(),
  /** Backend sends mensaje for the notification body text. */
  mensaje: z.string().optional(),
  /** Backend sends ocurrido_en (was fecha_evento) */
  ocurrido_en: z.string().datetime(),
  area_nombre: z.string().nullable().optional(),
  /** Backend sends `solicitud_id` directly. */
  solicitud_id: z.string().uuid().nullable().optional(),
  /** Public expediente/solicitud reference — mapped from expediente_id_publico. */
  solicitud_id_publico: z.string().nullable().optional(),
  /** Backend sends expediente_id_publico; preprocess maps it to solicitud_id_publico. */
  expediente_id_publico: z.string().nullable().optional(),
  interactuada: z.boolean().optional(),
  /** Backend sends descartada/abierta/vista flags for estado derivation. */
  descartada: z.boolean().optional(),
  abierta: z.boolean().optional(),
  vista: z.boolean().optional(),
  /** Backend sends periodo_id as UUID; exposed as optional since not always present. */
  periodo_id: z.string().uuid().nullable().optional(),
  /** Backend exposes this field from expediente/asunto. */
  solicitud_asunto: z.string().nullable().optional(),
  /** Backend exposes this field from periodo.numero_ciclo. */
  periodo_ciclo: z.number().nullable().optional(),
  /** Backend exposes this field from periodo.esta_abierto. */
  periodo_activo: z.boolean().nullable().optional(),
  /** Derived from backend vista/abierta/descartada flags before enum validation. */
  estado_individual: z.enum(ESTADO_NOTIFICACION_VALUES),
  /** Backend exposes this field based on SolicitudAsignacionUsuario participation. */
  participo: z.boolean().nullable().optional(),
  /** Backend emits computed audiencia_tipo: AREA or USUARIO (from relations). */
  audiencia_tipo: z.string().optional(),
});

export const NotificationItemSchema = z.preprocess(
  normalizeNotificationItem,
  NotificationItemObjectSchema,
);

export type NotificationItem = z.infer<typeof NotificationItemSchema>;

// ── Notification Detail Schema ────────────────────────────────────────────────

/**
 * NotificationDetailDataSchema — inner notification data (what backend returns in response.data).
 * Includes full description and redirect context.
 */
const NotificationDetailDataSchema = z.preprocess(
  normalizeNotificationItem,
  NotificationItemObjectSchema.extend({
    descripcion: z.string().nullable().optional(),
  }),
);

export type NotificationDetailData = z.infer<
  typeof NotificationDetailDataSchema
>;

/**
 * NotificationDetailResponseSchema — wrapper for detail endpoint.
 * Backend returns: ApiResponse[NotificacionDetailOut] = { success, data: {...}, error }
 */
export const NotificationDetailResponseSchema = z.object({
  success: z.boolean(),
  data: NotificationDetailDataSchema.nullable(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .nullable()
    .optional(),
});

/**
 * NotificationDetailSchema — full notification detail for /notificaciones/[id].
 * Kept for backward compatibility; actual schema is the response wrapper.
 */
export const NotificationDetailSchema = NotificationDetailResponseSchema;

export type NotificationDetail = NotificationDetailData;

// ── New Detail Schema (restructured — consumed by /notificaciones/{id}/detalle) ──

/**
 * ExpedientePublicoSchema — nested expediente data from the new detail endpoint.
 * Matches backend NotificacionDetalleOut.expediente_publico.
 */
export const ExpedientePublicoSchema = z.object({
  id_publico: z.string().nullable().optional(),
  asunto: z.string().nullable().optional(),
});
export type ExpedientePublico = z.infer<typeof ExpedientePublicoSchema>;

/**
 * PeriodoContextSchema — nested periodo data from the new detail endpoint.
 * Matches backend NotificacionDetalleOut.periodo.
 */
export const PeriodoContextSchema = z.object({
  id: z.string().uuid().nullable().optional(),
  numero_ciclo: z.number().nullable().optional(),
  esta_abierto: z.boolean().nullable().optional(),
});
export type PeriodoContext = z.infer<typeof PeriodoContextSchema>;

/**
 * NotificationSolicitudDetailSchema — full notification detail from the new
 * /notificaciones/{id}/detalle endpoint.
 *
 * Restructured with nested expediente_publico and periodo instead of flat fields.
 * Does NOT extend NotificationItemObjectSchema — defines the complete shape
 * with no z.any(), no wrapper_type, and no flat expediente/periodo fields.
 *
 * Matches backend: NotificacionDetalleOut
 */
const NotificationSolicitudDetailDataSchema = z.object({
  id: z.string().uuid(),
  ambito: z.string(),
  evento: z.string(),
  prioridad: z.string(),
  titulo: z.string(),
  mensaje: z.string().nullable().optional(),
  ocurrido_en: z.string().datetime(),
  interactuada: z.boolean(),
  vista: z.boolean(),
  abierta: z.boolean(),
  descartada: z.boolean(),
  estado_individual: z.enum(ESTADO_NOTIFICACION_VALUES),
  audiencia_tipo: z.string().nullable().optional(),
  generada_por_nombres: z.string().nullable().optional(),
  // SOLICITUD contextual fields
  solicitud_id: z.string().uuid().nullable().optional(),
  expediente_publico: ExpedientePublicoSchema.nullable().optional(),
  area_id: z.string().uuid().nullable().optional(),
  area_nombre: z.string().nullable().optional(),
  periodo: PeriodoContextSchema.nullable().optional(),
  interacciones: z.array(
    z.object({
      usuario_id: z.string().uuid(),
      vista_at: z.string().datetime().nullable().optional(),
      abierta_at: z.string().datetime().nullable().optional(),
      descartada_at: z.string().datetime().nullable().optional(),
    }),
  ),
  participo: z.boolean().nullable().optional(),
  solicitud_asunto: z.string().nullable().optional(),
});

export type NotificationSolicitudDetailData = z.infer<
  typeof NotificationSolicitudDetailDataSchema
>;

/**
 * Response wrapper for the new /notificaciones/{id}/detalle endpoint.
 */
export const NotificationDetalleResponseSchema = z.object({
  success: z.boolean(),
  data: NotificationSolicitudDetailDataSchema.nullable(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .nullable()
    .optional(),
});

export type NotificationDetalleResponse = z.infer<
  typeof NotificationDetalleResponseSchema
>;

// ── API Response Schemas ──────────────────────────────────────────────────────

/**
 * Paginated response wrapper for Notificaciones list.
 * Matches backend contract: ApiResponse[PaginatedData[NotificacionListItemOut]]
 *
 * NOTE: Uses NotificationListItemSchema (12 minimal fields, no contextual fields).
 * Contextual fields must be fetched via GET /api/notificaciones/{id}/detalle.
 */
export const NotificacionListResponseSchema = z.preprocess(
  normalizeNotificationListResponse,
  z.object({
    success: z.boolean(),
    data: z
      .object({
        items: z.array(NotificationListItemSchema),
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
  }),
);

export type NotificacionListResponse = z.infer<
  typeof NotificacionListResponseSchema
>;

// ── Action Response Schemas ────────────────────────────────────────────────────

/**
 * Response after marking a notification as viewed.
 * Backend returns: ApiResponse[NotificacionDetailOut] with full notification object.
 */
export const MarcarVistaResponseSchema = z.object({
  success: z.boolean(),
  data: z
    .preprocess(
      normalizeNotificationItem,
      NotificationItemObjectSchema.extend({
        descripcion: z.string().nullable().optional(),
      }),
    )
    .nullable(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .nullable()
    .optional(),
});

export type MarcarVistaResponse = z.infer<typeof MarcarVistaResponseSchema>;

/**
 * Response after discarding a notification.
 * Backend returns: ApiResponse[NotificacionDetailOut] with full notification object.
 */
export const DescartarNotificacionResponseSchema = z.object({
  success: z.boolean(),
  data: z
    .preprocess(
      normalizeNotificationItem,
      NotificationItemObjectSchema.extend({
        descripcion: z.string().nullable().optional(),
      }),
    )
    .nullable(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .nullable()
    .optional(),
});

export type DescartarNotificacionResponse = z.infer<
  typeof DescartarNotificacionResponseSchema
>;
