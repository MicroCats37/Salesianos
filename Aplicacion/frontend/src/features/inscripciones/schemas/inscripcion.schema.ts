import { z } from "zod";

/**
 * The exact mirror of the inscriptions of the TARGET backend.
 *
 * Backend: `Aplicacion/backend/modules/salesianos_fest/presentation/schemas/inscripcion_schemas.py`
 * (packet DOM-01, freeze `FREEZE-PS-1.0.0`).
 *
 * The wrappers are composed the way the backend composes them: identity,
 * general and specific. The mirror keeps the same blocks and the same field
 * names, so a drift between the presenter and the browser is a PARSE ERROR,
 * never a silently wrong field.
 */

/**
 * A reference to a record of the area (mirrors the `referencia` block).
 *
 * The band of a team and the cohort of a registration travel as a reference
 * and not as a flat list of columns: the server publishes the identity and
 * the name, and the browser prints both without deriving anything.
 */
export const referenciaEquipoSchema = z.object({
  id: z.string(),
  nombre: z.string(),
});

/**
 * The cohort of a registration (mirrors `PromocionOut`).
 *
 * It is the year that the visitor EXPLICITLY selected. The secondary cohort
 * of a fused registration (`fusion_promocion`) is DESCRIPTIVE metadata: it
 * never changes the band, the cupos, the payment, the team or the
 * eligibility.
 */
export const promocionInscripcionSchema = referenciaEquipoSchema.extend({
  /** The year of the cohort. */
  anio: z.number().int(),
});

export type PromocionInscripcion = z.infer<typeof promocionInscripcionSchema>;

/** A team of a registration (mirrors `EquipoOut`). */
export const equipoSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  disciplina_id: z.string(),
  disciplina_nombre: z.string(),
  nombre: z.string(),
  /**
   * The competitive band of the team, DERIVED by the server from the cohort
   * of its registration.
   *
   * The client NEVER sends it and NEVER derives it: it prints the band that
   * the server resolved (`RN-C02`, `QA-K01`).
   */
  categoria: referenciaEquipoSchema,
  /** `ACTIVO` or `RETIRADO`. */
  estado: z.string(),
});

export type Equipo = z.infer<typeof equipoSchema>;

/**
 * The detail of a registration (mirrors `InscripcionDetalleOut`).
 *
 * The FOUR counters are the answer of the server (`RN-I03`): the browser
 * prints them and NEVER subtracts them.
 */
export const inscripcionDetalleSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  edicion_id: z.string(),
  edicion_nombre: z.string(),
  responsable_id: z.string(),
  paquete_id: z.string(),
  paquete_nombre: z.string(),
  /** The cohort that the visitor selected when the registration was created. */
  promocion: promocionInscripcionSchema,
  /**
   * The secondary cohort of a fused registration.
   *
   * It is DESCRIPTIVE metadata: `null` when there is no fusion, and it never
   * changes the band, the cupos, the payment, the team or the eligibility.
   */
  fusion_promocion: promocionInscripcionSchema.nullable(),
  /** `CREADA` or `CANCELADA`. */
  estado: z.string(),
  referencia: z.string(),
  cupos_solicitados: z.number().int().nonnegative(),
  cupos_pagados: z.number().int().nonnegative(),
  cupos_asignados: z.number().int().nonnegative(),
  cupos_disponibles: z.number().int().nonnegative(),
  equipos: z.array(equipoSchema),
});

export type InscripcionDetalle = z.infer<typeof inscripcionDetalleSchema>;

/** The teams of a registration (mirrors `EquiposInscripcionOut`). */
export const equiposInscripcionSchema = z.object({
  inscripcion_id: z.string(),
  equipos: z.array(equipoSchema),
});

export type EquiposInscripcion = z.infer<typeof equiposInscripcionSchema>;

/**
 * The purchase that finances the registration (mirrors `CompraOut`).
 *
 * It is a PROJECTION of the purchase of `commerce`: this module is not its
 * owner and does not publish its whole model.
 *
 * `total` is a `Decimal` on the server and a STRING on the wire: the browser
 * prints it exactly as it arrives and never sums nor formats it.
 */
export const compraSchema = z.object({
  compra_id: z.string(),
  orden_pago_id: z.string(),
  /** The commercial state of the purchase: `PENDIENTE`, `PAGADA`, `CANCELADA`. */
  estado: z.string(),
  total: z.string(),
  /** The ISO-4217 code of the currency. */
  moneda: z.string(),
  /** Whether the pending purchase already existed and was reused. */
  reutilizada: z.boolean(),
});

export type Compra = z.infer<typeof compraSchema>;

/**
 * The answer of the alta of a registration (mirrors `InscripcionInicialOut`).
 *
 * `causa_operativa` is the CAUSE that the presenter publishes: why the
 * operation answered what it answered (`RN-A02`). The controller does not
 * decide it and neither does the browser.
 */
export const inscripcionInicialSchema = z.object({
  inscripcion: inscripcionDetalleSchema,
  compra: compraSchema,
  causa_operativa: z.string(),
});

export type InscripcionInicial = z.infer<typeof inscripcionInicialSchema>;

// ── Entradas ─────────────────────────────────────────────────────────────────

/**
 * A team declared in the alta (mirrors `EquipoIn`).
 *
 * The limits are the ones the server declares: the name is at least one
 * character and at most 160. They are a MIRROR of a declared limit, never a
 * rule of the browser.
 */
export const equipoInSchema = z.object({
  disciplina_id: z.string(),
  nombre: z.string().min(1).max(160),
});

export type EquipoIn = z.infer<typeof equipoInSchema>;

/**
 * The payload of the alta of a registration (mirrors `InscripcionInicialIn`).
 *
 * The responsible does NOT travel: the server resolves it from the
 * authenticated account (`RN-U04`). The price does NOT travel either: the
 * server resolves it against the catalogue in force (`RN-C02`).
 *
 * The number of teams a registration may declare is NOT bounded here on
 * purpose: the limit is a domain rule that the server declares and enforces,
 * and it answers 422 with its field error when it is exceeded.
 *
 * ## The cohort
 *
 * `promocion_id` travels because the visitor EXPLICITLY selects it: it is
 * the only input from which the server derives the competitive band of the
 * teams. The client does NOT send the band (`equipos[].categoria_id` does not
 * exist on the wire): the band is a SERVER-DERIVED fact.
 *
 * ## The quantity
 *
 * `cantidad` travels because it is the DECISION of the visitor: the number of
 * cupos that the registration buys. It is not a price and not a total: the
 * server resolves the money against the catalogue in force.
 */
export const inscripcionInicialInSchema = z.object({
  edicion_id: z.string(),
  paquete_id: z.string(),
  /** The cohort that the visitor selected. */
  promocion_id: z.string(),
  /** The number of cupos that the registration buys. */
  cantidad: z.number().int().min(1),
  /**
   * The secondary cohort of a fused registration.
   *
   * It is OPTIONAL and it is DESCRIPTIVE: it names the visible label of a
   * fused cohort and it never changes the band, the cupos, the payment, the
   * team or the eligibility.
   */
  fusion_promocion_id: z.string().nullable().optional(),
  /**
   * The version of the price that the quotation resolved.
   *
   * It is the CONCURRENCY TOKEN of the quotation and it travels ONLY when a
   * quotation exists. It is not a price: the server resolves the money again
   * and rejects the alta when the catalogue moved (`RN-C02`).
   */
  cotizacion_version: z.number().int().nullable().optional(),
  equipos: z.array(equipoInSchema).min(1),
});

export type InscripcionInicialIn = z.infer<typeof inscripcionInicialInSchema>;
