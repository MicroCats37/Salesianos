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

/** A team of a registration (mirrors `EquipoOut`). */
export const equipoSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  disciplina_id: z.string(),
  disciplina_nombre: z.string(),
  nombre: z.string(),
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
 * The number of teams is NOT bounded here on purpose: the limit is a domain
 * rule that the server declares and enforces, and it answers 422 with its
 * field error when it is exceeded.
 */
export const inscripcionInicialInSchema = z.object({
  edicion_id: z.string(),
  paquete_id: z.string(),
  equipos: z.array(equipoInSchema).min(1),
});

export type InscripcionInicialIn = z.infer<typeof inscripcionInicialInSchema>;
