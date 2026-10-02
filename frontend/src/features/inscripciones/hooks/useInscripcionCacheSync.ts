"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import type {
  InscripcionDetalleOut,
  ParticipanteOut,
} from "../services/inscripcion.service";
import { inscripcionDetalleKey } from "./useInscripcionDetalle";

/**
 * Pure helpers for in-place cache updates of an `InscripcionDetalleOut`.
 *
 * All operations are shape-preserving (same field names, same types) so the
 * cache stays compatible with the backend presenter output. This is what the
 * user calls "homogeneidad": the optimistic update looks the same as what
 * the backend would return on a refetch, so the UI never desincroniza.
 *
 * Functions return a NEW `InscripcionDetalleOut` (immutable updates). They
 * return `null` if the mutation can't be applied (e.g. equipo not found)
 * so callers can fall back to `invalidateQueries`.
 */
export const inscripcionCacheHelpers = {
  /**
   * Append one participante to a given equipo. If `participante.id` already
   * exists in any equipo, the function returns the data unchanged
   * (no duplicates, idempotent).
   */
  addParticipante(
    data: InscripcionDetalleOut | undefined,
    equipoId: string,
    participante: ParticipanteOut,
  ): InscripcionDetalleOut | null {
    if (!data) return null;
    if (
      data.equipos.some((e) =>
        e.participantes.some((p) => p.id === participante.id),
      )
    ) {
      return data;
    }
    return {
      ...data,
      equipos: data.equipos.map((e) =>
        e.id === equipoId
          ? { ...e, participantes: [...e.participantes, participante] }
          : e,
      ),
    };
  },

  /**
   * Remove a participante by id from whichever equipo it's currently in.
   */
  removeParticipante(
    data: InscripcionDetalleOut | undefined,
    participanteId: string,
  ): InscripcionDetalleOut | null {
    if (!data) return null;
    const equipos = data.equipos.map((e) =>
      e.participantes.some((p) => p.id === participanteId)
        ? {
            ...e,
            participantes: e.participantes.filter(
              (p) => p.id !== participanteId,
            ),
          }
        : e,
    );
    // If no equipo had the participante, return original data unchanged.
    const changed = equipos.some(
      (e, i) => e.participantes.length !== data.equipos[i].participantes.length,
    );
    return changed ? { ...data, equipos } : data;
  },

  /**
   * Replace a participante in place (preserves array order).
   */
  updateParticipante(
    data: InscripcionDetalleOut | undefined,
    participante: ParticipanteOut,
  ): InscripcionDetalleOut | null {
    if (!data) return null;
    return {
      ...data,
      equipos: data.equipos.map((e) => ({
        ...e,
        participantes: e.participantes.map((p) =>
          p.id === participante.id ? participante : p,
        ),
      })),
    };
  },

  /**
   * Move a participante from its current equipo to another.
   * No-op if source or target equipo is missing.
   */
  moveParticipante(
    data: InscripcionDetalleOut | undefined,
    participanteId: string,
    targetEquipoId: string,
    movedParticipante?: ParticipanteOut,
  ): InscripcionDetalleOut | null {
    if (!data) return null;
    const sourceEquipo = data.equipos.find((e) =>
      e.participantes.some((p) => p.id === participanteId),
    );
    if (!sourceEquipo) return data;
    const targetEquipo = data.equipos.find((e) => e.id === targetEquipoId);
    if (!targetEquipo) return data;
    if (sourceEquipo.id === targetEquipo.id) return data;

    const original = sourceEquipo.participantes.find(
      (p) => p.id === participanteId,
    );
    const participanteFinal: ParticipanteOut = movedParticipante ?? {
      ...(original as ParticipanteOut),
      equipo_id: targetEquipoId,
    };

    return {
      ...data,
      equipos: data.equipos.map((e) => {
        if (e.id === sourceEquipo.id) {
          return {
            ...e,
            participantes: e.participantes.filter(
              (p) => p.id !== participanteId,
            ),
          };
        }
        if (e.id === targetEquipo.id) {
          if (e.participantes.some((p) => p.id === participanteFinal.id)) {
            return e;
          }
          return {
            ...e,
            participantes: [...e.participantes, participanteFinal],
          };
        }
        return e;
      }),
    };
  },
};

/**
 * Hook that exposes cache-sync callbacks scoped to one inscripcion.
 *
 * All mutations in this module accept the SAME helpers so the optimistic
 * updates preserve the original `InscripcionDetalleOut` shape (homogeneidad).
 */
export function useInscripcionCacheSync(inscripcionId: string) {
  const queryClient = useQueryClient();
  const key = inscripcionDetalleKey(inscripcionId);

  const read = useCallback(
    () => queryClient.getQueryData<InscripcionDetalleOut>(key),
    [queryClient, key],
  );

  const write = useCallback(
    (updater: InscripcionDetalleOut) => {
      queryClient.setQueryData<InscripcionDetalleOut>(key, updater);
    },
    [queryClient, key],
  );

  const addParticipante = useCallback(
    (equipoId: string, participante: ParticipanteOut) => {
      const current = read();
      const next = inscripcionCacheHelpers.addParticipante(
        current,
        equipoId,
        participante,
      );
      if (next && next !== current) write(next);
    },
    [read, write],
  );

  const removeParticipante = useCallback(
    (participanteId: string) => {
      const current = read();
      const next = inscripcionCacheHelpers.removeParticipante(
        current,
        participanteId,
      );
      if (next && next !== current) write(next);
    },
    [read, write],
  );

  const updateParticipante = useCallback(
    (participante: ParticipanteOut) => {
      const current = read();
      const next = inscripcionCacheHelpers.updateParticipante(
        current,
        participante,
      );
      if (next && next !== current) write(next);
    },
    [read, write],
  );

  const moveParticipante = useCallback(
    (
      participanteId: string,
      targetEquipoId: string,
      moved?: ParticipanteOut,
    ) => {
      const current = read();
      const next = inscripcionCacheHelpers.moveParticipante(
        current,
        participanteId,
        targetEquipoId,
        moved,
      );
      if (next && next !== current) write(next);
    },
    [read, write],
  );

  const invalidate = useCallback(
    () => queryClient.invalidateQueries({ queryKey: key }),
    [queryClient, key],
  );

  return {
    read,
    addParticipante,
    removeParticipante,
    updateParticipante,
    moveParticipante,
    invalidate,
  };
}
