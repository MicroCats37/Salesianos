/**
 * Server-safe paquetes fetcher for the landing page.
 *
 * Uses native fetch (not axios) so it works in both Server Components
 * and Client Components. Does NOT require auth — paquetes are public.
 */

import type { ApiResponse } from "@/types/api.types";

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
  modo_disciplinas: "FIJO" | "ELEGIBLE" | string;
  cantidad_disciplinas_requeridas: number | null;
  cantidad_maxima_equipos: number;
  disciplinas: PaqueteDisciplina[];
}

export interface PaqueteDisciplina {
  disciplina_id: string;
  disciplina_nombre: string;
  disciplina_sigla: string;
  min_jugadores: number | null;
  max_jugadores: number | null;
}

const configuredBaseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

const BASE_URL =
  typeof window === "undefined" && configuredBaseUrl.startsWith("/")
    ? "http://backend:8000/api"
    : configuredBaseUrl;

/**
 * Fetch active paquetes from the backend.
 * Returns null on network/parse failure (caller should handle fallback).
 */
export async function fetchPaquetes(): Promise<Paquete[] | null> {
  try {
    const res = await fetch(`${BASE_URL}/inscripciones/paquetes/`, {
      cache: "no-store",
    });

    if (!res.ok) return null;

    const json = (await res.json()) as ApiResponse<Paquete[]>;

    if (!json.success || json.data === null) return null;

    // Return only active paquetes
    return json.data.filter((p) => p.esta_activo);
  } catch {
    return null;
  }
}

/**
 * Format a precio number as "S/ 1,350".
 */
export function formatPrecio(precio: number): string {
  return `S/ ${precio.toLocaleString("es-PE", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })}`;
}

/**
 * Return the display price for a paquete.
 * Uses precio_promocional when available, otherwise precio_regular.
 */
export function getDisplayPrecio(paquete: Paquete): string {
  if (paquete.precio_promocional !== null && paquete.precio_promocional > 0) {
    return formatPrecio(paquete.precio_promocional);
  }
  return formatPrecio(paquete.precio_regular);
}

/**
 * Return all paquetes in their original order — no filtering.
 * The landing renders every paquete the backend reports as active.
 */
export function getFeaturedPaquetes(paquetes: Paquete[]): Paquete[] {
  return paquetes;
}
