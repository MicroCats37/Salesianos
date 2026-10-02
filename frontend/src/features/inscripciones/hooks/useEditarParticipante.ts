"use client";

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import type {
  EditarParticipantePayload,
  ParticipanteOut,
} from "../services/inscripcion.service";
import { editarParticipante } from "../services/inscripcion.service";
import { useInscripcionCacheSync } from "./useInscripcionCacheSync";

/**
 * Mutation hook for editing a participant (rol, talle, aseguradora, notas).
 *
 * Cache strategy:
 * 1. Optimistic update using the `ParticipanteOut` returned by the backend.
 *    UI updates instantly without a refetch.
 * 2. On error → invalidate to resync with backend truth.
 *
 * Success toast reads `response.message` from the envelope (server-controlled).
 */
export function useEditarParticipante(
  inscripcionId: string,
  participanteId: string,
) {
  const cache = useInscripcionCacheSync(inscripcionId);

  return useMutation<
    { data: ParticipanteOut; message?: string },
    Error,
    EditarParticipantePayload
  >({
    mutationFn: async (payload) => {
      const response = await editarParticipante(
        inscripcionId,
        participanteId,
        payload,
      );
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ?? "Error al editar participante",
        );
      }
      return { data: response.data, message: response.message };
    },
    onSuccess: ({ data, message }) => {
      cache.updateParticipante(data);
      if (message) toast.success(message);
    },
    onError: (error) => {
      cache.invalidate();
      toast.error(
        error instanceof Error ? error.message : "Error al editar participante",
      );
    },
  });
}
