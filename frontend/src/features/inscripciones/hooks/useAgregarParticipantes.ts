"use client";

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import type {
  AgregarParticipantesPayload,
  AgregarParticipantesRespuesta,
} from "../services/inscripcion.service";
import { agregarParticipantesAEquipo } from "../services/inscripcion.service";
import { useInscripcionCacheSync } from "./useInscripcionCacheSync";

/**
 * Mutation hook for adding participants to an existing equipo.
 *
 * Cache strategy:
 * - Backend returns `{ participantes: ParticipanteOut[] }` — the canonical
 *   shape from the detail presenter (incl. `persona`, `acepto_*`, `notas`).
 *   The human-readable message lives at the top-level `message` of the
 *   envelope.
 * - We append each created participante to the `inscripcion-detalle` cache
 *   in place. No refetch. The `equipos[].participantes[]` array stays
 *   homogeneous because we use the SAME presenter that builds the detail.
 *
 * Success toast reads `response.message` from the envelope (server-controlled).
 */
export function useAgregarParticipantes(
  inscripcionId: string,
  _equipoId: string,
) {
  const cache = useInscripcionCacheSync(inscripcionId);

  return useMutation<
    { data: AgregarParticipantesRespuesta; message?: string },
    Error,
    AgregarParticipantesPayload
  >({
    mutationFn: async (payload) => {
      const response = await agregarParticipantesAEquipo(
        inscripcionId,
        // equipoId is read from the current cache for each participante to keep
        // the payload's equipoId as the single source of truth, but the
        // endpoint already receives it via the URL — pass through for type
        // safety.
        _equipoId,
        payload,
      );
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ?? "Error al agregar participante(s)",
        );
      }
      return { data: response.data, message: response.message };
    },
    onSuccess: ({ data, message }) => {
      // Optimistic append: each returned participante goes into its equipo.
      for (const participante of data.participantes) {
        cache.addParticipante(participante.equipo_id, participante);
      }
      if (message) toast.success(message);
    },
    onError: (error) => {
      // Rollback: backend rejected — invalidate to refetch correct state.
      cache.invalidate();
      toast.error(
        error instanceof Error
          ? error.message
          : "Error al agregar participante(s)",
      );
    },
  });
}
