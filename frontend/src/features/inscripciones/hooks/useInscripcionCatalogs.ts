"use client";

import { useQuery } from "@tanstack/react-query";
import {
  type Categoria,
  type Disciplina,
  type Evento,
  getCategorias,
  getDisciplinas,
  getEventos,
  getPaqueteDisciplinas,
  getPaquetes,
  getPromociones,
  type Paquete,
  type Promocion,
} from "../services/catalog.service";

// ── Evento Hook ───────────────────────────────────────────────────────────────

export function useEventos() {
  return useQuery({
    queryKey: ["inscripcion", "eventos"],
    queryFn: async () => {
      const response = await getEventos();
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Error al cargar eventos");
      }
      return response.data as Evento[];
    },
  });
}

// ── Paquetes Hook ──────────────────────────────────────────────────────────────

export function usePaquetes() {
  return useQuery({
    queryKey: ["inscripcion", "paquetes"],
    queryFn: async () => {
      const response = await getPaquetes();
      if (!response.success || !response.data) {
        throw new Error(response.error?.message ?? "Error al cargar paquetes");
      }
      return response.data as Paquete[];
    },
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

// ── Categorias Hook ────────────────────────────────────────────────────────────

export function useCategorias(disciplinaId: string | null) {
  return useQuery({
    queryKey: ["inscripcion", "categorias", disciplinaId],
    queryFn: async () => {
      if (!disciplinaId) return [];
      const response = await getCategorias(disciplinaId);
      if (!response.success || !response.data) {
        throw new Error(
          response.error?.message ?? "Error al cargar categorías",
        );
      }
      return response.data as Categoria[];
    },
    enabled: Boolean(disciplinaId),
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
