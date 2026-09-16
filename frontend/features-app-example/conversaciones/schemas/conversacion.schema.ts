import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

// ── Archivo Adjunto ───────────────────────────────────────────────────────────

/**
 * Archivo adjunto response from backend.
 * Includes archivo_url for download links.
 */
export const ArchivoAdjuntoSchema = z.object({
  id: z.string().uuid(),
  nombre_original: z.string(),
  mime_type: z.string().nullable().optional(),
  tamano_bytes: z.number().nullable().optional(),
  archivo_url: z.string().nullable().optional(),
  descripcion: z.string().nullable().optional(),
});

export type ArchivoAdjunto = z.infer<typeof ArchivoAdjuntoSchema>;

// ── Mención ───────────────────────────────────────────────────────────────────

/**
 * Usuario mencionado en un mensaje.
 */
export const MencionSchema = z.object({
  id: z.string().uuid(),
  usuario_id: z.string().uuid(),
});

export type Mencion = z.infer<typeof MencionSchema>;

// ── Mensaje ───────────────────────────────────────────────────────────────────

/**
 * Un mensaje dentro de una conversación.
 * Incluye archivos adjuntos, menciones y referencia a mensaje padre (reply).
 * autor_usuario_id es nullable para mensajes de sistema (tipo=SISTEMA).
 */
export const MensajeSchema = z.object({
  id: z.string().uuid(),
  conversacion_id: z.string().uuid(),
  autor_usuario_id: z.string().uuid().nullable().optional(),
  /** Author display name — populated from joined autor_usuario when available. */
  autor_nombre: z.string().nullable().optional(),
  /** Author username — populated from joined autor_usuario when available. */
  autor_username: z.string().nullable().optional(),
  contenido: z.string().nullable().optional(),
  tipo: z.string(),
  fecha_envio: z.string().datetime(),
  mensaje_padre_id: z.string().uuid().nullable().optional(),
  editado_at: z.string().datetime().nullable().optional(),
  eliminado_at: z.string().datetime().nullable().optional(),
  eliminado_por_id: z.string().uuid().nullable().optional(),
  archivos_adjuntos: z.array(ArchivoAdjuntoSchema),
  menciones: z.array(MencionSchema),
});

export type Mensaje = z.infer<typeof MensajeSchema>;

// ── Conversación ───────────────────────────────────────────────────────────────

/**
 * Conversación sin mensajes (para listados).
 */
export const ConversacionSchema = z.object({
  id: z.string().uuid(),
  titulo: z.string().nullable().optional(),
  creada_por_id: z.string().uuid(),
  fecha_inicio: z.string().datetime(),
  fecha_cierre: z.string().datetime().nullable().optional(),
  cerrado_por_id: z.string().uuid().nullable().optional(),
  estado: z.string(),
});

export type Conversacion = z.infer<typeof ConversacionSchema>;

/**
 * Detalle de conversación con sus mensajes.
 */
export const ConversacionDetailSchema = z.object({
  id: z.string().uuid(),
  titulo: z.string().nullable().optional(),
  creada_por_id: z.string().uuid(),
  fecha_inicio: z.string().datetime(),
  fecha_cierre: z.string().datetime().nullable().optional(),
  cerrado_por_id: z.string().uuid().nullable().optional(),
  estado: z.string(),
  mensajes: z.array(MensajeSchema),
});

export type ConversacionDetail = z.infer<typeof ConversacionDetailSchema>;

// ── API Response Wrappers ─────────────────────────────────────────────────────

/**
 * Paginated list response — ApiResponse[PaginatedData[Conversacion]].
 */
export const ConversacionListResponseSchema = apiResponseSchema(
  z.object({
    items: z.array(ConversacionSchema),
    total: z.number(),
    page: z.number(),
    page_size: z.number(),
    total_pages: z.number(),
  }),
);
export type ConversacionListResponse = z.infer<
  typeof ConversacionListResponseSchema
>;

/**
 * Detail response — ApiResponse[ConversacionDetailOut].
 */
export const ConversacionDetailResponseSchema = apiResponseSchema(
  ConversacionDetailSchema,
);
export type ConversacionDetailResponse = z.infer<
  typeof ConversacionDetailResponseSchema
>;

/**
 * Single object response — ApiResponse[ConversacionOut].
 */
export const ConversacionResponseSchema = apiResponseSchema(ConversacionSchema);
export type ConversacionResponse = z.infer<typeof ConversacionResponseSchema>;

/**
 * Mensaje created response — ApiResponse[MensajeOut].
 */
export const MensajeResponseSchema = apiResponseSchema(MensajeSchema);
export type MensajeResponse = z.infer<typeof MensajeResponseSchema>;

// ── Create Payloads ─────────────────────────────────────────────────────────

/**
 * Payload for creating a new message.
 * contenido is optional when there are files.
 * archivos_adjuntos carries structured attachment objects — each with metadata
 * (nombre_original, mime_type, tamano_bytes) plus the File object.
 * buildApiPayload tokenizes the File objects inside archivos_adjuntos automatically,
 * producing the backend-compatible multipart/form-data payload:
 *   JSON: { archivos_adjuntos: [{ ..., archivo: "file_<uuid>" }] }
 *   Multipart files: "file_<uuid>___realname.ext"
 * Backend parse_form_json + hydrate_form replaces token strings with real
 * UploadedFile objects before schema validation.
 * mensaje_padre_id references the parent message for reply threading.
 * menciones carries [{ usuario_id: uuid }] for user mentions.
 */
export const MensajeCreateSchema = z.object({
  contenido: z.string().nullable().optional(),
  archivos_adjuntos: z
    .array(
      z.object({
        nombre_original: z.string(),
        mime_type: z.string().nullable().optional(),
        tamano_bytes: z.number().nullable().optional(),
        archivo: z.instanceof(File),
        descripcion: z.string().nullable().optional().default(null),
      }),
    )
    .default([]),
  mensaje_padre_id: z.string().uuid().nullable().optional(),
  menciones: z.array(z.object({ usuario_id: z.string().uuid() })).default([]),
});

export type MensajeCreate = z.infer<typeof MensajeCreateSchema>;

/**
 * Payload for creating a new conversation.
 */
export const ConversacionCreateSchema = z.object({
  titulo: z.string().nullable().optional(),
  solicitud_id: z.number().nullable().optional(),
});

export type ConversacionCreate = z.infer<typeof ConversacionCreateSchema>;
