import type { PaqueteCatalogo } from "../types/inscripcion.types";

/**
 * The presentation of the catalogue of packages.
 *
 * It is COPIED from the previous frontend (`frontend/src/components/paquetes/
 * paquete-copy.ts`) and adapted to the contract of the target backend:
 *
 * - the colours of the disciplines are TOKENS, never literals;
 * - the discipline is identified by its `slug` and its `nombre`, because the
 *   target backend publishes NO `sigla` (the frozen shape is rejected by
 *   `__tests__/inscripcion-mirrors.test.ts`);
 * - the amounts are printed exactly as the server sends them, and the
 *   browser NEVER multiplies a price by a quantity: the total is the answer
 *   of the quotation.
 */

export const DISCIPLINA_COLORS = {
  F7M: "var(--success)",
  F7F: "var(--accent)",
  VOL: "var(--warning)",
  BAS: "var(--brand-cyan)",
} as const;

export const DEFAULT_DISCIPLINA_COLOR = "var(--primary)";

export interface InclusionBullet {
  texto: string;
  destacado?: boolean;
}

/**
 * The key of a discipline for the colour and the glyph.
 *
 * The target backend publishes the `slug` and the `nombre` of the
 * discipline. The key is resolved from the slug when it already IS the
 * short code, and from the NAME when it is not: the mark of a discipline is
 * a drawing, never a business decision.
 */
export function claveDisciplina(disciplina: {
  slug?: string | null;
  nombre?: string | null;
}): keyof typeof DISCIPLINA_COLORS {
  const slug = (disciplina.slug ?? "").trim().toUpperCase();

  if (slug === "F7M" || slug === "F7F" || slug === "VOL" || slug === "BAS") {
    return slug;
  }

  const nombre = (disciplina.nombre ?? "").toLowerCase();

  if (nombre.includes("femenin") || nombre.includes("femenino")) return "F7F";
  if (nombre.includes("voley") || nombre.includes("voleibol")) return "VOL";
  if (nombre.includes("basquet") || nombre.includes("básquet")) return "BAS";

  return "F7M";
}

/**
 * The colour of a discipline.
 *
 * It is the colour of the institution, and the same discipline is always the
 * same colour: the visitor recognises the sport before it reads the name.
 */
export function getDisciplinaColor(clave: string | null | undefined): string {
  const normalizada = clave?.trim().toUpperCase();

  if (
    normalizada === "F7M" ||
    normalizada === "F7F" ||
    normalizada === "VOL" ||
    normalizada === "BAS"
  ) {
    return DISCIPLINA_COLORS[normalizada];
  }

  return DEFAULT_DISCIPLINA_COLOR;
}

/** The disciplines of a package, in the order the catalogue declares them. */
export function getDisciplinasOrdenadas(paquete: PaqueteCatalogo) {
  return [...paquete.disciplinas];
}

/** The discipline that gives the card its accent colour. */
export function getUltimaDisciplina(paquete: PaqueteCatalogo) {
  return getDisciplinasOrdenadas(paquete).at(-1) ?? null;
}

/** The accent colour of the card: the colour of its last discipline. */
export function getColorAcento(paquete: PaqueteCatalogo): string {
  const disciplina = getUltimaDisciplina(paquete);
  return disciplina
    ? getDisciplinaColor(claveDisciplina(disciplina))
    : DEFAULT_DISCIPLINA_COLOR;
}

/**
 * Whether the package includes ONE discipline or several.
 *
 * It is a VIEW grouping and not a business rule: it decides how the
 * catalogue is filtered on screen and nothing else. The price, the cupos, the
 * teams and the eligibility are the server's.
 */
export function esPaqueteDeVariasDisciplinas(
  paquete: PaqueteCatalogo,
): boolean {
  return getDisciplinasOrdenadas(paquete).length > 1;
}

/**
 * The unit of the price: a small package is sold by team and a big one by
 * promotion.
 *
 * It is the same rule that the previous frontend had, and it only changes
 * the WORD that accompanies the amount.
 */
export function getUnidadPrecio(
  paquete: PaqueteCatalogo,
): "equipo" | "promoción" {
  return paquete.minimo_compra_inicial <= 10 ? "equipo" : "promoción";
}

function unirNombres(nombres: string[]): string {
  if (nombres.length === 0) return "la disciplina incluida";
  if (nombres.length === 1) return nombres[0];
  if (nombres.length === 2) return `${nombres[0]} y ${nombres[1]}`;
  return `${nombres.slice(0, -1).join(", ")} y ${nombres.at(-1)}`;
}

/** The first line of the block "Incluye": what the registration covers. */
export function getTextoInscripcion(paquete: PaqueteCatalogo): string {
  const nombres = getDisciplinasOrdenadas(paquete).map(
    (disciplina) => disciplina.nombre,
  );

  if (nombres.length === 0) return "Inscripción a 1 disciplina.";
  if (nombres.length === 1) return `Inscripción a ${nombres[0]}.`;

  return `Inscripción a ${unirNombres(nombres)}.`;
}

/**
 * The bullets of the block "Incluye".
 *
 * They come from the BENEFITS that the catalogue declares, never from a flag
 * that the browser computes: the catalogue publishes what the package
 * offers and this only prints it.
 */
export function getInclusionBullets(
  paquete: PaqueteCatalogo,
): InclusionBullet[] {
  const bullets: InclusionBullet[] = [{ texto: getTextoInscripcion(paquete) }];

  bullets.push({
    texto: `${paquete.minimo_compra_inicial} integrantes como mínimo.`,
  });

  for (const beneficio of paquete.beneficios) {
    bullets.push({
      texto: `${beneficio.nombre} · ${beneficio.cantidad}`,
      destacado: beneficio.tipo === "FIJO_INICIAL",
    });
  }

  return bullets;
}
