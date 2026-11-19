import { z } from "zod";

// ── Contract Schemas ───────────────────────────────────────────────────────────

/**
 * Package discipline detail — matches PaqueteDisciplinaOut backend schema.
 * Defined first so other schemas can reference it.
 */
export const PaqueteDisciplinaContractSchema = z.object({
  disciplina_id: z.string(),
  disciplina_nombre: z.string(),
  disciplina_sigla: z.string(),
  min_jugadores: z.number().int().nullable(),
  max_jugadores: z.number().int().nullable(),
});

export type PaqueteDisciplinaContract = z.infer<
  typeof PaqueteDisciplinaContractSchema
>;

/**
 * Package price detail — matches PaquetePrecioOut backend schema.
 */
export const PaquetePrecioContractSchema = z.object({
  etapa: z.enum(["PREVENTA", "REGULAR"]),
  precio_unitario: z.number(),
  vigente_desde: z.string(),
  vigente_hasta: z.string().nullable(),
});

export type PaquetePrecioContract = z.infer<typeof PaquetePrecioContractSchema>;

/**
 * Package benefit detail — matches PaqueteBeneficioOut backend schema.
 */
export const PaqueteBeneficioContractSchema = z.object({
  tipo: z.enum(["FIESTA", "BOX", "CERVEZA"]),
  cantidad: z.number().int().positive(),
  alcance: z.enum(["INDIVIDUAL", "GRUPAL"]),
  modo_calculo: z.enum(["POR_CUPO", "FIJO_INICIAL"]),
});

export type PaqueteBeneficioContract = z.infer<
  typeof PaqueteBeneficioContractSchema
>;

/**
 * Canonical package list contract — matches PaqueteListOut backend schema.
 * Used for package selection cards and the quotation card.
 *
 * Mirrors the PaquetePresenter contract 1:1 (section 2 of the inscripcion
 * target contract): the list endpoint returns `disciplinas[]` (with
 * min/max jugadores), `beneficios[]` and `precios[]` so the wizard
 * does NOT need to fetch detail after package selection.
 */
export const PaqueteListContractSchema = z.object({
  id: z.string(),
  evento_id: z.string(),
  nombre: z.string(),
  tipo: z.enum(["PACK", "DISCIPLINA"]),
  modo_disciplinas: z.enum(["FIJO", "ELEGIBLE"]), // CANONICAL — NOT inferred
  cantidad_disciplinas: z.number().int().min(1).max(3),
  cantidad_minima_compra: z.number().int().min(1), // renamed from cantidad_maxima_participantes
  cantidad_maxima_equipos: z.number().int().min(1),
  precio_preventa: z.number().nullable(),
  precio_regular: z.number().nullable(),
  precio_promocional: z.number().nullable().optional(), // present in detail but sometimes in list
  tiene_fiesta: z.boolean(),
  tiene_box: z.boolean(),
  tiene_cerveza: z.boolean(),
  disciplinas_resumen: z.array(z.string()), // ["F7M", "VOL", "BAS"]
  // Canonical: now REQUIRED per PaquetePresenter contract (section 2).
  // Backend always returns this array (empty when paquete has no disciplines).
  disciplinas: z.array(PaqueteDisciplinaContractSchema),
  // beneficios[] and precios[] are now included at list level for quotation card
  beneficios: z.array(PaqueteBeneficioContractSchema),
  precios: z.array(PaquetePrecioContractSchema),
  descripcion: z.string(),
  minimo_compra_inicial: z.number().int().optional(),
});

export type PaqueteListContract = z.infer<typeof PaqueteListContractSchema>;

/**
 * Canonical package detail contract — matches PaqueteDetailOut backend schema.
 * Used for wizard configuration (prices, benefits, disciplines with min/max).
 */
export const PaqueteDetailContractSchema = PaqueteListContractSchema.extend({
  descripcion: z.string(),
  precios: z.array(PaquetePrecioContractSchema),
  beneficios: z.array(PaqueteBeneficioContractSchema),
  disciplinas: z.array(PaqueteDisciplinaContractSchema),
  // Override: detail has minimo_compra_inicial explicitly
  minimo_compra_inicial: z.number().int().min(1),
});

export type PaqueteDetailContract = z.infer<typeof PaqueteDetailContractSchema>;

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Returns the display label for modo_disciplinas badge.
 */
export function getModoLabel(
  modo: PaqueteListContract["modo_disciplinas"],
): string {
  return modo === "ELEGIBLE" ? "Elegible" : "Fijo";
}

/**
 * Returns true if the package is ELEGIBLE mode.
 * Uses the canonical modo_disciplinas field — NOT cantidad_disciplinas.
 */
export function isElegible(paquete: PaqueteListContract): boolean {
  return paquete.modo_disciplinas === "ELEGIBLE";
}

/**
 * Returns the current price (preventa if available, else regular).
 */
export function getCurrentPrice(paquete: PaqueteListContract): number | null {
  return paquete.precio_preventa ?? paquete.precio_regular ?? null;
}

/**
 * Returns a formatted price string.
 */
export function formatPrice(precio: number | null): string {
  if (precio === null) return "—";
  return `S/${precio.toFixed(2)}`;
}

// ── Query Keys ────────────────────────────────────────────────────────────────

export const paqueteQueryKeys = {
  all: ["paquetes"] as const,
  list: () => [...paqueteQueryKeys.all, "list"] as const,
  detail: (id: string) => [...paqueteQueryKeys.all, "detail", id] as const,
} as const;
