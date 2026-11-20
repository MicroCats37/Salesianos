import { z } from "zod";

import { compraSchema } from "./inscripcion.schema";

/**
 * The exact mirror of the purchase of EXTRA cupos.
 *
 * Backend: `Aplicacion/backend/modules/salesianos_fest/presentation/schemas/compra_cupos_schemas.py`
 * (packet DOM-02, freeze `FREEZE-PS-1.0.0` · `FREEZE-CM-1.0.0`).
 *
 * The payload admits NO amount: the price is resolved by the server against
 * the catalogue in force (`RN-C02`). The quantity carries no range in the
 * schema either: the domain declares the limit and the server enforces it
 * with the stable code `CUPO_INVALIDO` (422).
 */

/** The payload of the purchase of extra cupos (mirrors `ComprarCuposIn`). */
export const comprarCuposInSchema = z.object({
  cantidad: z.number().int(),
});

export type ComprarCuposIn = z.infer<typeof comprarCuposInSchema>;

/**
 * The answer of the purchase of extra cupos (mirrors `CompraCreadaOut`).
 *
 * The amount, the currency and the reuse flag travel INSIDE `compra`: it is
 * the projection of the purchase of `commerce` and it is not duplicated.
 *
 * The capacity of the answer is the capacity of the registration, and the
 * cupos that were just bought are NOT paid yet: the capacity only changes
 * when the payment is activated (`RN-I02`).
 */
export const compraCreadaSchema = z.object({
  inscripcion_id: z.string(),
  compra: compraSchema,
  cupos_solicitados: z.number().int().positive(),
  cupos_pagados: z.number().int().nonnegative(),
  cupos_asignados: z.number().int().nonnegative(),
  cupos_disponibles: z.number().int().nonnegative(),
  /** The operational cause of the answer. The domain declares it. */
  causa_operativa: z.string(),
});

export type CompraCreada = z.infer<typeof compraCreadaSchema>;
