import api from "@/lib/api";
import type {
  AsignacionResponse,
  BandejaResponse,
  CambiarParticipacionData,
  CreateAsignacionData,
  FinalizarPeriodoData,
  IncorporarAreaData,
  MarcarAsignacionErroneaData,
  UpdateAsignacionData,
} from "../schemas/asignacion.schema";

/**
 * Asignacion service - consumes Django REST API via Axios.
 */

// ── Legacy CRUD ──────────────────────────────────────────────────────────────

export async function getAsignaciones(): Promise<AsignacionResponse[]> {
  const response = await api.get<AsignacionResponse[]>("/asignaciones/");
  return response.data;
}

export async function getAsignacion(id: string): Promise<AsignacionResponse> {
  const response = await api.get<AsignacionResponse>(`/asignaciones/${id}/`);
  return response.data;
}

export async function createAsignacion(
  data: CreateAsignacionData,
): Promise<AsignacionResponse> {
  const response = await api.post<AsignacionResponse>("/asignaciones/", data);
  return response.data;
}

export async function updateAsignacion(
  id: string,
  data: UpdateAsignacionData,
): Promise<AsignacionResponse> {
  const response = await api.patch<AsignacionResponse>(
    `/asignaciones/${id}/`,
    data,
  );
  return response.data;
}

export async function deleteAsignacion(id: string): Promise<void> {
  await api.delete(`/asignaciones/${id}/`);
}

// ── Bandeja / Periodos ──────────────────────────────────────────────────────

export interface GetPeriodosBandejaParams {
  page?: number;
  page_size?: number;
  estado?: string;
  area_id?: string;
}

/**
 * Fetches the user's bandeja (inbox) of periods.
 * Returns paginated PeriodoItems grouped by area.
 */
export async function getPeriodosBandeja(
  params: GetPeriodosBandejaParams = {},
): Promise<BandejaResponse> {
  const response = await api.get<BandejaResponse>("/periodos/bandeja", {
    params,
  });
  return response.data;
}

/**
 * Takes a period (marks the user as participant).
 * POST /api/periodos/{id}/tomar
 */
export async function tomarPeriodo(id: string): Promise<unknown> {
  const response = await api.post<unknown>(`/periodos/${id}/tomar`);
  return response.data;
}

/**
 * Incorporates an area into a Solicitud.
 * POST /api/solicitudes/{solicitudId}/areas
 */
export async function incorporarArea(
  solicitudId: string,
  data: IncorporarAreaData,
): Promise<unknown> {
  const response = await api.post<unknown>(
    `/solicitudes/${solicitudId}/areas`,
    data,
  );
  return response.data;
}

// ── Periodo Operations ───────────────────────────────────────────────────────────

/**
 * Initiates period management.
 * POST /api/periodos/{id}/iniciar-gestion
 */
export async function iniciarGestionPeriodo(id: string): Promise<unknown> {
  const response = await api.post<unknown>(`/periodos/${id}/iniciar-gestion`);
  return response.data;
}

/**
 * Finalizes a period.
 * POST /api/periodos/{id}/finalizar
 */
export async function finalizarPeriodo(
  id: string,
  data: FinalizarPeriodoData,
): Promise<unknown> {
  const response = await api.post<unknown>(`/periodos/${id}/finalizar`, data);
  return response.data;
}

/**
 * Marks a period as erroneous.
 * POST /api/periodos/{id}/marcar-asignacion-erronea
 */
export async function marcarAsignacionErronea(
  id: string,
  data: MarcarAsignacionErroneaData,
): Promise<unknown> {
  const response = await api.post<unknown>(
    `/periodos/${id}/marcar-asignacion-erronea`,
    data,
  );
  return response.data;
}

/**
 * Changes period participation type.
 * POST /api/periodos/{id}/cambiar-participacion
 */
export async function cambiarParticipacionPeriodo(
  id: string,
  data: CambiarParticipacionData,
): Promise<unknown> {
  const response = await api.post<unknown>(
    `/periodos/${id}/cambiar-participacion`,
    data,
  );
  return response.data;
}
