// features/tramites/hooks/useFinalizarSolicitud.ts
// Hook para emitir una respuesta formal a una Solicitud.
// Endpoint: POST /api/solicitudes/{solicitud_id}/finalizar
// Usa useGenericCreateMutation con forceFormData=true (patrón dual payload).

import { useGenericCreateMutation } from "@/hooks";
import {
  type FinalizarSolicitudFormData,
  FinalizarSolicitudResponseSchema,
  type SolicitudRespuestaOut,
} from "../schemas/finalizar-solicitud.schema";

/**
 * Transforms UI form data to the backend-compatible payload.
 *
 * Files are transformed into the archivos_adjuntos structure expected by the backend.
 * buildApiPayload (called inside useGenericCreateMutation) tokenizes File objects
 * automatically.
 */
function toBackendPayload(data: FinalizarSolicitudFormData) {
  return {
    tipo_respuesta: data.tipo_respuesta,
    contenido: data.contenido,
    archivos: data.archivos.map((item) => ({
      nombre_original: item.file.name,
      mime_type: item.file.type || null,
      tamano_bytes: item.file.size,
      archivo: item.file,
    })),
  };
}

/**
 * Mutation hook for issuing a formal response to a Solicitud.
 *
 * Uses useGenericCreateMutation with:
 * - Dynamic URL via function: POST /solicitudes/{solicitudId}/finalizar
 * - mapVariables to transform UI vars to backend format before buildApiPayload
 * - forceFormData: true — backend always expects FormData with "data" field
 * - afterSuccess invalidates the solicitud detail query cache
 *
 * Architecture contract compliance:
 * - Uses generic create hook (not raw useMutation) ✓
 * - buildApiPayload called inside generic hook infrastructure ✓
 * - URL is dynamic via function ✓
 * - Variable transformation in mapVariables (domain shaping) ✓
 * - forceFormData: true for dual payload pattern ✓
 *
 * Note: TItem is unknown since the cache key is the full wrapper
 * (used only for invalidation via afterSuccess, not direct reads).
 */
export function useFinalizarSolicitud(solicitudId: string) {
  return useGenericCreateMutation<
    SolicitudRespuestaOut,
    FinalizarSolicitudFormData
  >({
    queryKey: ["solicitudes", "finalizar", solicitudId],
    url: (vars: FinalizarSolicitudFormData) =>
      `/solicitudes/${solicitudId}/finalizar`,
    schema: FinalizarSolicitudResponseSchema,
    mapVariables: (data: FinalizarSolicitudFormData) => toBackendPayload(data),
    forceFormData: true,
    afterSuccess: (queryClient) => {
      // Invalidate the solicitud detail cache so the page refreshes
      queryClient.invalidateQueries({
        queryKey: ["solicitudes", "detail", solicitudId],
      });
    },
  });
}
