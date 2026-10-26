"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { getErrorMessage, notify } from "@/errors";
import type { ElegibleOut } from "../services/elegibles.service";
import type {
  EquipoDetalleOut,
  InscripcionDetalleOut,
  ParticipanteOut,
} from "../services/inscripcion.service";
import {
  type AsignarAEquipoRespuesta,
  asignarPoolAEquipo,
  type PoolOut,
} from "../services/pool.service";
import { inscripcionElegiblesPrefixKey } from "./useElegiblesEquipo";
import { inscripcionDetalleKey } from "./useInscripcionDetalle";
import { inscripcionPoolKey, inscripcionSaldoKey } from "./useInscripcionPool";

export interface AsignarParticipanteVariables {
  /** The candidate being assigned (`InscripcionPersona.id`). */
  inscripcionPersonaId: string;
  /** The candidate payload — used to build the optimistic roster row. */
  candidato: ElegibleOut;
  /** The target team. */
  equipo: EquipoDetalleOut;
  /** Role inside the team. Defaults to "J" (jugador), like the backend default. */
  rol?: string;
}

interface AsignarParticipanteContext {
  prevPool?: PoolOut;
  prevDetalle?: InscripcionDetalleOut;
}

/**
 * Temporary id for the optimistic roster row.
 *
 * The real `Participacion.id` only exists after the backend answers, so the
 * optimistic row uses a namespaced placeholder. Both queries are invalidated
 * on success, so the placeholder never survives the round trip.
 *
 * The team id IS part of the placeholder: one paid cup authorises the person
 * in EVERY contracted discipline, so the SAME person can be optimistically
 * added to two teams. Without the team id both rows would share a key and the
 * second one would collide with the first.
 */
function optimisticParticipanteId(
  equipoId: string,
  inscripcionPersonaId: string,
) {
  return `optimistic:${equipoId}:${inscripcionPersonaId}`;
}

function buildOptimisticParticipante(
  candidato: ElegibleOut,
  equipo: EquipoDetalleOut,
  eventoId: string,
  rol: string,
): ParticipanteOut {
  return {
    id: optimisticParticipanteId(equipo.id, candidato.id),
    inscripcion_persona_id: candidato.id,
    equipo_id: equipo.id,
    equipo_nombre: equipo.nombre,
    evento_id: eventoId,
    disciplina: equipo.disciplina,
    persona: {
      id: candidato.persona.id,
      nombre: candidato.persona.nombre,
      nombres: candidato.persona.nombres ?? "",
      apellidos: candidato.persona.apellidos ?? "",
      numero_documento: candidato.persona.numero_documento,
    },
    rol,
    talla_camiseta: null,
    notas: null,
    estado: "A",
    created_at: new Date().toISOString(),
  };
}

/**
 * Mutation hook for the atomic assignment of a participant to a team.
 *
 * It calls `POST /inscripciones/{id}/pool/asignar`, the endpoint that is the
 * sole authority for placing a participant in a team. It is reused as-is by the
 * selector modal — no new write endpoint, no changed contract.
 *
 * Cache strategy (optimistic with rollback):
 * 1. `onMutate` — snapshot both caches, then remove the person from the pool
 *    (if they were waiting there) and append them to the target roster.
 * 2. `onError` — restore the snapshots (instant rollback) and surface the
 *    backend error message.
 * 3. `onSuccess` — invalidate every query that depends on the roster so the
 *    canonical state (real `Participacion.id`, counters) replaces the
 *    optimistic shape.
 */
export function useAsignarParticipanteAEquipo(inscripcionId: string) {
  const queryClient = useQueryClient();
  const poolKey = inscripcionPoolKey(inscripcionId);
  const detalleKey = inscripcionDetalleKey(inscripcionId);
  const saldoKey = inscripcionSaldoKey(inscripcionId);
  // The PREFIX key: it matches the candidate list of EVERY team of the
  // inscription (the assignment changes the eligibility of the other
  // disciplines too).
  const elegiblesKey = inscripcionElegiblesPrefixKey(inscripcionId);

  return useMutation<
    { data: AsignarAEquipoRespuesta; message?: string },
    Error,
    AsignarParticipanteVariables,
    AsignarParticipanteContext
  >({
    mutationFn: async ({ candidato, equipo, rol }) => {
      const response = await asignarPoolAEquipo(inscripcionId, {
        inscripcion_persona_id: candidato.id,
        equipo_id: equipo.id,
        rol: rol ?? "J",
      });
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ??
            "No se pudo asignar el participante al equipo",
        );
      }
      return { data: response.data, message: response.message };
    },
    onMutate: async ({ candidato, equipo, rol }) => {
      await queryClient.cancelQueries({ queryKey: poolKey });
      await queryClient.cancelQueries({ queryKey: detalleKey });

      const prevPool = queryClient.getQueryData<PoolOut>(poolKey);
      const prevDetalle =
        queryClient.getQueryData<InscripcionDetalleOut>(detalleKey);

      // Optimistic: the person leaves the pool (only when they were in it).
      queryClient.setQueryData<PoolOut>(poolKey, (old) =>
        old
          ? { ...old, pool: old.pool.filter((e) => e.id !== candidato.id) }
          : old,
      );

      // Optimistic: the person joins the target roster.
      queryClient.setQueryData<InscripcionDetalleOut>(detalleKey, (old) => {
        if (!old) return old;
        return {
          ...old,
          equipos: old.equipos.map((e) =>
            e.id === equipo.id
              ? {
                  ...e,
                  participantes: [
                    ...e.participantes,
                    buildOptimisticParticipante(
                      candidato,
                      e,
                      old.evento_id,
                      rol ?? "J",
                    ),
                  ],
                }
              : e,
          ),
        };
      });

      return { prevPool, prevDetalle };
    },
    onError: (error, _variables, context) => {
      // Rollback: restore the exact state the UI had before the gesture.
      if (context?.prevPool) {
        queryClient.setQueryData<PoolOut>(poolKey, context.prevPool);
      }
      if (context?.prevDetalle) {
        queryClient.setQueryData<InscripcionDetalleOut>(
          detalleKey,
          context.prevDetalle,
        );
      }
      notify.error(getErrorMessage(error));
      // Resync with the server (the rollback above is only the first step).
      queryClient.invalidateQueries({ queryKey: poolKey });
      queryClient.invalidateQueries({ queryKey: detalleKey });
      queryClient.invalidateQueries({ queryKey: elegiblesKey });
    },
    onSuccess: ({ message }) => {
      if (message) notify.success(message);
      queryClient.invalidateQueries({ queryKey: poolKey });
      queryClient.invalidateQueries({ queryKey: detalleKey });
      queryClient.invalidateQueries({ queryKey: saldoKey });
      // The assignment changes the eligibility of EVERY team of the
      // inscription (the person may now play in more disciplines).
      queryClient.invalidateQueries({ queryKey: elegiblesKey });
    },
  });
}
