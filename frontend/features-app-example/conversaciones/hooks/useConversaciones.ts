import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { z } from "zod";
import { useApiCreate, useApiQuery, useGenericCreateMutation } from "@/hooks";
import api from "@/lib/api";
import {
  type ConversacionDetail,
  ConversacionDetailResponseSchema,
  ConversacionResponseSchema,
  type Mensaje,
  MensajeResponseSchema,
} from "../schemas";
import { cerrarConversacion, eliminarMensaje } from "../services";

// ── Query Keys ─────────────────────────────────────────────────────────────────

const CONVERSACIONES_QUERY_KEY = ["conversaciones"] as const;
const _CONVERSACIONES_LIST_KEY = (params?: {
  page?: number;
  page_size?: number;
}) => ["conversaciones", "list", params] as const;
const CONVERSACION_DETAIL_KEY = (id: string) =>
  ["conversaciones", "detail", id] as const;

// ── useConversacionDetail ─────────────────────────────────────────────────────

/**
 * Fetch a single conversation with its messages.
 */
export function useConversacionDetail(conversacionId: string | null) {
  return useApiQuery<
    z.infer<typeof ConversacionDetailResponseSchema>,
    ConversacionDetail | null
  >({
    queryKey: CONVERSACION_DETAIL_KEY(conversacionId ?? ""),
    url: conversacionId ? `/conversaciones/${conversacionId}` : null,
    schema: ConversacionDetailResponseSchema,
    queryOptions: {
      enabled: Boolean(conversacionId),
      select: (response) => response.data ?? null,
    },
  });
}

// ── useCrearMensaje ───────────────────────────────────────────────────────────

export interface CrearMensajeVariables {
  conversacionId: string;
  contenido: string;
  archivos: Array<{ file: File; descripcion?: string | null }>;
  mensaje_padre_id?: string | null;
  /** Array of mentioned user IDs — sent as [{ usuario_id: uuid }] */
  menciones?: Array<{ usuario_id: string }>;
}

/**
 * Transforms a flat File[] into the backend-compatible archivos_adjuntos format,
 * following the expedienteproven pattern.
 * Each entry has metadata fields plus the actual File object (which buildApiPayload
 * will tokenize to file_<uuid> in the JSON and attach separately as multipart).
 */
function toArchivoAdjuntoPayload(archivos: CrearMensajeVariables["archivos"]) {
  return archivos.map((item) => ({
    nombre_original: item.file.name,
    mime_type: item.file.type || null,
    tamano_bytes: item.file.size,
    archivo: item.file,
    descripcion: item.descripcion ?? null,
  }));
}

/**
 * Mutation: post a new message to a conversation.
 *
 * Uses useGenericCreateMutation with:
 * - Dynamic URL via function (vars) => `/conversaciones/${vars.conversacionId}/mensajes`
 * - mapVariables to transform UI vars to backend format before buildApiPayload
 * - forceFormData: true — backend always expects FormData with "data" field
 * - afterSuccess for conversation detail cache invalidation
 *
 * Architecture contract compliance:
 * - Uses generic create hook (not raw useMutation) ✓
 * - buildApiPayload called inside generic hook infrastructure ✓
 * - URL is dynamic via function ✓
 * - Variable transformation in mapVariables (domain shaping), not payload construction
 */
export function useCrearMensaje() {
  return useGenericCreateMutation<Mensaje, CrearMensajeVariables>({
    queryKey: ["mensajes", "create"],
    url: (vars) => `/conversaciones/${vars.conversacionId}/mensajes`,
    schema: MensajeResponseSchema,
    mapVariables: (vars) => ({
      contenido: vars.contenido || null,
      archivos_adjuntos: toArchivoAdjuntoPayload(vars.archivos),
      mensaje_padre_id: vars.mensaje_padre_id ?? null,
      menciones: vars.menciones ?? [],
    }),
    forceFormData: true,
    afterSuccess: (queryClient, _rawResult, variables) => {
      queryClient.invalidateQueries({
        queryKey: CONVERSACION_DETAIL_KEY(variables.conversacionId),
      });
    },
  });
}

// ── useCrearComentarioSolicitud ─────────────────────────────────────────────

/**
 * Variables for the contextual solicitud comment mutation.
 * Maps 1:1 to the UI state owned by ConversacionPanel.
 */
export interface CrearComentarioSolicitudVariables {
  /** ID of the parent solicitud — drives the URL */
  solicitudId: string;
  /** ID of the conversation — drives the URL */
  conversacionId: string;
  contenido: string;
  archivos: Array<{ file: File; descripcion?: string | null }>;
  mensaje_padre_id?: string | null;
  /** Array of mentioned user IDs — sent as [{ usuario_id: uuid }] */
  menciones?: Array<{ usuario_id: string }>;
}

/**
 * Mutation: post a new comment to a solicitud conversation via the contextual
 * endpoint added in Batch 4.
 *
 * URL: POST /solicitudes/{solicitud_id}/conversaciones/{conversacion_id}/comentarios
 *
 * Uses useGenericCreateMutation with:
 * - Dynamic URL via function (vars) => contextual endpoint
 * - Same mapVariables / archivos transformation as useCrearMensaje
 * - forceFormData: true — backend expects FormData with "data" field
 * - afterSuccess invalidates the conversation detail cache
 *
 * Architecture contract compliance:
 * - Uses generic create hook (not raw useMutation) ✓
 * - buildApiPayload called inside generic hook infrastructure ✓
 * - URL is dynamic via function ✓
 * - Variable transformation in mapVariables ✓
 * - Preserves multipart contract for attachments ✓
 * - Preserves mentions UI flow ✓
 */
export function useCrearComentarioSolicitud() {
  return useGenericCreateMutation<Mensaje, CrearComentarioSolicitudVariables>({
    queryKey: ["comentarios-solicitud", "create"],
    url: (vars) =>
      `/solicitudes/${vars.solicitudId}/conversaciones/${vars.conversacionId}/comentarios`,
    schema: MensajeResponseSchema,
    mapVariables: (vars) => ({
      contenido: vars.contenido || null,
      archivos_adjuntos: toArchivoAdjuntoPayload(vars.archivos),
      mensaje_padre_id: vars.mensaje_padre_id ?? null,
      menciones: vars.menciones ?? [],
    }),
    forceFormData: true,
    afterSuccess: (queryClient, _rawResult, variables) => {
      queryClient.invalidateQueries({
        queryKey: CONVERSACION_DETAIL_KEY(variables.conversacionId),
      });
    },
  });
}

// ── useEliminarMensaje ────────────────────────────────────────────────────────

export interface EliminarMensajeVariables {
  conversacionId: string;
  mensajeId: string;
}

/**
 * Mutation: soft-delete a message.
 */
export function useEliminarMensaje() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ mensajeId }: EliminarMensajeVariables) => {
      await eliminarMensaje(mensajeId);
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: CONVERSACION_DETAIL_KEY(variables.conversacionId),
      });
    },
  });
}

// ── useCerrarConversacion ─────────────────────────────────────────────────────

/**
 * Mutation: close a conversation.
 * Uses useMutation directly — useApiUpdate direct mode requires a static URL,
 * but the cerrar endpoint uses POST with the ID in the path.
 */
export function useCerrarConversacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (conversacionId: string) => {
      await cerrarConversacion(conversacionId);
    },
    onSuccess: (_data, conversacionId) => {
      queryClient.invalidateQueries({
        queryKey: CONVERSACION_DETAIL_KEY(conversacionId),
      });
    },
  });
}

// ── useCrearConversacion ─────────────────────────────────────────────────────

/**
 * Mutation: create a new conversation.
 */
export function useCrearConversacion() {
  const queryClient = useQueryClient();

  return useApiCreate({
    url: "/conversaciones",
    schema: ConversacionResponseSchema,
    options: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: CONVERSACIONES_QUERY_KEY });
      },
    },
  });
}

// ── useIniciarConversacion ─────────────────────────────────────────────────

export interface IniciarConversacionVariables {
  solicitudId: number;
  titulo?: string;
}

/**
 * On-demand conversation creation linked to a solicitud.
 * Creates the conversation and returns its ID so the panel can immediately
 * display it. Idempotent in intent — calling again while a conversation
 * exists is a no-op from the UX perspective (caller should only call once).
 */
export function useIniciarConversacion() {
  const queryClient = useQueryClient();

  return useMutation<{ id: string }, unknown, IniciarConversacionVariables>({
    mutationFn: async ({ solicitudId, titulo }) => {
      const response = await api.post<{
        success: boolean;
        data: { id: string } | null;
        error?: { message: string };
      }>("/conversaciones", {
        solicitud_id: solicitudId,
        titulo: titulo ?? null,
      });

      if (!response.data.success || !response.data.data) {
        throw new Error(
          response.data.error?.message ?? "Error al iniciar conversación",
        );
      }
      return response.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSACIONES_QUERY_KEY });
    },
  });
}
