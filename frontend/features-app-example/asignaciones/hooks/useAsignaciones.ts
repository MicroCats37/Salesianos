import {
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useApiQuery } from "@/hooks/callsApi/useApiQuery";
import { usePagination } from "@/hooks/system/usePagination";
import type {
  BandejaResponse,
  CambiarParticipacionData,
  CreateAsignacionData,
  FinalizarPeriodoData,
  IncorporarAreaData,
  MarcarAsignacionErroneaData,
  PeriodoItem,
  UpdateAsignacionData,
} from "../schemas/asignacion.schema";
import { BandejaResponseSchema } from "../schemas/asignacion.schema";
import {
  cambiarParticipacionPeriodo,
  createAsignacion,
  deleteAsignacion,
  finalizarPeriodo,
  getAsignacion,
  getAsignaciones,
  getPeriodosBandeja,
  incorporarArea,
  iniciarGestionPeriodo,
  marcarAsignacionErronea,
  tomarPeriodo,
  updateAsignacion,
} from "../services/asignacion.service";

// ── Legacy Query Options ────────────────────────────────────────────────────

/**
 * Query options for asignaciones list.
 */
export const asignacionesQueryOptions = queryOptions({
  queryKey: ["asignaciones"],
  queryFn: getAsignaciones,
  staleTime: 5 * 60 * 1000,
});

export const asignacionQueryOptions = (id: string) =>
  queryOptions({
    queryKey: ["asignaciones", id],
    queryFn: () => getAsignacion(id),
    staleTime: 5 * 60 * 1000,
  });

/**
 * Hook to fetch asignaciones list.
 */
export function useAsignaciones() {
  return useQuery(asignacionesQueryOptions);
}

export function useAsignacion(id: string) {
  return useQuery(asignacionQueryOptions(id));
}

export function useCreateAsignacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAsignacionData) => createAsignacion(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["asignaciones"] });
    },
  });
}

export function useUpdateAsignacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateAsignacionData }) =>
      updateAsignacion(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["asignaciones"] });
      queryClient.invalidateQueries({
        queryKey: ["asignaciones", variables.id],
      });
    },
  });
}

export function useDeleteAsignacion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteAsignacion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["asignaciones"] });
    },
  });
}

// ── Bandeja / Periodos Hooks ───────────────────────────────────────────────

export interface UsePeriodosBandejaOptions {
  estado?: string;
  area_id?: string;
  enabled?: boolean;
}

/**
 * Hook to fetch the user's bandeja of periods with pagination.
 * Combines useApiQuery + usePagination.
 * Returns items + total + totalPages via select transform.
 */
export function usePeriodosBandeja(options: UsePeriodosBandejaOptions = {}) {
  const { estado, area_id, enabled = true } = options;
  const { page, pageSize, onPageChange, paginationParams } = usePagination();

  const query = useApiQuery<
    BandejaResponse,
    { items: PeriodoItem[]; total: number; totalPages: number }
  >({
    queryKey: ["periodos", "bandeja", { estado, area_id }],
    url: "/periodos/bandeja",
    schema: BandejaResponseSchema,
    params: {
      ...paginationParams,
      ...(estado ? { estado } : {}),
      ...(area_id ? { area_id } : {}),
    },
    queryOptions: {
      enabled,
      staleTime: 30 * 1000, // 30 seconds — bandeja changes frequently
      select: (response) => {
        const data = response.data;
        if (!data) {
          return { items: [] as PeriodoItem[], total: 0, totalPages: 0 };
        }
        return {
          items: data.items,
          total: data.total,
          totalPages: data.total_pages,
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
  };
}

/**
 * Mutation hook for taking a period (becoming a participant).
 * POST /api/periodos/{id}/tomar
 */
export function useTomarPeriodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (periodoId: string) => tomarPeriodo(periodoId),
    onSuccess: () => {
      // Invalidate bandeja and related queries
      queryClient.invalidateQueries({ queryKey: ["periodos", "bandeja"] });
      queryClient.invalidateQueries({ queryKey: ["solicitudes"] });
    },
  });
}

/**
 * Mutation hook for taking a period from within a Solicitud detail page.
 * Extends useTomarPeriodo with Solicitud detail cache invalidation.
 * POST /api/periodos/{periodoId}/tomar
 *
 * @param solicitudId - The parent Solicitud ID, used to invalidate the detail cache.
 */
export function useTomarPeriodoSolicitud(solicitudId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (periodoId: string) => tomarPeriodo(periodoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["periodos", "bandeja"] });
      queryClient.invalidateQueries({ queryKey: ["solicitudes"] });
      // Invalidate the solicitud detail so the period card refreshes
      queryClient.invalidateQueries({
        queryKey: ["solicitudes", "detail", solicitudId],
      });
    },
  });
}

/**
 * Mutation hook for incorporating an area into a Solicitud.
 * POST /api/solicitudes/{solicitudId}/areas
 *
 * @param solicitudId - The Solicitud ID to add the area to.
 */
export function useIncorporarArea(solicitudId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: IncorporarAreaData) => incorporarArea(solicitudId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["solicitudes"] });
      queryClient.invalidateQueries({
        queryKey: ["solicitudes", "detail", solicitudId],
      });
    },
  });
}

// ── Periodo Operation Hooks ────────────────────────────────────────────────────

/**
 * Mutation hook for initiating period management.
 * POST /api/periodos/{periodoId}/iniciar-gestion
 *
 * @param solicitudId - The parent Solicitud ID, used to invalidate the detail cache.
 */
export function useIniciarGestionPeriodo(solicitudId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (periodoId: string) => iniciarGestionPeriodo(periodoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["periodos", "bandeja"] });
      queryClient.invalidateQueries({ queryKey: ["solicitudes"] });
      queryClient.invalidateQueries({
        queryKey: ["solicitudes", "detail", solicitudId],
      });
    },
  });
}

/**
 * Mutation hook for finalizing a period.
 * POST /api/periodos/{periodoId}/finalizar
 *
 * @param solicitudId - The parent Solicitud ID, used to invalidate the detail cache.
 */
export function useFinalizarPeriodo(solicitudId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      periodoId,
      data,
    }: {
      periodoId: string;
      data: FinalizarPeriodoData;
    }) => finalizarPeriodo(periodoId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["periodos", "bandeja"] });
      queryClient.invalidateQueries({ queryKey: ["solicitudes"] });
      queryClient.invalidateQueries({
        queryKey: ["solicitudes", "detail", solicitudId],
      });
    },
  });
}

/**
 * Mutation hook for marking a period as erroneous.
 * POST /api/periodos/{periodoId}/marcar-asignacion-erronea
 *
 * @param solicitudId - The parent Solicitud ID, used to invalidate the detail cache.
 */
export function useMarcarAsignacionErronea(solicitudId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      periodoId,
      data,
    }: {
      periodoId: string;
      data: MarcarAsignacionErroneaData;
    }) => marcarAsignacionErronea(periodoId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["periodos", "bandeja"] });
      queryClient.invalidateQueries({ queryKey: ["solicitudes"] });
      queryClient.invalidateQueries({
        queryKey: ["solicitudes", "detail", solicitudId],
      });
    },
  });
}

/**
 * Mutation hook for changing period participation type.
 * POST /api/periodos/{periodoId}/cambiar-participacion
 *
 * @param solicitudId - The parent Solicitud ID, used to invalidate the detail cache.
 */
export function useCambiarParticipacionPeriodo(solicitudId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      periodoId,
      data,
    }: {
      periodoId: string;
      data: CambiarParticipacionData;
    }) => cambiarParticipacionPeriodo(periodoId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["periodos", "bandeja"] });
      queryClient.invalidateQueries({ queryKey: ["solicitudes"] });
      queryClient.invalidateQueries({
        queryKey: ["solicitudes", "detail", solicitudId],
      });
    },
  });
}
