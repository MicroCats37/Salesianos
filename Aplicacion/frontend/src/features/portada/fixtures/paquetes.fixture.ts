import type { PaqueteListContract } from "./paquete.schema";

export type Paquete = PaqueteListContract;

/**
 * PROVISIONAL_CONTRACT_FIXTURE — el catálogo de paquetes de la edición 2026.
 *
 * Los importes son los PUBLICADOS por la organización: el frontend no calcula
 * precios, no aplica promociones y no decide elegibilidad. Cuando el
 * catálogo real esté congelado, este archivo se sustituye por el servicio y
 * las vistas no cambian.
 */
export const PAQUETES_FIXTURE: PaqueteListContract[] = [
  {
    id: "pack-familia",
    evento_id: "salesianos-fest-2026",
    nombre: "Pack Familia",
    tipo: "PACK",
    modo_disciplinas: "ELEGIBLE",
    cantidad_disciplinas: 3,
    cantidad_minima_compra: 10,
    cantidad_maxima_equipos: 4,
    precio_preventa: 90,
    precio_regular: 120,
    precio_promocional: null,
    tiene_fiesta: true,
    tiene_box: true,
    tiene_cerveza: true,
    disciplinas_resumen: ["F7M", "F7F", "VOL"],
    disciplinas: [
      {
        disciplina_id: "f7m",
        disciplina_nombre: "Fútbol 7 Masculino",
        disciplina_sigla: "F7M",
        min_jugadores: 7,
        max_jugadores: 10,
      },
      {
        disciplina_id: "f7f",
        disciplina_nombre: "Fútbol 7 Femenino",
        disciplina_sigla: "F7F",
        min_jugadores: 7,
        max_jugadores: 10,
      },
      {
        disciplina_id: "vol",
        disciplina_nombre: "Vóley Mixto",
        disciplina_sigla: "VOL",
        min_jugadores: 6,
        max_jugadores: 8,
      },
    ],
    beneficios: [
      {
        tipo: "FIESTA",
        cantidad: 1,
        alcance: "GRUPAL",
        modo_calculo: "POR_CUPO",
      },
      {
        tipo: "BOX",
        cantidad: 1,
        alcance: "INDIVIDUAL",
        modo_calculo: "POR_CUPO",
      },
    ],
    precios: [
      {
        etapa: "PREVENTA",
        precio_unitario: 90,
        vigente_desde: "2026-09-01",
        vigente_hasta: "2026-10-31",
      },
      {
        etapa: "REGULAR",
        precio_unitario: 120,
        vigente_desde: "2026-11-01",
        vigente_hasta: null,
      },
    ],
    descripcion:
      "Hasta tres disciplinas para toda la promoción, con entrada a la fiesta, box del festival y cerveza.",
    minimo_compra_inicial: 10,
  },
  {
    id: "pack-futbol-7-masculino",
    evento_id: "salesianos-fest-2026",
    nombre: "Fútbol 7 Masculino",
    tipo: "DISCIPLINA",
    modo_disciplinas: "FIJO",
    cantidad_disciplinas: 1,
    cantidad_minima_compra: 7,
    cantidad_maxima_equipos: 2,
    precio_preventa: 70,
    precio_regular: 90,
    precio_promocional: null,
    tiene_fiesta: true,
    tiene_box: false,
    tiene_cerveza: true,
    disciplinas_resumen: ["F7M"],
    disciplinas: [
      {
        disciplina_id: "f7m",
        disciplina_nombre: "Fútbol 7 Masculino",
        disciplina_sigla: "F7M",
        min_jugadores: 7,
        max_jugadores: 10,
      },
    ],
    beneficios: [
      {
        tipo: "FIESTA",
        cantidad: 1,
        alcance: "INDIVIDUAL",
        modo_calculo: "POR_CUPO",
      },
    ],
    precios: [
      {
        etapa: "PREVENTA",
        precio_unitario: 70,
        vigente_desde: "2026-09-01",
        vigente_hasta: "2026-10-31",
      },
      {
        etapa: "REGULAR",
        precio_unitario: 90,
        vigente_desde: "2026-11-01",
        vigente_hasta: null,
      },
    ],
    descripcion:
      "Una sola disciplina de fútbol 7, con entrada a la fiesta y cerveza para laediatrición.",
  },
  {
    id: "pack-voley-mixto",
    evento_id: "salesianos-fest-2026",
    nombre: "Vóley Mixto",
    tipo: "DISCIPLINA",
    modo_disciplinas: "FIJO",
    cantidad_disciplinas: 1,
    cantidad_minima_compra: 6,
    cantidad_maxima_equipos: 2,
    precio_preventa: 70,
    precio_regular: 90,
    precio_promocional: null,
    tiene_fiesta: true,
    tiene_box: false,
    tiene_cerveza: true,
    disciplinas_resumen: ["VOL"],
    disciplinas: [
      {
        disciplina_id: "vol",
        disciplina_nombre: "Vóley Mixto",
        disciplina_sigla: "VOL",
        min_jugadores: 6,
        max_jugadores: 8,
      },
    ],
    beneficios: [
      {
        tipo: "FIESTA",
        cantidad: 1,
        alcance: "INDIVIDUAL",
        modo_calculo: "POR_CUPO",
      },
    ],
    precios: [
      {
        etapa: "PREVENTA",
        precio_unitario: 70,
        vigente_desde: "2026-09-01",
        vigente_hasta: "2026-10-31",
      },
      {
        etapa: "REGULAR",
        precio_unitario: 90,
        vigente_desde: "2026-11-01",
        vigente_hasta: null,
      },
    ],
    descripcion:
      "Vóley mixto en espacios techados, con entrada a la fiesta y cerveza para la promoción.",
  },
];
