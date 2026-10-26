"use client";

import { useQuery } from "@tanstack/react-query";
import type { PaqueteDetailContract } from "../schemas/paquete.schema";
import {
  type Categoria,
  type Disciplina,
  getCategorias,
  getDisciplinas,
  getPaqueteDisciplinas,
  getPaquetes,
  getPromociones,
  type Paquete,
  type Promocion,
} from "../services/catalog.service";
import {
  fetchPaqueteDetail,
  fetchPaqueteList,
  paqueteQueryKeys,
} from "../services/paquete.service";

// ── Paquete Detail Hook ───────────────────────────────────────────────────────

/**
 * Fetch full package detail including prices, benefits, and disciplines.
 * Used when a package is selected to configure team creation.
 */
export function usePaqueteDetail(paqueteId: string | null) {
  return useQuery({
    queryKey: paqueteQueryKeys.detail(paqueteId ?? ""),
    queryFn: async (): Promise<PaqueteDetailContract> => {
      if (!paqueteId) {
        throw new Error("paqueteId is required");
      }
      return fetchPaqueteDetail(paqueteId);
    },
    enabled: Boolean(paqueteId),
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

// ── Paquetes Hook (NEW — typed with Zod validation) ───────────────────────────

/**
 * Fetch package list with Zod-validated contract types.
 * Uses canonical query keys for cache management.
 */
export function usePaquetes() {
  return useQuery({
    queryKey: paqueteQueryKeys.list(),
    queryFn: fetchPaqueteList,
    staleTime: 5 * 60 * 1000, // 5 min — catalog changes are admin-driven
    gcTime: 30 * 60 * 1000, // 30 min
  });
}

// ── Paquete Disciplinas Hook ──────────────────────────────────────────────────

export function usePaqueteDisciplinas(paqueteId: string | null) {
  return useQuery({
    queryKey: ["inscripcion", "paqueteDisciplinas", paqueteId],
    queryFn: async () => {
      if (!paqueteId) return [];
      const response = await getPaqueteDisciplinas(paqueteId);
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ?? "Error al cargar disciplinas del paquete",
        );
      }
      return response.data;
    },
    enabled: Boolean(paqueteId),
  });
}

// ── Disciplinas Hook ──────────────────────────────────────────────────────────

export function useDisciplinas() {
  return useQuery({
    queryKey: ["inscripcion", "disciplinas"],
    queryFn: async () => {
      const response = await getDisciplinas();
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ?? "Error al cargar disciplinas",
        );
      }
      return response.data as Disciplina[];
    },
  });
}

// ── Categorias Hook ───────────────────────────────────────────────────────────

export function useCategorias() {
  return useQuery({
    queryKey: ["inscripcion", "categorias"],
    queryFn: async () => {
      const response = await getCategorias();
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ?? "Error al cargar categorías",
        );
      }
      return response.data as Categoria[];
    },
  });
}

// ── Promociones Hook ───────────────────────────────────────────────────────────

export function usePromociones() {
  return useQuery({
    queryKey: ["inscripcion", "promociones"],
    queryFn: async () => {
      const response = await getPromociones();
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ?? "Error al cargar promociones",
        );
      }
      return response.data as Promocion[];
    },
  });
}
