// features/tramites/hooks/useAreas.ts
// Hook para obtener la lista de áreas institucionales activas desde GET /api/areas

import { z } from "zod";
import { useApiQuery } from "@/hooks";

// ── Schema de respuesta API ───────────────────────────────────────────────────

export const AreaSchema = z.object({
  id: z.string().uuid(),
  nombre: z.string(),
  descripcion: z.string().nullable(),
  activo: z.boolean(),
});

export const AreasResponseSchema = z.object({
  success: z.boolean(),
  data: z.array(AreaSchema).nullable(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .nullable()
    .optional(),
});

export type Area = z.infer<typeof AreaSchema>;
export type AreasResponse = z.infer<typeof AreasResponseSchema>;

// ── Hook ───────────────────────────────────────────────────────────────────────

/**
 * Hook to fetch the list of active institutional areas.
 * Calls GET /api/areas with auth Bearer.
 * Returns { areas, isLoading, isError, refetch }.
 *
 * Usage:
 * ```tsx
 * const { areas, isLoading, isError, refetch } = useAreas();
 * ```
 */
export function useAreas() {
  const query = useApiQuery<AreasResponse, Area[]>({
    queryKey: ["areas"],
    url: "/areas/",
    schema: AreasResponseSchema,
    queryOptions: {
      select: (response) => {
        // Filter only active areas and return the array directly
        return (response.data ?? []).filter((area) => area.activo === true);
      },
    },
  });

  return {
    areas: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    error: query.error,
  };
}
