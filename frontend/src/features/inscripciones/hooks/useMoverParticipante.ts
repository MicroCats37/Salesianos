"use client";

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import type {
  MoverParticipantePayload,
  ParticipanteOut,
} from "../services/inscripcion.service";
import { moverParticipante } from "../services/inscripcion.service";
import { useInscripcionCacheSync } from "./useInscripcionCacheSync";

/**
 * Mutation hook for moving a participant to another equipo (same inscription).
 *
 * Cache strategy:
 * 1. Optimistic move using the `ParticipanteOut` returned by the backend
 *    (which contains the new `equipo_id`).
 * 2. On error → invalidate to resync.
 *
 * Success toast reads `response.message` from the envelope (server-controlled).
 */
export function useMoverParticipante(
  inscripcionId: string,
  participanteId: string,
) {
  const cache = useInscripcionCacheSync(inscripcionId);

  return useMutation<
    { data: ParticipanteOut; message?: string },
    Error,
    MoverParticipantePayload
  >({
    mutationFn: async (payload) => {
      const response = await moverParticipante(
        inscripcionId,
        participanteId,
        payload,
      );
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Error al mover jugador");
      }
      return { data: response.data, message: response.message };
    },
    onSuccess: ({ data, message }) => {
      cache.moveParticipante(participanteId, data.equipo_id, data);
      if (message) toast.success(message);
    },
    onError: (error) => {
      cache.invalidate();
      toast.error(
        error instanceof Error ? error.message : "Error al mover jugador",
      );
    },
  });
}
