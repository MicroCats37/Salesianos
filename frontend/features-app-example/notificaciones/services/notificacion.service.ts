import api from "@/lib/api";
import type {
  DescartarNotificacionResponse,
  MarcarVistaResponse,
  NotificationDetalleResponse,
} from "../schemas/notificacion.schema";

// ── Notificaciones Service ─────────────────────────────────────────────────────

/**
 * Notificaciones service — consumes Django REST API via Axios.
 * Follows naming convention: {action}{Resource}() → camelCase
 */

export interface GetNotificacionesParams {
  page?: number;
  page_size?: number;
  /** Filter by status: NO_VISTA | VISTA | ABIERTA | DESCARTADA */
  estado?: string;
}

/**
 * Mark a notification as viewed (NO_VISTA → VISTA).
 * Should be called once when the notification is deliberately shown.
 * Idempotent: calling again does not change the timestamp.
 */
export async function marcarVista(id: string): Promise<MarcarVistaResponse> {
  const response = await api.post<MarcarVistaResponse>(
    `/notificaciones/${id}/vista`,
  );
  return response.data;
}

/**
 * Discard a notification (removes it from the user's active view).
 * Only affects the current user's individual interaction record.
 */
export async function descartarNotificacion(
  id: string,
): Promise<DescartarNotificacionResponse> {
  const response = await api.post<DescartarNotificacionResponse>(
    `/notificaciones/${id}/descartar`,
  );
  return response.data;
}

/**
 * Mark a notification as opened.
 * Sets abierta_at; also sets vista_at if NULL (backend invariant).
 * Idempotent: calling again does not change timestamps.
 */
export async function abrirNotificacion(id: string): Promise<unknown> {
  const response = await api.post(`/notificaciones/${id}/abrir`);
  return response.data;
}

/**
 * Counts of unread and total notifications for the current user.
 * Used to populate the notifications badge in the topbar.
 *
 * Backend contract: GET /notificaciones/resumen
 * Response: { success: true, data: { total: number, sin_leer: number } }
 *
 * Graceful fallback: if the endpoint is not yet implemented on the backend,
 * returns null so callers can skip badge updates without crashing.
 */
export interface NotificacionSummary {
  total: number;
  sin_leer: number;
}

export async function getNotificacionSummary(): Promise<NotificacionSummary | null> {
  try {
    const response = await api.get<{
      success: boolean;
      data: NotificacionSummary;
    }>("/notificaciones/resumen");
    return response.data.data ?? null;
  } catch {
    // Endpoint not yet implemented — return null so callers degrade gracefully.
    return null;
  }
}

/**
 * Fetch the full detail of a notification from the new restructured endpoint.
 * Uses GET /notificaciones/{id}/detalle which returns nested expediente_publico
 * and periodo instead of flat fields.
 */
export async function getNotificacionDetalle(
  id: string,
): Promise<NotificationDetalleResponse> {
  const response = await api.get<NotificationDetalleResponse>(
    `/notificaciones/${id}/detalle`,
  );
  return response.data;
}
