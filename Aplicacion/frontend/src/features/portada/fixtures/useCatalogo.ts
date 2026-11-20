"use client";

import { useQuery } from "@tanstack/react-query";
import { z } from "zod";

/**
 * PROVISIONAL_CONTRACT_FIXTURE — la presentación del catálogo público de la
 * portada.
 *
 * ## Lo que queda aquí y lo que se fue
 *
 * Las CATEGORÍAS se fueron de este archivo: la portada las lee del
 * SERVICIO real (`useCatalogoCategorias`, en
 * `@/features/inscripciones/hooks/useCatalogo`), que es el único cliente del
 * catálogo de la edición. El fixture declaraba un `evento_id` y un
 * `promocion_desde/hasta` que ningún backend publicaba.
 *
 * Las DISCIPLINAS siguen provisionales: su fixture replica la forma del
 * backend CONGELADO (`sigla`, `min_jugadores`), que no es la forma que
 * publica el backend objetivo (`slug`, `minimo_por_equipo`). Migrarlas es
 * un trabajo propio, con su propio espejo, y no se mezcla con la
 * restauración de las categorías.
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

/** Alias explicito del fixture. */
export const DISCIPLINAS_FIXTURE = DISCIPLINAS_FALLBACK;

/** Disciplinas activas del festival (PROVISIONAL: fixture del backend congelado). */
export function useDisciplinas() {
  return useQuery({
    queryKey: ["landing", "disciplinas"] as const,
    queryFn: () => DISCIPLINAS_FIXTURE,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}
