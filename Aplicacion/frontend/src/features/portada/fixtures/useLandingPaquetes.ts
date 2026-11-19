"use client";

import { useQuery } from "@tanstack/react-query";
import type { PaqueteListContract } from "./paquete.schema";
import { PAQUETES_FIXTURE } from "./paquetes.fixture";

/**
 * PROVISIONAL_CONTRACT_FIXTURE — los paquetes de la edición.
 *
 * En la etapa de esqueleto NO hay endpoint: el catálogo de paquetes es un
 * fixture determinista con los MISMOS campos que publica
 * `PaqueteListOut` (`paquete.schema.ts`). El precio llega publicado; el
 * frontend no lo calcula, no lo compara y no deriva elegibilidad.
 *
 * Cuando el catálogo real esté congelado, este archivo se sustituye por el
 * servicio y las vistas no cambian.
 */
export function useLandingPaquetes() {
  return useQuery({
    queryKey: ["landing", "paquetes"] as const,
    queryFn: () => PAQUETES_FIXTURE,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

export type { PaqueteListContract };
