import { useApiQuery, useGenericCreateMutation, usePagination } from "@/hooks";
import type {
  CreateTramiteData,
  ExpedienteCreateData,
  ExpedienteDetail,
  ExpedienteDetailResponse,
  ExpedienteItem,
  ExpedienteListResponse,
  SolicitudDetail,
  SolicitudDetailResponse,
  SolicitudItem,
  SolicitudListResponse,
} from "../schemas/tramite.schema";
import {
  ExpedienteDetailResponseSchema,
  ExpedienteListResponseSchema,
  SolicitudDetailResponseSchema,
  SolicitudListResponseSchema,
} from "../schemas/tramite.schema";
import type {
  SolicitudTrazabilidad,
  SolicitudTrazabilidadResponse,
} from "../schemas/trazabilidad.schema";
import { SolicitudTrazabilidadResponseSchema } from "../schemas/trazabilidad.schema";

// ── Solicitudes hooks (paginated) ──────────────────────────────────────────

/**
 * Hook to fetch paginated Solicitudes list.
 * Combines usePagination (page, pageSize) with useApiQuery.
 * Returns { items, total, totalPages } directly via select transform on the ApiResponse envelope.
 */
export function useSolicitudes(initialPage = 1) {
  const { page, pageSize, onPageChange, onPageSizeChange, paginationParams } =
    usePagination({ initialPage });

  const query = useApiQuery<
    SolicitudListResponse,
    { items: SolicitudItem[]; total: number; totalPages: number }
  >({
    queryKey: ["solicitudes"],
    url: "/solicitudes/",
    schema: SolicitudListResponseSchema,
    params: paginationParams,
    queryOptions: {
      select: (response) => {
        const data = response.data;
        return {
          items: data?.items ?? [],
          total: data?.total ?? 0,
          totalPages: data?.total_pages ?? 0,
        };
      },
    },
  });

  return {
    ...query,
    items: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    totalPages: query.data?.totalPages ?? 0,
    page,
    pageSize,
    onPageChange,
    onPageSizeChange,
  };
}

/**
 * Alias for useSolicitudes for TramiteList compatibility.
 */
export const useTramites = useSolicitudes;

/**
 * Hook to fetch a single Solicitud detail.
 */
export function useSolicitudDetail(id: string | null) {
  return useApiQuery<SolicitudDetailResponse, SolicitudDetail | null>({
    queryKey: ["solicitudes", "detail", id],
    url: id ? `/solicitudes/${id}` : null,
    schema: SolicitudDetailResponseSchema,
    queryOptions: {
      select: (response) => response.data,
    },
  });
}

/**
 * Alias for useSolicitudDetail for TramiteDetail compatibility.
 */
export const useTramite = useSolicitudDetail;

// ── Expedientes hooks (paginated) ──────────────────────────────────────────

/**
 * Hook to fetch paginated Expedientes list.
 * Combines usePagination (page, pageSize) with useApiQuery.
 * Returns { items, total, totalPages } directly via select transform on the ApiResponse envelope.
 */
export function useExpedientes(initialPage = 1) {
  const { page, pageSize, onPageChange, onPageSizeChange, paginationParams } =
    usePagination({ initialPage });

  const query = useApiQuery<
    ExpedienteListResponse,
    { items: ExpedienteItem[]; total: number; totalPages: number }
  >({
    queryKey: ["expedientes"],
    url: "/expedientes/",
    schema: ExpedienteListResponseSchema,
    params: paginationParams,
    queryOptions: {
      select: (response) => {
        const data = response.data;
        return {
          items: data?.items ?? [],
          total: data?.total ?? 0,
          totalPages: data?.total_pages ?? 0,
        };
      },
    },
  });

  return {
    ...query,
    items: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    totalPages: query.data?.totalPages ?? 0,
    page,
    pageSize,
    onPageChange,
    onPageSizeChange,
  };
}

/**
 * Hook to fetch a single Expediente detail.
 */
export function useExpedienteDetail(id: string | null) {
  return useApiQuery<ExpedienteDetailResponse, ExpedienteDetail | null>({
    queryKey: ["expedientes", "detail", id],
    url: id ? `/expedientes/${id}` : null,
    schema: ExpedienteDetailResponseSchema,
    queryOptions: {
      select: (response) => response.data,
    },
  });
}

// ── Solicitud trazabilidad ────────────────────────────────────────────────────

/**
 * Hook to fetch the complete operative traceability graph for a Solicitud.
 * Query is disabled when id is null — standard TanStack Query v5 pattern.
 * Exposes standard loading/error/refetch behavior via useApiQuery.
 */
export function useSolicitudTrazabilidad(id: string | null) {
  return useApiQuery<
    SolicitudTrazabilidadResponse,
    SolicitudTrazabilidad | null
  >({
    queryKey: ["solicitudes", "trazabilidad", id],
    url: id ? `/solicitudes/${id}/trazabilidad` : null,
    schema: SolicitudTrazabilidadResponseSchema,
    queryOptions: {
      select: (response) => response.data,
    },
  });
}

// ── Crear Tramite (hybrid multipart) ───────────────────────────────────────

/**
 * Hook to create a complete Tramite (Expediente + Solicitud + distribution).
 * Uses buildApiPayload internally for multipart/form-data with file tokenization.
 * On success, prepends the new Solicitud to the paginated list cache.
 */
export function useCrearTramite() {
  return useGenericCreateMutation<SolicitudDetail, CreateTramiteData>({
    queryKey: ["solicitudes"],
    url: "/solicitudes/crear-completo",
    listShape: "paginated",
    insertPosition: "start",
  });
}

// ── Crear Expediente ─────────────────────────────────────────────────────────

/**
 * Hook to create a standalone Expediente (without a Solicitud).
 * Uses buildApiPayload internally for multipart/form-data with file tokenization.
 * On success, prepends the new Expediente to the paginated list cache.
 */
export function useCrearExpediente() {
  return useGenericCreateMutation<ExpedienteDetail, ExpedienteCreateData>({
    queryKey: ["expedientes"],
    url: "/expedientes/crear",
    listShape: "paginated",
    insertPosition: "start",
  });
}
