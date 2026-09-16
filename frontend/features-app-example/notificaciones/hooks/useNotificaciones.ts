import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { z } from "zod";
import { useApiQuery, usePagination } from "@/hooks";
import {
  type DescartarNotificacionResponse,
  type EstadoNotificacionIndividual,
  type MarcarVistaResponse,
  type NotificacionListResponse,
  NotificacionListResponseSchema,
  type NotificationDetailData,
  NotificationDetailResponseSchema,
  NotificationDetalleResponseSchema,
  type NotificationListItem,
  type NotificationSolicitudDetailData,
} from "../schemas/notificacion.schema";
import {
  abrirNotificacion,
  descartarNotificacion,
  type GetNotificacionesParams,
  getNotificacionDetalle,
  getNotificacionSummary,
  marcarVista,
  type NotificacionSummary,
} from "../services/notificacion.service";

// ── Query Keys ─────────────────────────────────────────────────────────────────

const NOTIFICACIONES_QUERY_KEY = ["notificaciones"] as const;
const NOTIFICACIONES_LIST_KEY = (params: GetNotificacionesParams) =>
  ["notificaciones", "list", { ...params }] as const;
const NOTIFICACIONES_SUMMARY_KEY = ["notificaciones", "summary"] as const;
const NOTIFICACIONES_DETAIL_KEY = (id: string) =>
  ["notificaciones", "detail", id] as const;

// ── useNotificaciones ─────────────────────────────────────────────────────────

export interface UseNotificacionesOptions {
  /** Filter by individual status: NO_VISTA | VISTA | ABIERTA | DESCARTADA */
  estado?: EstadoNotificacionIndividual | string;
  /** Initial page number (default: 1). */
  initialPage?: number;
  /** Override the pagination page-size (defaults to user preference via usePagination). */
  pageSize?: number;
}

/**
 * Return type of useNotificaciones — exposed for callers who need the shape.
 */
export interface UseNotificacionesReturn {
  /** The notification items for the current page — minimal list shape from GET /api/notificaciones/. */
  items: NotificationListItem[];
  /** Total count of items matching the current filter (client-side). */
  total: number;
  /** Total pages based on pageSize. */
  totalPages: number;
  /** Current page number. */
  page: number;
  /** Current page size. */
  pageSize: number;
  /** Navigate to a different page. */
  onPageChange: (page: number) => void;
  /** Change page size and reset to page 1. */
  onPageSizeChange: (size: number) => void;
  /** Whether the query is currently loading. */
  isLoading: boolean;
  /** Whether the query encountered an error. */
  isError: boolean;
  /** The raw error if isError is true. */
  error: unknown;
  /** Refetch the notifications list. */
  refetch: () => void;
}

/**
 * Hook to fetch paginated notifications list.
 * Combines usePagination (page, pageSize) with useApiQuery.
 * Returns items + total + totalPages via select transform on the ApiResponse envelope.
 * Loading the list does NOT mark notifications as viewed.
 *
 * Supports two call styles for backward compatibility:
 * - useNotificaciones() or useNotificaciones(1)  → all notifications
 * - useNotificaciones({ estado: "NO_VISTA" })  → filtered list
 *
 * @param firstArg - Page number (backward compat) OR a full options object.
 */
export function useNotificaciones(
  firstArg?: number | UseNotificacionesOptions,
  _maybeOptions?: UseNotificacionesOptions,
): UseNotificacionesReturn {
  // Resolve options from either overload style.
  const isNumeric = typeof firstArg === "number";
  const options: UseNotificacionesOptions = isNumeric
    ? { initialPage: firstArg }
    : (firstArg ?? {});

  const { estado, initialPage = 1, pageSize } = options;
  const {
    page,
    pageSize: resolvedPageSize,
    onPageChange,
    onPageSizeChange,
    paginationParams,
  } = usePagination({ initialPage });

  const effectivePageSize = pageSize ?? resolvedPageSize;

  // Build query params — include estado when provided.
  const queryParams: GetNotificacionesParams = {
    ...paginationParams,
    ...(estado ? { estado } : {}),
  };

  const query = useApiQuery<
    NotificacionListResponse,
    { items: NotificationListItem[]; total: number; totalPages: number }
  >({
    queryKey: NOTIFICACIONES_LIST_KEY(queryParams),
    url: "/notificaciones",
    schema: NotificacionListResponseSchema,
    params: queryParams as Record<string, unknown>,
    queryOptions: {
      // Client-side filter when estado_individual is provided.
      // Backend `estado` param filters institutional status, not individual.
      select: (response) => {
        const data = response.data;
        const allItems: NotificationListItem[] = data?.items ?? [];

        const filteredItems: NotificationListItem[] = estado
          ? allItems.filter((item) => item.estado_individual === estado)
          : allItems;

        return {
          items: filteredItems,
          total: filteredItems.length,
          totalPages: Math.ceil(filteredItems.length / effectivePageSize) || 1,
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
    pageSize: effectivePageSize,
    onPageChange,
    onPageSizeChange,
  };
}

// ── useNotificacionSummary ────────────────────────────────────────────────────

/**
 * Hook to fetch notification summary counts (total + sin_leer).
 * Uses the `GET /notificaciones/resumen` endpoint.
 *
 * Graceful fallback: returns `null` when the endpoint is unavailable (404, 5xx,
 * network error). Callers must handle the null state and show an appropriate
 * placeholder rather than crashing.
 */
export function useNotificacionSummary() {
  return useQuery<NotificacionSummary | null, Error>({
    queryKey: NOTIFICACIONES_SUMMARY_KEY,
    queryFn: getNotificacionSummary,
    // No retry — a failure means the endpoint isn't ready yet, not a transient error.
    retry: false,
    // Stale time of 30 seconds — counts don't need to be real-time.
    staleTime: 30_000,
  });
}

// ── useNotificacionDetail ────────────────────────────────────────────────────

const NOTIFICACIONES_DETALLE_NEW_KEY = (id: string) =>
  ["notificaciones", "detalle", id] as const;

/**
 * Hook to fetch a single notification's full detail.
 * Used by the `/notificaciones/[id]` detail page.
 */
export function useNotificacionDetail(id: string) {
  return useApiQuery<
    z.infer<typeof NotificationDetailResponseSchema>,
    NotificationDetailData | null
  >({
    queryKey: NOTIFICACIONES_DETAIL_KEY(id),
    url: `/notificaciones/${id}`,
    schema: NotificationDetailResponseSchema,
    queryOptions: {
      enabled: Boolean(id),
      select: (response) => response.data,
    },
  });
}

/**
 * Hook to fetch a notification's detail from the new restructured endpoint.
 * Uses GET /notificaciones/{id}/detalle which returns nested expediente_publico
 * and periodo instead of flat fields.
 *
 * This is the hook for the new combined detail endpoint — use this for the
 * detail page while the old useNotificacionDetail (flat fields) is phased out.
 */
export function useNotificacionDetalle(id: string) {
  return useApiQuery<
    z.infer<typeof NotificationDetalleResponseSchema>,
    NotificationSolicitudDetailData | null
  >({
    queryKey: NOTIFICACIONES_DETALLE_NEW_KEY(id),
    url: `/notificaciones/${id}/detalle`,
    schema: NotificationDetalleResponseSchema,
    queryOptions: {
      enabled: Boolean(id),
      select: (response) => response.data,
    },
  });
}

// ── useMarkVista ──────────────────────────────────────────────────────────────

/**
 * Mutation hook to mark a notification as viewed (NO_VISTA → VISTA).
 * Should be called once when the notification is deliberately shown.
 * Invalidates the notificaciones list cache, summary cache,
 * AND detail cache on success.
 */
export function useMarkVista() {
  const queryClient = useQueryClient();

  return useMutation<MarcarVistaResponse, unknown, string>({
    mutationFn: (id: string) => marcarVista(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: NOTIFICACIONES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: NOTIFICACIONES_SUMMARY_KEY });
      queryClient.invalidateQueries({
        queryKey: NOTIFICACIONES_DETAIL_KEY(id),
      });
    },
  });
}

// ── useAbrirNotificacion ─────────────────────────────────────────────────────

/**
 * Mutation hook to mark a notification as opened.
 * Sets abierta_at; also sets vista_at if NULL (backend invariant).
 * Idempotent: calling again does not change timestamps.
 * Invalidates the notificaciones list cache, summary cache,
 * AND detail cache on success.
 */
export function useAbrirNotificacion() {
  const queryClient = useQueryClient();

  return useMutation<unknown, unknown, string>({
    mutationFn: (id: string) => abrirNotificacion(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: NOTIFICACIONES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: NOTIFICACIONES_SUMMARY_KEY });
      queryClient.invalidateQueries({
        queryKey: NOTIFICACIONES_DETAIL_KEY(id),
      });
    },
  });
}

// ── useDescartarNotificacion ─────────────────────────────────────────────────

/**
 * Mutation hook to discard a notification.
 * Only affects the current user's individual interaction record.
 * Invalidates the notificaciones list cache AND the summary on success.
 */
export function useDescartarNotificacion() {
  const queryClient = useQueryClient();

  return useMutation<DescartarNotificacionResponse, unknown, string>({
    mutationFn: (id: string) => descartarNotificacion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: NOTIFICACIONES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: NOTIFICACIONES_SUMMARY_KEY });
    },
  });
}

// ── Re-exports ────────────────────────────────────────────────────────────────

export type { GetNotificacionesParams, NotificacionSummary };
