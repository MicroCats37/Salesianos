// features/tramites/hooks/useTiposDocumento.ts
// Hook para obtener la lista de tipos de documento desde GET /api/tipos-documento

import { z } from "zod";
import { useApiQuery } from "@/hooks";

// ── Schema de respuesta API ───────────────────────────────────────────────────

export const TipoDocumentoSchema = z.object({
  id: z.string().uuid(),
  nombre: z.string(),
  descripcion: z.string(),
});

export const TiposDocumentoResponseSchema = z.object({
  success: z.boolean(),
  data: z.array(TipoDocumentoSchema).nullable(),
  error: z
    .object({
      code: z.string(),
      message: z.string(),
    })
    .nullable()
    .optional(),
});

export type TipoDocumento = z.infer<typeof TipoDocumentoSchema>;
export type TiposDocumentoResponse = z.infer<
  typeof TiposDocumentoResponseSchema
>;

// ── Hook ─────────────────────────────────────────────────────────────────────

/**
 * Hook to fetch the list of types of document.
 * Calls GET /api/tipos-documento with auth Bearer.
 * Returns { tiposDocumento, isLoading, isError, refetch }.
 *
 * Usage:
 * ```tsx
 * const { tiposDocumento, isLoading, isError, refetch } = useTiposDocumento();
 * ```
 */
export function useTiposDocumento() {
  const query = useApiQuery<TiposDocumentoResponse, TipoDocumento[]>({
    queryKey: ["tipos-documento"],
    url: "/tipos-documento/",
    schema: TiposDocumentoResponseSchema,
    queryOptions: {
      select: (response) => {
        // Return all tipos de documento (no activo filter like areas)
        return response.data ?? [];
      },
    },
  });

  return {
    tiposDocumento: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    error: query.error,
  };
}
