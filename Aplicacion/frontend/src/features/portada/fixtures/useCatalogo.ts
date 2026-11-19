"use client";

import { useQuery } from "@tanstack/react-query";
import { z } from "zod";

/**
 * PROVISIONAL_CONTRACT_FIXTURE — el catálogo público de la portada.
 *
 * La etapa de esqueleto no consume endpoints: los valores vienen del fixture
 * determinista de abajo, con los MISMOS campos que publica el backend
 * (`DisciplinaOut` y `CategoriaOut`). Cuando el contrato esté congelado, este
 * archivo se sustituye por el servicio real y las vistas no cambian.
 *
 * NO calcula nada: los valores están publicados, no derivados.
 */

/** Espejo 1:1 de `DisciplinaOut` (backend). */
export const DisciplinaOutSchema = z.object({
  id: z.string(),
  nombre: z.string(),
  sigla: z.string(),
  modalidad: z.string(),
  min_jugadores: z.number(),
  max_jugadores: z.number(),
});

export type DisciplinaOut = z.infer<typeof DisciplinaOutSchema>;

/** Espejo 1:1 de `CategoriaOut` (backend). */
export const CategoriaOutSchema = z.object({
  id: z.string(),
  evento_id: z.string(),
  evento_nombre: z.string(),
  nombre: z.string(),
  promocion_desde: z.number(),
  promocion_hasta: z.number(),
});

export type CategoriaOut = z.infer<typeof CategoriaOutSchema>;

/** Orden editorial de las tabs del campeonato: una por disciplina. */
export const ORDEN_DISCIPLINAS = ["F7M", "F7F", "VOL", "BAS"] as const;

export interface DisciplinaPresentacion {
  /** Stat de canchas: "4 CANCHAS". */
  stat: string;
  /** Bajada del stat: "FÚTBOL 7 · GRASS SINTÉTICO". */
  etiqueta: string;
  /** Detalle de las canchas (texto literal del micrositio oficial). */
  canchas: string;
  /** Imagen de la disciplina en la portada. */
  imagen: string;
  /** Texto alternativo de la imagen. */
  alt: string;
}

const FUTBOL: DisciplinaPresentacion = {
  stat: "4 CANCHAS",
  etiqueta: "FÚTBOL 7 · GRASS SINTÉTICO",
  canchas: "4 canchas de grass sintético.",
  imagen: "/images/portada/futbol.png",
  alt: "Fútbol, imagen de la propuesta del festival",
};

const VOLEY: DisciplinaPresentacion = {
  stat: "2 CANCHAS",
  etiqueta: "VÓLEY MIXTO · ESPACIOS TECHADOS",
  canchas: "2 canchas para compartir la pasión por el vóley.",
  imagen: "/images/portada/voley.png",
  alt: "Jugadora de vóley, imagen de la propuesta del festival",
};

const BASQUET: DisciplinaPresentacion = {
  stat: "1 CANCHA",
  etiqueta: "BÁSQUET · COMPITE CON TU PROMOCIÓN",
  canchas: "1 cancha de básquet.",
  imagen: "/images/portada/basquet.png",
  alt: "Cancha y balón de básquet, imagen de la propuesta del festival",
};

/**
 * Datos de presentación por sigla.
 *
 * Las canchas no viven en la API (el backend expone la disciplina y el
 * mínimo de jugadores, no el aforo de canchas), así que se mapearon desde
 * el micrositio oficial.
 */
export const MAPA_DISCIPLINA: Record<string, DisciplinaPresentacion> = {
  F7M: FUTBOL,
  F7F: FUTBOL,
  VOL: VOLEY,
  BAS: BASQUET,
};

/** Presentación de una disciplina, con respaldo genérico para siglas nuevas. */
export function presentacionDisciplina(
  sigla: string,
  nombre: string,
): DisciplinaPresentacion {
  return (
    MAPA_DISCIPLINA[sigla] ?? {
      stat: "CANCHAS DEL FESTIVAL",
      etiqueta: nombre.toUpperCase(),
      canchas: "",
      imagen: "/images/portada/futbol.png",
      alt: `${nombre}, imagen de la propuesta del festival`,
    }
  );
}

/**
 * PROVISIONAL_CONTRACT_FIXTURE — las disciplinas publicadas en el micrositio
 * oficial.
 */
export const DISCIPLINAS_FALLBACK: DisciplinaOut[] = [
  {
    id: "f7m",
    nombre: "Fútbol 7 Masculino",
    sigla: "F7M",
    modalidad: "MASCULINO",
    min_jugadores: 7,
    max_jugadores: 10,
  },
  {
    id: "f7f",
    nombre: "Fútbol 7 Femenino",
    sigla: "F7F",
    modalidad: "FEMENINO",
    min_jugadores: 7,
    max_jugadores: 10,
  },
  {
    id: "vol",
    nombre: "Vóley Mixto",
    sigla: "VOL",
    modalidad: "MIXTO",
    min_jugadores: 6,
    max_jugadores: 8,
  },
  {
    id: "bas",
    nombre: "Básquet Masculino",
    sigla: "BAS",
    modalidad: "MASCULINO",
    min_jugadores: 5,
    max_jugadores: 10,
  },
];

/** PROVISIONAL_CONTRACT_FIXTURE — las categorías publicadas en el micrositio. */
export const CATEGORIAS_FALLBACK: CategoriaOut[] = [
  {
    id: "junior",
    evento_id: "salesianos-fest-2026",
    evento_nombre: "Salesianos FEST 2026",
    nombre: "Junior",
    promocion_desde: 2012,
    promocion_hasta: 2025,
  },
  {
    id: "senior",
    evento_id: "salesianos-fest-2026",
    evento_nombre: "Salesianos FEST 2026",
    nombre: "Senior",
    promocion_desde: 1998,
    promocion_hasta: 2011,
  },
  {
    id: "master",
    evento_id: "salesianos-fest-2026",
    evento_nombre: "Salesianos FEST 2026",
    nombre: "Máster",
    promocion_desde: 1985,
    promocion_hasta: 1997,
  },
  {
    id: "super-master",
    evento_id: "salesianos-fest-2026",
    evento_nombre: "Salesianos FEST 2026",
    nombre: "Súper Máster",
    promocion_desde: 1970,
    promocion_hasta: 1984,
  },
];

/** Alias explicito del fixture. */
export const DISCIPLINAS_FIXTURE = DISCIPLINAS_FALLBACK;

/** Disciplinas activas del festival (GET /api/catalogo/disciplinas/). */
export function useDisciplinas() {
  return useQuery({
    queryKey: ["landing", "disciplinas"] as const,
    queryFn: () => DISCIPLINAS_FIXTURE,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

/** Alias explicito del fixture. */
export const CATEGORIAS_FIXTURE = CATEGORIAS_FALLBACK;

/** Categorías activas del festival (GET /api/catalogo/categorias/). */
export function useCategorias() {
  return useQuery({
    queryKey: ["landing", "categorias"] as const,
    queryFn: () => CATEGORIAS_FIXTURE,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}
