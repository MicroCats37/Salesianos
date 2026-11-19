"use client";

import { useLandingPaquetes } from "@/features/landing/hooks/useLandingPaquetes";
import type { Paquete } from "@/features/landing/paquetes.service";
import { PaquetesCards } from "./PaquetesCards";

type DisciplinaFallback = Paquete["disciplinas"][number];
type BeneficioFallback = Paquete["beneficios"][number];
type PrecioFallback = Paquete["precios"][number];

interface PaqueteFallbackInput {
  id: string;
  nombre: string;
  descripcion: string;
  tipo: Paquete["tipo"];
  modo_disciplinas: Paquete["modo_disciplinas"];
  cantidad_disciplinas: number;
  cantidad_minima_compra: number;
  cantidad_maxima_equipos: number;
  precio_preventa: number;
  precio_regular: number;
  tiene_fiesta: boolean;
  tiene_box: boolean;
  tiene_cerveza: boolean;
  disciplinas: DisciplinaFallback[];
  beneficios: BeneficioFallback[];
}

const F7M: DisciplinaFallback = {
  disciplina_id: "fallback-f7m",
  disciplina_nombre: "Fútbol 7 Masculino",
  disciplina_sigla: "F7M",
  min_jugadores: 7,
  max_jugadores: 10,
};

const F7F: DisciplinaFallback = {
  disciplina_id: "fallback-f7f",
  disciplina_nombre: "Fútbol 7 Femenino",
  disciplina_sigla: "F7F",
  min_jugadores: 7,
  max_jugadores: 10,
};

const VOL: DisciplinaFallback = {
  disciplina_id: "fallback-vol",
  disciplina_nombre: "Vóley Mixto",
  disciplina_sigla: "VOL",
  min_jugadores: 6,
  max_jugadores: 8,
};

const BAS: DisciplinaFallback = {
  disciplina_id: "fallback-bas",
  disciplina_nombre: "Básquet Masculino",
  disciplina_sigla: "BAS",
  min_jugadores: 5,
  max_jugadores: 10,
};

const FIESTA_FIJO: BeneficioFallback = {
  tipo: "FIESTA",
  cantidad: 1,
  alcance: "INDIVIDUAL",
  modo_calculo: "FIJO_INICIAL",
};

const FIESTA_POR_CUPO: BeneficioFallback = {
  tipo: "FIESTA",
  cantidad: 1,
  alcance: "INDIVIDUAL",
  modo_calculo: "POR_CUPO",
};

const BOX: BeneficioFallback = {
  tipo: "BOX",
  cantidad: 1,
  alcance: "GRUPAL",
  modo_calculo: "FIJO_INICIAL",
};

const CERVEZA: BeneficioFallback = {
  tipo: "CERVEZA",
  cantidad: 6,
  alcance: "GRUPAL",
  modo_calculo: "FIJO_INICIAL",
};

function crearPrecios(
  precioPreventa: number,
  precioRegular: number,
): PrecioFallback[] {
  return [
    {
      etapa: "PREVENTA",
      precio_unitario: precioPreventa,
      vigente_desde: "2026-10-19",
      vigente_hasta: "2026-10-31",
    },
    {
      etapa: "REGULAR",
      precio_unitario: precioRegular,
      vigente_desde: "2026-10-31",
      vigente_hasta: null,
    },
  ];
}

function crearPaqueteFallback(paquete: PaqueteFallbackInput): Paquete {
  return {
    id: paquete.id,
    evento_id: "fallback-salesianos-fest-2026",
    nombre: paquete.nombre,
    descripcion: paquete.descripcion,
    tipo: paquete.tipo,
    modo_disciplinas: paquete.modo_disciplinas,
    cantidad_disciplinas: paquete.cantidad_disciplinas,
    cantidad_minima_compra: paquete.cantidad_minima_compra,
    cantidad_maxima_equipos: paquete.cantidad_maxima_equipos,
    precio_preventa: paquete.precio_preventa,
    precio_regular: paquete.precio_regular,
    precio_promocional: null,
    tiene_fiesta: paquete.tiene_fiesta,
    tiene_box: paquete.tiene_box,
    tiene_cerveza: paquete.tiene_cerveza,
    disciplinas_resumen: paquete.disciplinas.map(
      (disciplina) => disciplina.disciplina_sigla,
    ),
    disciplinas: paquete.disciplinas,
    beneficios: paquete.beneficios,
    precios: crearPrecios(paquete.precio_preventa, paquete.precio_regular),
  };
}

export const FALLBACK_PAQUETES: Paquete[] = [
  crearPaqueteFallback({
    id: "fallback-reencuentro",
    nombre: "Reencuentro + Fiesta",
    descripcion: "Reencuentro con acceso a fiesta de cierre.",
    tipo: "PACK",
    modo_disciplinas: "ELEGIBLE",
    cantidad_disciplinas: 1,
    cantidad_minima_compra: 10,
    cantidad_maxima_equipos: 1,
    precio_preventa: 40,
    precio_regular: 50,
    tiene_fiesta: true,
    tiene_box: false,
    tiene_cerveza: false,
    disciplinas: [F7F, VOL, BAS],
    beneficios: [FIESTA_FIJO],
  }),
  crearPaqueteFallback({
    id: "fallback-pichanga",
    nombre: "Pichanga + Fiesta",
    descripcion: "Pichanga competitiva con acceso a fiesta de cierre.",
    tipo: "PACK",
    modo_disciplinas: "FIJO",
    cantidad_disciplinas: 1,
    cantidad_minima_compra: 10,
    cantidad_maxima_equipos: 1,
    precio_preventa: 45,
    precio_regular: 55,
    tiene_fiesta: true,
    tiene_box: false,
    tiene_cerveza: false,
    disciplinas: [F7M],
    beneficios: [FIESTA_FIJO],
  }),
  crearPaqueteFallback({
    id: "fallback-duo",
    nombre: "Dúo + Fiesta Box",
    descripcion: "Pack para dos personas con fiesta y box de bebidas.",
    tipo: "PACK",
    modo_disciplinas: "ELEGIBLE",
    cantidad_disciplinas: 2,
    cantidad_minima_compra: 15,
    cantidad_maxima_equipos: 2,
    precio_preventa: 60,
    precio_regular: 70,
    tiene_fiesta: true,
    tiene_box: true,
    tiene_cerveza: true,
    disciplinas: [VOL, BAS],
    beneficios: [FIESTA_POR_CUPO, BOX, CERVEZA],
  }),
  crearPaqueteFallback({
    id: "fallback-trio",
    nombre: "Trío + Fiesta Box",
    descripcion: "Pack para tres personas con fiesta y box de bebidas.",
    tipo: "PACK",
    modo_disciplinas: "ELEGIBLE",
    cantidad_disciplinas: 3,
    cantidad_minima_compra: 20,
    cantidad_maxima_equipos: 3,
    precio_preventa: 60,
    precio_regular: 70,
    tiene_fiesta: true,
    tiene_box: true,
    tiene_cerveza: true,
    disciplinas: [F7M, VOL, BAS],
    beneficios: [FIESTA_POR_CUPO, BOX, CERVEZA],
  }),
  crearPaqueteFallback({
    id: "fallback-futbol-7-masculino",
    nombre: "Fútbol 7 Masculino",
    descripcion: "Torneo de fútbol 7 masculino.",
    tipo: "DISCIPLINA",
    modo_disciplinas: "FIJO",
    cantidad_disciplinas: 1,
    cantidad_minima_compra: 7,
    cantidad_maxima_equipos: 1,
    precio_preventa: 40,
    precio_regular: 50,
    tiene_fiesta: false,
    tiene_box: false,
    tiene_cerveza: false,
    disciplinas: [F7M],
    beneficios: [],
  }),
  crearPaqueteFallback({
    id: "fallback-futbol-7-femenino",
    nombre: "Fútbol 7 Femenino",
    descripcion: "Torneo de fútbol 7 femenino.",
    tipo: "DISCIPLINA",
    modo_disciplinas: "FIJO",
    cantidad_disciplinas: 1,
    cantidad_minima_compra: 7,
    cantidad_maxima_equipos: 1,
    precio_preventa: 40,
    precio_regular: 50,
    tiene_fiesta: false,
    tiene_box: false,
    tiene_cerveza: false,
    disciplinas: [F7F],
    beneficios: [],
  }),
  crearPaqueteFallback({
    id: "fallback-voley-mixto",
    nombre: "Vóley Mixto",
    descripcion: "Torneo de vóley mixto.",
    tipo: "DISCIPLINA",
    modo_disciplinas: "FIJO",
    cantidad_disciplinas: 1,
    cantidad_minima_compra: 6,
    cantidad_maxima_equipos: 1,
    precio_preventa: 40,
    precio_regular: 50,
    tiene_fiesta: false,
    tiene_box: false,
    tiene_cerveza: false,
    disciplinas: [VOL],
    beneficios: [],
  }),
  crearPaqueteFallback({
    id: "fallback-basquet-masculino",
    nombre: "Básquet Masculino",
    descripcion: "Torneo de básquet masculino.",
    tipo: "DISCIPLINA",
    modo_disciplinas: "FIJO",
    cantidad_disciplinas: 1,
    cantidad_minima_compra: 5,
    cantidad_maxima_equipos: 1,
    precio_preventa: 40,
    precio_regular: 50,
    tiene_fiesta: false,
    tiene_box: false,
    tiene_cerveza: false,
    disciplinas: [BAS],
    beneficios: [],
  }),
];

export function Paquetes() {
  const { data: paquetes } = useLandingPaquetes();
  const paquetesVisibles =
    paquetes && paquetes.length > 0 ? paquetes : FALLBACK_PAQUETES;

  return <PaquetesCards paquetes={paquetesVisibles} />;
}
