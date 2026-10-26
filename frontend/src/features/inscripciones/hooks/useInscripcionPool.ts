"use client";

import { type UseQueryResult, useQuery } from "@tanstack/react-query";
import {
  getPool,
  getSaldoInscripcion,
  type PoolOut,
  type SaldoOut,
} from "../services/pool.service";

/**
 * Stable query key for the participant pool of one inscripcion.
 *
 * Use it everywhere the pool cache is read or written so the key never drifts.
 */
export function inscripcionPoolKey(inscripcionId: string) {
  return ["inscripcion-pool", inscripcionId] as const;
}

/** Stable query key for the cupo saldo of one inscripcion. */
export function inscripcionSaldoKey(inscripcionId: string) {
  return ["inscripcion-saldo", inscripcionId] as const;
}

/**
 * Query hook for the participant pool.
 *
 * The pool is read-only from the UI: eligibility comes from the backend, never
 * from a local computation.
 */
export function useInscripcionPool(
  inscripcionId: string,
): UseQueryResult<PoolOut, Error> {
  return useQuery<PoolOut, Error>({
    queryKey: inscripcionPoolKey(inscripcionId),
    queryFn: async () => {
      const res = await getPool(inscripcionId);
      if (!res.success || !res.data) {
        throw new Error(
          res.error?.message ?? "Error al cargar el pool de participantes",
        );
      }
      return res.data;
    },
    enabled: !!inscripcionId,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

/**
 * Query hook for the cupo saldo of the inscription.
 *
 * `disponibles_pagados === 0` means there is no paid capacity left, so nobody
 * in the pool can be assigned to a team.
 */
export function useInscripcionSaldo(
  inscripcionId: string,
): UseQueryResult<SaldoOut, Error> {
  return useQuery<SaldoOut, Error>({
    queryKey: inscripcionSaldoKey(inscripcionId),
    queryFn: async () => {
      const res = await getSaldoInscripcion(inscripcionId);
      if (!res.success || !res.data) {
        throw new Error(res.error?.message ?? "Error al calcular el saldo");
      }
      return res.data;
    },
    enabled: !!inscripcionId,
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}
