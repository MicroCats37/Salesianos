"use client";

import {
  type UseQueryResult,
  useQueries,
  useQuery,
} from "@tanstack/react-query";
import {
  type ElegiblesEquipoOut,
  getElegiblesEquipo,
} from "../services/elegibles.service";

/**
 * Prefix key of the candidate lists of an inscripcion.
 *
 * It matches EVERY team of the inscription, which is what an assignment must
 * invalidate: adding a person to one discipline changes the eligibility of
 * the others too.
 *
 * It is deliberately a 2-element key — TanStack Query matches array elements
 * one by one, so a 3-element key would only match that exact team.
 */
export function inscripcionElegiblesPrefixKey(inscripcionId: string) {
  return ["inscripcion-elegibles", inscripcionId] as const;
}

/**
 * Stable query key for the candidate list of ONE team.
 */
export function inscripcionElegiblesKey(
  inscripcionId: string,
  equipoId: string,
) {
  return [...inscripcionElegiblesPrefixKey(inscripcionId), equipoId] as const;
}

/**
 * Query hook for the team-scoped participant selector.
 *
 * `equipoId` is null when no team is targeted — the query stays disabled.
 */
async function fetchElegibles(
  inscripcionId: string,
  equipoId: string,
): Promise<ElegiblesEquipoOut> {
  const res = await getElegiblesEquipo(inscripcionId, equipoId);
  if (!res.success || !res.data) {
    throw new Error(
      res.error?.message ??
        "Error al cargar los participantes elegibles del equipo",
    );
  }
  return res.data;
}

/**
 * Query hook for the team-scoped participant selector.
 *
 * `equipoId` is null when no team is targeted — the query stays disabled.
 */
export function useElegiblesEquipo(
  inscripcionId: string,
  equipoId: string | null,
): UseQueryResult<ElegiblesEquipoOut, Error> {
  return useQuery<ElegiblesEquipoOut, Error>({
    queryKey: inscripcionElegiblesKey(inscripcionId, equipoId ?? ""),
    queryFn: () => fetchElegibles(inscripcionId, equipoId ?? ""),
    enabled: !!inscripcionId && !!equipoId,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

/**
 * Candidate list of EVERY team of the inscription, in one go.
 *
 * The team card needs to know whether somebody can be added BEFORE the modal
 * opens (otherwise the button opens a selector with no candidates). It also
 * gives the matrix persona × equipo for free: one cup authorises a person in
 * every contracted discipline, so the teams share candidates.
 *
 * The queries use the SAME key as `useElegiblesEquipo`, so the modal opens
 * with the data already in cache — no loading, no refetch.
 */
export function useElegiblesEquipos(
  inscripcionId: string,
  equipoIds: string[],
): Array<{
  equipoId: string;
  data: ElegiblesEquipoOut | undefined;
  isPending: boolean;
  isError: boolean;
  error: Error | null;
}> {
  const resultados = useQueries({
    queries: equipoIds.map((equipoId) => ({
      queryKey: inscripcionElegiblesKey(inscripcionId, equipoId),
      queryFn: () => fetchElegibles(inscripcionId, equipoId),
      staleTime: 30 * 1000,
      gcTime: 5 * 60 * 1000,
    })),
  });

  return resultados.map((resultado, index) => ({
    equipoId: equipoIds[index],
    data: resultado.data,
    isPending: resultado.isPending,
    isError: resultado.isError,
    error: resultado.error ?? null,
  }));
}
