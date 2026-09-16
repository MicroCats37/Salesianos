import api from "@/lib/api";
import { buildApiPayload } from "@/utils";
import type {
  CreateTramiteData,
  ExpedienteDetail,
  ExpedienteDetailResponse,
  ExpedienteListResponse,
  SolicitudDetail,
  SolicitudDetailResponse,
  SolicitudListResponse,
} from "../schemas/tramite.schema";
import type {
  SolicitudTrazabilidad,
  SolicitudTrazabilidadResponse,
} from "../schemas/trazabilidad.schema";

/**
 * Tramite service - consumes Django REST API via Axios.
 * Follows naming convention: {action}{Resource}() → camelCase
 */

// ── Solicitudes (paginated) ──────────────────────────────────────────────────

export interface GetSolicitudesParams {
  page?: number;
  page_size?: number;
  estado?: string;
  prioridad?: string;
}

export async function getSolicitudes(
  params: GetSolicitudesParams = {},
): Promise<SolicitudListResponse> {
  const response = await api.get<SolicitudListResponse>("/solicitudes/", {
    params,
  });
  return response.data;
}

export async function getSolicitudDetail(id: string): Promise<SolicitudDetail> {
  const response = await api.get<SolicitudDetailResponse>(`/solicitudes/${id}`);
  if (!response.data.data) {
    throw new Error(response.data.error?.message ?? "Solicitud no encontrada");
  }
  return response.data.data;
}

// ── Expedientes (paginated) ─────────────────────────────────────────────────

export interface GetExpedientesParams {
  page?: number;
  page_size?: number;
  busqueda?: string;
}

export async function getExpedientes(
  params: GetExpedientesParams = {},
): Promise<ExpedienteListResponse> {
  const response = await api.get<ExpedienteListResponse>("/expedientes/", {
    params,
  });
  return response.data;
}

export async function getExpedienteDetail(
  id: string,
): Promise<ExpedienteDetail> {
  const response = await api.get<ExpedienteDetailResponse>(
    `/expedientes/${id}`,
  );
  if (!response.data.data) {
    throw new Error(response.data.error?.message ?? "Expediente no encontrado");
  }
  return response.data.data;
}

// ── Solicitud trazabilidad ────────────────────────────────────────────────────

/**
 * Fetches the complete operative traceability graph for a Solicitud.
 * Returns: nested hierarchy (areas → etapas → participants/responses/history)
 * plus a derived chronological timeline.
 */
export async function getSolicitudTrazabilidad(
  id: string,
): Promise<SolicitudTrazabilidad> {
  const response = await api.get<SolicitudTrazabilidadResponse>(
    `/solicitudes/${id}/trazabilidad`,
  );
  if (response.data.data === null) {
    throw new Error(
      response.data.error?.message ?? "Trazabilidad no encontrada",
    );
  }
  return response.data.data;
}

// ── Hybrid create (multipart/form-data for files) ───────────────────────────

/**
 * Creates a complete Tramite (Expediente + Solicitud + distribucion) via
 * multipart/form-data. Uses buildApiPayload to tokenize File objects and
 * send them alongside the JSON-encoded data payload.
 */
export async function crearTramiteCompleto(
  data: CreateTramiteData,
): Promise<SolicitudDetail> {
  const payload = buildApiPayload(data);
  const response = await api.post<SolicitudDetail>(
    "/solicitudes/crear-completo",
    payload,
  );
  return response.data;
}
