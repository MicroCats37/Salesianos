"use client";

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { eliminarParticipante } from "../services/inscripcion.service";
import { useInscripcionCacheSync } from "./useInscripcionCacheSync";

/**
 * Mutation hook for removing a participant from an existing equipo.
 *
 * Cache strategy:
 * 1. Optimistic remove from the local `inscripcion-detalle` cache (instant UI).
 * 2. On error → invalidate to rollback to backend truth.
 * 3. On success → no refetch needed (cache is already up to date).
 *
 * Success toast reads `response.message` from the envelope (server-controlled).
 */
export function useEliminarParticipante(
  inscripcionId: string,
  participanteId: string,
) {
  const cache = useInscripcionCacheSync(inscripcionId);

  return useMutation<
    { data: { participante_id: string }; message?: string },
    Error,
    void
  >({
    mutationFn: async () => {
      const response = await eliminarParticipante(
        inscripcionId,
        participanteId,
      );
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ?? "Error al eliminar participante",
        );
      }
      return { data: response.data, message: response.message };
    },
    onSuccess: ({ message }) => {
      cache.removeParticipante(participanteId);
      if (message) toast.success(message);
    },
    onError: (error) => {
      // Backend might have a stricter view; resync cache to be safe.
      cache.invalidate();
      toast.error(
        error instanceof Error
          ? error.message
          : "Error al eliminar participante",
      );
    },
  });
}
