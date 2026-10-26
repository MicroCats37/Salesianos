"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { getErrorMessage, notify } from "@/errors";
import {
  type PreregistrarEnPoolPayload,
  type PreregistrarEnPoolRespuesta,
  preregistrarEnPool,
} from "../services/pool.service";
import { inscripcionElegiblesPrefixKey } from "./useElegiblesEquipo";
import { inscripcionDetalleKey } from "./useInscripcionDetalle";
import { inscripcionPoolKey, inscripcionSaldoKey } from "./useInscripcionPool";

/**
 * Mutation hook for the pool preregistration.
 *
 * It calls `POST /inscripciones/{id}/personas` WITHOUT `equipo_id`, so the
 * backend creates only the `InscripcionPersona`: the person waits in the pool
 * until a paid cup is assigned to them.
 *
 * Capacity and deadline are backend rules — the frontend does not re-create
 * them, it only surfaces the backend message (`CUPO_CONTRATADO_EXCEDIDO`,
 * `FECHA_LIMITE_EXCEDIDA`, …) through the shared error parser.
 *
 * On success the four caches that depend on the pool are invalidated:
 * the pool itself, the inscription detail (roster counters), the cupo saldo
 * and the candidate lists of every team (a newly preregistered person must be
 * assignable right away — the selector reads its own endpoint).
 */
export function usePreregistrarEnPool(inscripcionId: string) {
  const queryClient = useQueryClient();
  const poolKey = inscripcionPoolKey(inscripcionId);
  const detalleKey = inscripcionDetalleKey(inscripcionId);
  const saldoKey = inscripcionSaldoKey(inscripcionId);
  const elegiblesKey = inscripcionElegiblesPrefixKey(inscripcionId);

  return useMutation<
    { data: PreregistrarEnPoolRespuesta; message?: string },
    Error,
    PreregistrarEnPoolPayload
  >({
    mutationFn: async (payload) => {
      const response = await preregistrarEnPool(inscripcionId, payload);
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ??
            "No se pudo registrar al participante en el pool",
        );
      }
      return { data: response.data, message: response.message };
    },
    onSuccess: ({ message }) => {
      if (message) notify.success(message);
      queryClient.invalidateQueries({ queryKey: poolKey });
      queryClient.invalidateQueries({ queryKey: detalleKey });
      queryClient.invalidateQueries({ queryKey: saldoKey });
      // The new candidate must be assignable right away: the selector reads
      // the team-scoped eligible endpoint, not the pool.
      queryClient.invalidateQueries({ queryKey: elegiblesKey });
    },
    onError: (error) => {
      // Backend rule violation (capacity, deadline, …) — show it verbatim.
      notify.error(getErrorMessage(error));
    },
  });
}
