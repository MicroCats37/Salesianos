"use client";

import { api } from "@/lib/api";
import type { ApiResponse } from "@/types/api.types";

// ── Catalog Types ──────────────────────────────────────────────────────────────

export interface Evento {
  id: string;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  esta_activo: boolean;
}

export interface PaqueteDisciplina {
  disciplina_id: string;
  disciplina_nombre: string;
  disciplina_sigla: string;
  min_jugadores: number | null;
  max_jugadores: number | null;
}

export interface Paquete {
  id: string;
  nombre: string;
  descripcion: string | null;
  cantidad_maxima_participantes: number;
  precio_regular: number;
  precio_promocional: number | null;
  valido_desde: string;
  valido_hasta: string;
  esta_activo: boolean;
  modo_disciplinas: string;
  cantidad_disciplinas_requeridas: number;
  /** Total equipos the package allows (FIJO => paquete_disciplinas count). */
  cantidad_maxima_equipos: number;
  disciplinas: PaqueteDisciplina[];
}

export interface Disciplina {
  id: string;
  nombre: string;
  sigla: string;
  modalidad: string;
  min_jugadores: number;
  max_jugadores: number;
  esta_activa: boolean;
}

export interface Categoria {
  id: string;
  disciplina_id: string;
  nombre: string;
  anio_minimo: number;
  anio_maximo: number;
  esta_activa: boolean;
}

export interface Promocion {
  id: string;
  anio: number;
  colegio: string;
  nombre: string;
  activa: boolean;
}

// ── API Functions ──────────────────────────────────────────────────────────────

export async function getEventos(): Promise<ApiResponse<Evento[]>> {
  const { data } = await api.get<ApiResponse<Evento[]>>(
    "/inscripciones/eventos/",
  );
  return data;
}

export async function getPaquetes(): Promise<ApiResponse<Paquete[]>> {
  const { data } = await api.get<ApiResponse<Paquete[]>>(
    "/inscripciones/paquetes/",
  );
  return data;
}

export async function getPaqueteDisciplinas(
  paqueteId: string,
): Promise<ApiResponse<PaqueteDisciplina[]>> {
  const { data } = await api.get<ApiResponse<PaqueteDisciplina[]>>(
    `/inscripciones/paquetes/${paqueteId}/disciplinas`,
  );
  return data;
}

export async function getDisciplinas(): Promise<ApiResponse<Disciplina[]>> {
  const { data } = await api.get<ApiResponse<Disciplina[]>>(
    "/inscripciones/disciplinas/",
  );
  return data;
}

export async function getCategorias(
  disciplinaId: string,
): Promise<ApiResponse<Categoria[]>> {
  const { data } = await api.get<ApiResponse<Categoria[]>>(
    `/inscripciones/disciplinas/${disciplinaId}/categorias`,
  );
  return data;
}

export async function getPromociones(): Promise<ApiResponse<Promocion[]>> {
  const { data } = await api.get<ApiResponse<Promocion[]>>(
    "/inscripciones/promociones/",
  );
  return data;
}
