import { z } from "zod";

/**
 * The mirror of the QUOTATION of the target backend.
 *
 * Backend: `Aplicacion/backend/modules/salesianos_fest/presentation/schemas/`
 * (the quotation of the package and the quantity, restored by
 * `restore-registration-promotion-catalog-flow`).
 *
 * ## What a quotation is
 *
 * It is a STATELESS calculation of the server against the catalogue in force
 * (`RN-C02`): the visitor asks for a package and a quantity and the server
 * answers with the unit price, the total and the version of the price.
 *
 * It is NOT persisted: it belongs to the wizard session and it travels back
 * to the server as a CONCURRENCY TOKEN (`version`), so that the server can
 * detect that the price moved between the quotation and the alta.
 *
 * ## What the browser NEVER does with it
 *
 * The browser NEVER sends the unit price or the total back as the truth of
 * the purchase: it sends the QUANTITY (the decision of the visitor) and, when
 * a quotation exists, its `version` (the token of the concurrency check). The
 * price is resolved again by the server when the registration is created
 * (`RN-C02`).
 *
 * ## The money is a STRING
 *
 * Same rule as the catalogue (`schemas/catalogo.schema.ts`): a `Decimal` on
 * the server is a JSON STRING on the wire. The browser prints the amount
 * exactly as it arrives and never sums nor formats it.
 */

/** The request of a quotation (mirrors `CotizacionIn`). */
export const cotizacionInSchema = z.object({
  /** The package that is quoted. */
  paquete_id: z.string().min(1, "paquete_id requerido"),
  /** The number of cupos that are quoted. */
  cantidad: z.number().int().min(1, "La cantidad debe ser al menos 1"),
});

export type CotizacionIn = z.infer<typeof cotizacionInSchema>;

/** The answer of the server (mirrors `CotizacionOut`). */
export const cotizacionOutSchema = z.object({
  /** The package that was quoted. */
  paquete_id: z.string(),
  /** The name of the package that was quoted. */
  paquete_nombre: z.string(),
  /** The commercial minimum of the package, as the catalogue declares it. */
  minimo_cantidad: z.number().int().positive(),
  /** The quantity that was quoted. */
  cantidad_cotizada: z.number().int().positive(),
  /** The unit price in force, as the server sends it. */
  precio_unitario: z.string(),
  /** The total of the quotation, as the server sends it. */
  total: z.string(),
  /** The ISO-4217 code of the currency. */
  moneda: z.string(),
  /**
   * The version of the price that the quotation resolved.
   *
   * It is the CONCURRENCY TOKEN: it travels back to the server when the
   * registration is created so that a price that moved in between is
   * detected instead of silently accepted.
   */
  version: z.number().int(),
  /** `ACTIVA` or `EXPIRADA`. */
  estado: z.string(),
  /** The instant until which the quotation is valid. */
  validez_hasta: z.string(),
});

export type Cotizacion = z.infer<typeof cotizacionOutSchema>;
