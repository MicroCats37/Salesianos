/**
 * Optimistic pricing for the package cards.
 *
 * The quotation endpoint is authoritative but asynchronous. While a request is
 * in flight the card must keep showing a total instead of an empty box, and
 * that total must not blink between "no price" and "server price".
 *
 * The rule: the last known unit price of the SAME package is reused to
 * project the total for the current quantity. The server answer replaces it
 * only when it confirms the exact package and quantity.
 *
 * This module is dependency-free on purpose so it can be unit tested without
 * the React/axios runtime.
 */

export interface CotizacionResumen {
  paquete_id: string;
  cantidad_cotizada: number;
  precio_unitario: number;
  total: number;
  estado: "ACTIVA" | "EXPIRADA";
}

export interface PrecioOptimistaParams {
  /** Last quotation received by the client, if any. */
  cotizacion: CotizacionResumen | null;
  /** Package the card renders. */
  paqueteId: string;
  /** Quantity currently selected for that package. */
  cantidad: number;
  /** Catalog preventa price — the fallback when there is no quote yet. */
  precioPreventa: number | null;
  /** Catalog regular price — the last resort fallback. */
  precioRegular: number | null;
}

export interface PrecioOptimista {
  /** Unit price used to project the total. */
  precioUnitario: number;
  /** Total to display right now. */
  total: number;
  /** Regular price × quantity — null when there is no discount to show. */
  totalRegular: number | null;
  /** True when the server already confirmed this exact package + quantity. */
  confirmada: boolean;
  /** True when a quote exists but belongs to another package or quantity. */
  desfasada: boolean;
}

export function precioOptimista({
  cotizacion,
  paqueteId,
  cantidad,
  precioPreventa,
  precioRegular,
}: PrecioOptimistaParams): PrecioOptimista {
  const precioLocal = precioPreventa ?? precioRegular ?? 0;
  const esDelPaquete = cotizacion?.paquete_id === paqueteId;

  const regular = (unitario: number) =>
    precioRegular != null && precioRegular > unitario
      ? precioRegular * cantidad
      : null;

  if (!esDelPaquete || !cotizacion) {
    return {
      precioUnitario: precioLocal,
      total: precioLocal * cantidad,
      totalRegular: regular(precioLocal),
      confirmada: false,
      desfasada: cotizacion != null,
    };
  }

  if (cotizacion.cantidad_cotizada === cantidad) {
    return {
      precioUnitario: cotizacion.precio_unitario,
      total: cotizacion.total,
      totalRegular: regular(cotizacion.precio_unitario),
      confirmada: true,
      desfasada: false,
    };
  }

  // Same package, different quantity: project with the quoted unit price so
  // consecutive increments stay stable while the new quote is in flight.
  return {
    precioUnitario: cotizacion.precio_unitario,
    total: cotizacion.precio_unitario * cantidad,
    totalRegular: regular(cotizacion.precio_unitario),
    confirmada: false,
    desfasada: true,
  };
}
