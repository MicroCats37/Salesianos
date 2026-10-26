/**
 * Etapa de venta de inscripciones.
 *
 * Replica `pricing.js` del micrositio oficial: el calendario de venta vive
 * en el frontend (el backend solo expone `precio_preventa` y
 * `precio_regular`, sin hora de corte) y los importes salen de la API.
 *
 * Las ventanas se comparan contra instantes absolutos: Lima no aplica
 * horario de verano, así que el offset `-05:00` de los ISO es suficiente.
 */

import { VENTAS } from "./config/festival";

export type EtapaVenta =
  | "preventa"
  | "gap"
  | "regular"
  | "extemporanea"
  | "cerrada";

export interface EstadoVenta {
  key: EtapaVenta;
  etiqueta: string;
  nota: string;
  /** `true` cuando hay un precio público aplicable en esta etapa. */
  conPrecio: boolean;
}

const PREVENTA_ETIQUETA = "PREVENTA · HASTA EL 25 OCT, 8 P. M.";
const PREVENTA_NOTA =
  "Preventa hasta el 25 de octubre a las 8:00 p. m. (hora de Lima).";
const REGULAR_ETIQUETA = "TARIFA REGULAR · HASTA EL 8 NOV, 8 P. M.";
const REGULAR_NOTA =
  "Inscripción regular del 26 de octubre al 8 de noviembre; cierre a las 8:00 p. m. (hora de Lima).";
const EXTEMPORANEA_ETIQUETA = "INSCRIPCIÓN EXTEMPORÁNEA";
const EXTEMPORANEA_NOTA =
  "Del 9 al 18 de noviembre, hasta las 8:00 p. m. La tarifa extemporánea debe confirmarse con la organización.";
const CERRADA_ETIQUETA = "INSCRIPCIONES FINALIZADAS";
const CERRADA_NOTA =
  "El cronograma publicado cerró las inscripciones el 18 de noviembre a las 8:00 p. m. Contacta a la organización para cualquier consulta.";

function instante(iso: string): number {
  return new Date(iso).getTime();
}

/**
 * Estado de la venta para una fecha dada.
 */
export function estado(now: number = Date.now()): EstadoVenta {
  if (now < instante(VENTAS.preventaHasta)) {
    return {
      key: "preventa",
      etiqueta: PREVENTA_ETIQUETA,
      nota: PREVENTA_NOTA,
      conPrecio: true,
    };
  }
  if (now < instante(VENTAS.regularDesde)) {
    return {
      key: "gap",
      etiqueta: "PREVENTA FINALIZADA",
      nota: "La inscripción regular comienza el 26 de octubre. Consulta con la organización.",
      conPrecio: false,
    };
  }
  if (now < instante(VENTAS.regularHasta)) {
    return {
      key: "regular",
      etiqueta: REGULAR_ETIQUETA,
      nota: REGULAR_NOTA,
      conPrecio: true,
    };
  }
  if (now < instante(VENTAS.extemporaneaDesde)) {
    return {
      key: "gap",
      etiqueta: "ETAPA REGULAR FINALIZADA",
      nota: "La inscripción extemporánea comienza el 9 de noviembre. Consulta su tarifa con la organización.",
      conPrecio: false,
    };
  }
  if (now < instante(VENTAS.inscripcionCierra)) {
    return {
      key: "extemporanea",
      etiqueta: EXTEMPORANEA_ETIQUETA,
      nota: EXTEMPORANEA_NOTA,
      conPrecio: false,
    };
  }
  return {
    key: "cerrada",
    etiqueta: CERRADA_ETIQUETA,
    nota: CERRADA_NOTA,
    conPrecio: false,
  };
}

/** Etiqueta pública de la etapa vigente. */
export function etiqueta(now: number = Date.now()): string {
  return estado(now).etiqueta;
}

/** Nota pública de la etapa vigente. */
export function nota(now: number = Date.now()): string {
  return estado(now).nota;
}

export interface PaquetePrecio {
  precio_preventa: number | null;
  precio_regular: number | null;
  cantidad_minima_compra: number;
}

/**
 * Precio unitario aplicable en la etapa actual.
 *
 * En preventa se muestra el precio de preventa; en regular, el regular; en
 * las etapas sin tarifa publicada devuelve `null` y la card muestra
 * "Consultar".
 */
export function precioDe(
  paquete: PaquetePrecio,
  now: number = Date.now(),
): number | null {
  const etapa = estado(now).key;
  if (etapa === "preventa") return paquete.precio_preventa;
  if (etapa === "regular") return paquete.precio_regular;
  return null;
}

/**
 * Unidad del precio total: "x equipo" para una nómina de equipo completo,
 * "x promoción" cuando el paquete cubre a toda la promoción.
 */
export function unidadPrecio(
  paquete: PaquetePrecio,
): "x equipo" | "x promoción" {
  return paquete.cantidad_minima_compra <= 10 ? "x equipo" : "x promoción";
}
