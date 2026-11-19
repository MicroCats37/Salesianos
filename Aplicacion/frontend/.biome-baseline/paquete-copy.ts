import type { PaqueteListContract } from "@/features/inscripciones/schemas/paquete.schema";

export const DISCIPLINA_COLORS = {
  F7M: "#16a34a",
  F7F: "#ec4899",
  VOL: "#f59e0b",
  BAS: "#0ea5e9",
} as const;

export const DEFAULT_DISCIPLINA_COLOR = "#312e8e";

export interface InclusionBullet {
  texto: string;
  destacado?: boolean;
}

export interface LineasPrecio {
  total: string;
  totalRegular: string | null;
  unitario: string;
  unidad: "equipo" | "promoción";
}

export function getDisciplinaColor(sigla: string | null | undefined): string {
  const clave = sigla?.trim().toUpperCase();
  if (
    clave === "F7M" ||
    clave === "F7F" ||
    clave === "VOL" ||
    clave === "BAS"
  ) {
    return DISCIPLINA_COLORS[clave];
  }
  return DEFAULT_DISCIPLINA_COLOR;
}

export function getDisciplinasOrdenadas(paquete: PaqueteListContract) {
  return [...paquete.disciplinas];
}

export function getUltimaDisciplina(paquete: PaqueteListContract) {
  const disciplinas = getDisciplinasOrdenadas(paquete);
  return disciplinas.at(-1) ?? null;
}

export function getColorAcento(paquete: PaqueteListContract): string {
  return getDisciplinaColor(getUltimaDisciplina(paquete)?.disciplina_sigla);
}

export function getDescripcionFallback(variant: "PACK" | "DISCIPLINA"): string {
  return variant === "PACK"
    ? "Elige tu disciplina y celebra con tu promoción."
    : "Para los que compiten en grande.";
}

/**
 * Etapa de venta queula tarjeta refleja.
 *
 * - `preventa` → precio de preventa, con el regular tachado como referencia.
 * - `regular` → precio regular, sin tachado.
 * - `consultar` → la etapa no publica tarifa (extemporánea o cerrada): la
 *   tarjeta muestra "Consultar" en vez de un importe.
 */
export type EtapaPrecio = "preventa" | "regular" | "consultar";

export function getUnidadPrecio(
  paquete: PaqueteListContract,
): "equipo" | "promoción" {
  return paquete.cantidad_minima_compra <= 10 ? "equipo" : "promoción";
}

export function getPrecioUnitario(
  paquete: PaqueteListContract,
  etapa: EtapaPrecio = "preventa",
): number | null {
  if (etapa === "consultar") return null;
  if (etapa === "regular") {
    return paquete.precio_regular ?? paquete.precio_preventa ?? null;
  }
  return paquete.precio_preventa ?? paquete.precio_regular ?? null;
}

export function formatMonto(monto: number): string {
  return `S/${monto.toLocaleString("es-PE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function getLineasPrecio(
  paquete: PaqueteListContract,
  etapa: EtapaPrecio = "preventa",
): LineasPrecio {
  const precioUnitario = getPrecioUnitario(paquete, etapa);
  const unidad = getUnidadPrecio(paquete);
  const total =
    precioUnitario === null
      ? null
      : precioUnitario * paquete.cantidad_minima_compra;
  const totalRegular =
    etapa === "preventa" &&
    paquete.precio_regular !== null &&
    paquete.precio_preventa !== null &&
    paquete.precio_regular > paquete.precio_preventa
      ? paquete.precio_regular * paquete.cantidad_minima_compra
      : null;

  return {
    total: total === null ? "Consultar" : `${formatMonto(total)} x ${unidad}`,
    totalRegular: totalRegular === null ? null : formatMonto(totalRegular),
    unitario:
      precioUnitario === null
        ? "Consultar"
        : `${formatMonto(precioUnitario)} x integrante`,
    unidad,
  };
}

function unirNombres(nombres: string[]): string {
  if (nombres.length === 0) return "la disciplina incluida";
  if (nombres.length === 1) return nombres[0];
  if (nombres.length === 2) return `${nombres[0]} y ${nombres[1]}`;
  return `${nombres.slice(0, -1).join(", ")} y ${nombres.at(-1)}`;
}

export function getTextoInscripcion(paquete: PaqueteListContract): string {
  const nombres = getDisciplinasOrdenadas(paquete).map(
    (disciplina) => disciplina.disciplina_nombre,
  );

  if (paquete.modo_disciplinas === "FIJO") {
    return `Inscripción a ${unirNombres(nombres)}.`;
  }

  if (paquete.cantidad_disciplinas === 1) {
    if (nombres.length === 0) return "Inscripción a 1 disciplina.";
    if (nombres.length === 1) return `Inscripción a ${nombres[0]}.`;
    return `Inscripción a ${nombres.slice(0, -1).join(", ")} o ${nombres.at(-1)}.`;
  }

  return `Inscripción a ${paquete.cantidad_disciplinas} disciplinas.`;
}

export function getInclusionBullets(
  paquete: PaqueteListContract,
): InclusionBullet[] {
  const bullets: InclusionBullet[] = [{ texto: getTextoInscripcion(paquete) }];

  if (paquete.tiene_fiesta) {
    bullets.push({
      texto: `${paquete.cantidad_minima_compra} pases para el ingreso a la fiesta${
        paquete.tiene_box ? " (zona box)" : ""
      }.`,
    });
  } else {
    bullets.push({
      texto: `${paquete.cantidad_minima_compra} integrantes como mínimo.`,
    });
  }

  if (paquete.tiene_box) {
    bullets.push({
      texto: "Acceso a un box exclusivo para la promoción.",
      destacado: true,
    });
  }

  if (paquete.tiene_cerveza) {
    const cantidadCerveza =
      paquete.beneficios.find((beneficio) => beneficio.tipo === "CERVEZA")
        ?.cantidad ?? 0;
    const cantidadCajas = Math.ceil(cantidadCerveza / 6);
    if (cantidadCajas > 0) {
      bullets.push({
        texto: `${cantidadCajas} caja${cantidadCajas === 1 ? "" : "s"} de cerveza.`,
        destacado: true,
      });
    }
  }

  return bullets;
}
