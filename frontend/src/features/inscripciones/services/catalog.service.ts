"use client";

import { api } from "@/lib/api";
import type { ApiResponse } from "@/types/api.types";

// ── Catalog Types ──────────────────────────────────────────────────────────────

export interface PaqueteDisciplina {
  disciplina_id: string;
  disciplina_nombre: string;
  disciplina_sigla: string;
  min_jugadores: number | null;
  max_jugadores: number | null;
}

/**
 * @deprecated Use PaqueteListContract from paquete.schema.ts instead.
 * This interface is kept for backward compatibility during transition.
 */
export interface Paquete {
  id: string;
  evento_id: string;
  nombre: string;
  descripcion: string | null;
  tipo: string;
  modo_disciplinas: string;
  cantidad_disciplinas: number;
  /** Minimum commercial purchase quantity (renamed from cantidad_maxima_participantes). */
  cantidad_minima_compra: number;
  /** Total equipos allowed (equals cantidad_disciplinas for ELEGIBLE mode). */
  cantidad_maxima_equipos: number;
  /** Preventa price (maps to precio_preventa from backend). */
  precio_promocional: number | null;
  precio_regular: number | null;
  /** Whether the package includes the fiesta benefit. */
  tiene_fiesta: boolean;
  /** Whether the package includes the box benefit. */
  tiene_box: boolean;
  /** Whether the package includes the cerveza benefit. */
  tiene_cerveza: boolean;
  /** Disciplina sigla summary for chips (e.g., ["F7M", "VOL", "BAS"]). */
  disciplinas_resumen: string[];
  /** Disciplinas are NOT included in list response; fetch via GET /catalogo/paquetes/{id} for details. */
  disciplinas?: PaqueteDisciplina[];
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
  evento_id: string;
  evento_nombre: string;
  nombre: string;
  /** Min birth year for this category (backend field: promocion_desde). */
  anio_minimo: number;
  /** Max birth year for this category (backend field: promocion_hasta). */
  anio_maximo: number;
  esta_activa: boolean;
}

export interface Promocion {
  id: string;
  anio: number;
  /** Full name of the promocion. */
  nombre: string;
  /** Whether the promocion is currently active. */
  activa: boolean;
}

type PaqueteApi = Omit<
  Paquete,
  "precio_promocional" | "precio_regular" | "cantidad_minima_compra"
> & {
  precio_promocional: number | string | null;
  precio_regular: number | string | null;
  // Backward compatibility: old backend sends cantidad_maxima_participantes
  cantidad_maxima_participantes?: number;
  cantidad_minima_compra?: number;
};

function normalizarPrecio(precio: number | string | null): number | null {
  if (precio === null) return null;

  const valor = Number(precio);
  return Number.isFinite(valor) ? valor : null;
}

// ── API Functions ──────────────────────────────────────────────────────────────

export async function getPaquetes(): Promise<ApiResponse<Paquete[]>> {
  const { data } = await api.get<ApiResponse<PaqueteApi[]>>(
    "/catalogo/paquetes/",
  );
  return {
    ...data,
    data:
      data.data?.map((paquete) => ({
        ...paquete,
        // Normalize price fields
        precio_promocional: normalizarPrecio(paquete.precio_promocional),
        precio_regular: normalizarPrecio(paquete.precio_regular),
        // Canonical field name: cantidad_minima_compra
        // Fall back to cantidad_maxima_participantes during transition
        cantidad_minima_compra:
          paquete.cantidad_minima_compra ??
          paquete.cantidad_maxima_participantes ??
          0,
        // Ensure benefit flags exist
        tiene_box: paquete.tiene_box ?? false,
        tiene_cerveza: paquete.tiene_cerveza ?? false,
        // Ensure disciplinas_resumen exists
        disciplinas_resumen: paquete.disciplinas_resumen ?? [],
      })) ?? [],
  };
}

export async function getPaqueteDisciplinas(
  paqueteId: string,
): Promise<ApiResponse<PaqueteDisciplina[]>> {
  // Backend GET /catalogo/paquetes/{id} returns PaqueteDetailOut with disciplinas array.
  // The response is {success: true, data: PaqueteDetailOut, message: ...}.
  // We extract the disciplinas field.
  const { data } = await api.get<
    ApiResponse<{ disciplinas: PaqueteDisciplina[] }>
  >(`/catalogo/paquetes/${paqueteId}/`);
  if (!data.success || !data.data) {
    return { success: false, data: [], message: data.message ?? "Error" };
  }
  return {
    ...data,
    data: data.data.disciplinas,
  };
}

export async function getDisciplinas(): Promise<ApiResponse<Disciplina[]>> {
  const { data } = await api.get<ApiResponse<Disciplina[]>>(
    "/catalogo/disciplinas/",
  );
  return data;
}

export async function getCategorias(): Promise<ApiResponse<Categoria[]>> {
  const { data } = await api.get<ApiResponse<Categoria[]>>(
    "/catalogo/categorias/",
  );
  return data;
}

export async function getPromociones(): Promise<ApiResponse<Promocion[]>> {
  const { data } = await api.get<ApiResponse<Promocion[]>>(
    "/catalogo/promociones/",
  );
  return data;
}
