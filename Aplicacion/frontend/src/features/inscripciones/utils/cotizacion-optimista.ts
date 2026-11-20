import type { Cotizacion } from "../schemas/cotizacion.schema";

/**
 * The optimistic price of a package card.
 *
 * It is COPIED from the previous frontend
 * (`frontend/src/features/inscripciones/utils/cotizacion.optimista.ts`) and
 * adapted to the contract of the target backend, where the amounts are
 * STRINGS (the backend serializes its Decimal that way).
 *
 * The rule of the previous frontend is kept: the card ALWAYS shows a total.
 * While the request travels, the total is a PROJECTION of the last price the
 * server confirmed for THAT package, and the number never blinks between
 * "no price" and "server price".
 *
 * The projection is a DISPLAY: it never travels to the server. The server
 * resolves the money again when the registration is created.
 */

export interface PrecioOptimista {
  /** The unit price used to project the total. */
  precioUnitario: number;
  /** The total to show right now. */
  total: number;
  /** True when the server confirmed THIS package and THIS quantity. */
  confirmada: boolean;
  /** True when a quotation exists but belongs to another quantity. */
  desfasada: boolean;
}

export interface PrecioOptimistaParams {
  /** The last quotation that the server answered, if any. */
  cotizacion: Cotizacion | null;
  /** The package the card renders. */
  paqueteId: string;
  /** The quantity that is selected for that package. */
  cantidad: number;
  /** The unit price that the CATALOGUE declares. */
  precioUnitarioCatalogo: number | null;
}

/**
 * The amount of the catalogue, as a number.
 *
 * The wire sends a string; the browser prints it as it arrives and only
 * multiplies it for the projection of the card.
 */
export function precioNumerico(monto: string | number | null | undefined) {
  if (monto === null || monto === undefined || monto === "") return null;

  const valor = Number(monto);
  return Number.isFinite(valor) ? valor : null;
}

export function precioOptimista({
  cotizacion,
  paqueteId,
  cantidad,
  precioUnitarioCatalogo,
}: PrecioOptimistaParams): PrecioOptimista {
  const precioLocal = precioUnitarioCatalogo ?? 0;
  const esDelPaquete = cotizacion?.paquete_id === paqueteId;

  if (!esDelPaquete || !cotizacion) {
    return {
      precioUnitario: precioLocal,
      total: precioLocal * cantidad,
      confirmada: false,
      desfasada: cotizacion !== null,
    };
  }

  const unitarioCotizado =
    precioNumerico(cotizacion.precio_unitario) ?? precioLocal;

  if (cotizacion.cantidad_cotizada === cantidad) {
    return {
      precioUnitario: unitarioCotizado,
      total: precioNumerico(cotizacion.total) ?? unitarioCotizado * cantidad,
      confirmada: true,
      desfasada: false,
    };
  }

  /*
   * The same package with ANOTHER quantity: the total is projected with the
   * unit price that the server already confirmed, so the consecutive
   * increments stay stable while the new quotation travels.
   */
  return {
    precioUnitario: unitarioCotizado,
    total: unitarioCotizado * cantidad,
    confirmada: false,
    desfasada: true,
  };
}
