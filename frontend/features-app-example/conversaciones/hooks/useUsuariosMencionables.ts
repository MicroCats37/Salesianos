// features/conversaciones/hooks/useUsuariosMencionables.ts
// Hook para obtener usuarios mencionables — non-paginated list.

import { useApiQuery } from "@/hooks";
import {
  type UsuarioMencionable,
  type UsuariosMencionablesResponse,
  UsuariosMencionablesResponseSchema,
} from "../schemas";

interface UseUsuariosMencionablesProps {
  solicitudId?: string | null;
  periodoId?: string | null;
  conversacionId?: string | null;
  areaId?: string | null;
  nombre?: string | null;
  enabled?: boolean;
}

/**
 * Hook to fetch mentionable users for a given context.
 *
 * A user is mentionable in solicitud context if they have an active
 * participation (fecha_fin IS NULL) in an open period (fecha_fin IS NULL)
 * of any area assigned to the solicitud.
 *
 * Enabled when at least one of: solicitud_id, conversacion_id, or area_id is provided.
 *
 * Usage:
 * ```tsx
 * const { usuarios, isLoading, isError, refetch } = useUsuariosMencionables({
 *   solicitudId: "uuid",
 *   nombre: "search",
 * });
 * ```
 */
export function useUsuariosMencionables({
  solicitudId,
  periodoId,
  conversacionId,
  areaId,
  nombre,
  enabled = true,
}: UseUsuariosMencionablesProps) {
  // Build params — only include non-null values
  const params: Record<string, string> = {};
  if (solicitudId) params.solicitud_id = solicitudId;
  if (periodoId) params.periodo_id = periodoId;
  if (conversacionId) params.conversacion_id = conversacionId;
  if (areaId) params.area_id = areaId;
  if (nombre) params.nombre = nombre;

  // Determine if the query should be enabled
  const isEnabled =
    enabled &&
    (!!solicitudId || !!conversacionId || !!areaId) &&
    Object.keys(params).length > 0;

  const query = useApiQuery<UsuariosMencionablesResponse, UsuarioMencionable[]>(
    {
      queryKey: ["usuarios-mencionables", params],
      url: "/usuarios/mencionables/",
      schema: UsuariosMencionablesResponseSchema,
      params: Object.keys(params).length > 0 ? params : undefined,
      queryOptions: {
        enabled: isEnabled,
        select: (response) => {
          return (response.data ?? []) as UsuarioMencionable[];
        },
      },
    },
  );

  return {
    usuarios: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    error: query.error,
  };
}
