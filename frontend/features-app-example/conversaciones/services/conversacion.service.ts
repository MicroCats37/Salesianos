import api from "@/lib/api";
import type {
  ConversacionCreate,
  ConversacionDetailResponse,
  ConversacionListResponse,
  ConversacionResponse,
  MensajeCreate,
  MensajeResponse,
} from "../schemas";

// ── Query ─────────────────────────────────────────────────────────────────────

/**
 * List conversations for the current user.
 */
export async function getConversaciones(params?: {
  page?: number;
  page_size?: number;
}): Promise<ConversacionListResponse> {
  const response = await api.get<ConversacionListResponse>("/conversaciones", {
    params,
  });
  return response.data;
}

/**
 * Get conversation detail by ID, including messages.
 * Returns raw response.data — hook parses with schema.
 */
export async function getConversacionDetail(
  conversacionId: string,
): Promise<ConversacionDetailResponse> {
  const response = await api.get<ConversacionDetailResponse>(
    `/conversaciones/${conversacionId}`,
  );
  return response.data;
}

// ── Mutation ─────────────────────────────────────────────────────────────────

/**
 * Create a new conversation, optionally linked to a solicitud.
 */
export async function crearConversacion(
  data: ConversacionCreate,
): Promise<ConversacionResponse["data"]> {
  const response = await api.post<ConversacionResponse>(
    "/conversaciones",
    data,
  );
  if (!response.data.success || !response.data.data) {
    throw new Error(
      response.data.error?.message ?? "Error creating conversation",
    );
  }
  return response.data.data;
}

/**
 * Post a new message to a conversation.
 * Supports file attachments via buildApiPayload tokenization in the hook layer.
 * The conversationId is part of the URL path.
 * Returns raw response.data — hook parses with schema.
 */
export async function crearMensaje(
  conversacionId: string,
  data: MensajeCreate,
): Promise<MensajeResponse> {
  const response = await api.post<MensajeResponse>(
    `/conversaciones/${conversacionId}/mensajes`,
    data,
  );
  return response.data;
}

/**
 * Soft-delete a message.
 */
export async function eliminarMensaje(mensajeId: string): Promise<void> {
  await api.delete(`/conversaciones/mensajes/${mensajeId}`);
}

/**
 * Close a conversation.
 */
export async function cerrarConversacion(
  conversacionId: string,
): Promise<void> {
  await api.post(`/conversaciones/${conversacionId}/cerrar`);
}
