/**
 * Commercial rules of a pass — pure helpers over the catalogue payload.
 *
 * Dependency-free on purpose: the module stays importable without the
 * React/axios runtime so the rules can be verified deterministically.
 *
 * The rules MIRROR the backend:
 *   - `CANTIDAD_MAXIMA_POR_COMPRA` (per-purchase cap of the batch).
 *   - `_es_vigente` (the validity window of a price row: the last day is
 *     INCLUSIVE).
 *   - the effective price is the first vigente row ordered by `etapa`, so the
 *     preventa stage wins over the regular one when both windows overlap.
 */

import type { PaseCatalogo, PasePrecio } from "../schemas/pase.schema";

/**
 * Maximum number of passes of ONE purchase.
 *
 * Mirrors the backend constant `CANTIDAD_MAXIMA_POR_COMPRA`: the server
 * rejects a bigger batch with `PaseCantidadInvalidaError`.
 */
export const PASE_CANTIDAD_MAXIMA_POR_COMPRA = 50;

/** Currency used when the backend does not report one. */
export const PASE_MONEDA_POR_DEFECTO = "PEN";

/**
 * The local calendar day of the browser — ISO date (YYYY-MM-DD).
 *
 * The backend resolves the price calendar with the date of the EVENT
 * (America/Lima), so the browser uses its own LOCAL day instead of the UTC
 * one: after 19:00 in Lima the UTC day is already the next day.
 */
export function paseHoyLocal(): string {
  const ahora = new Date();
  const mes = String(ahora.getMonth() + 1).padStart(2, "0");
  const dia = String(ahora.getDate()).padStart(2, "0");
  return `${ahora.getFullYear()}-${mes}-${dia}`;
}

/**
 * The effective unit price of the pass right now.
 *
 * The value comes from the backend (`precio_vigente`): the browser NEVER
 * recomputes the price of a sale, it only displays the authoritative one.
 */
export function pasePrecioUnitario(pase: PaseCatalogo): number | null {
  return pase.precio_vigente ?? null;
}

/**
 * The price row that is in force on the given day.
 *
 * The window of a row is INCLUSIVE on both ends, exactly like the backend
 * `_es_vigente`: the row is vigente while `vigente_desde <= hoy` and
 * `vigente_hasta` is `null` or `>= hoy`.
 *
 * The rows are ordered by `etapa`, so the preventa stage wins over the
 * regular one when both windows overlap — the same precedence the backend
 * applies to `precio_vigente`.
 *
 * @param hoy - ISO date (YYYY-MM-DD) the answer is computed for.
 */
export function paseEtapaVigente(
  pase: PaseCatalogo,
  hoy: string,
): PasePrecio | null {
  const vigentes = pase.precios
    .filter((precio) => {
      if (precio.vigente_desde > hoy) return false;
      if (precio.vigente_hasta !== null && precio.vigente_hasta < hoy) {
        return false;
      }
      return true;
    })
    .sort((a, b) => a.etapa.localeCompare(b.etapa));

  return vigentes[0] ?? null;
}

/**
 * The maximum quantity the browser accepts for this pass.
 *
 * The cap is the smaller of the per-purchase limit of the backend and the
 * inventory of the pass (`cantidad_maxima`, `0` means unlimited).
 */
export function paseCantidadLimite(pase: PaseCatalogo): number {
  if (pase.cantidad_maxima > 0) {
    return Math.min(PASE_CANTIDAD_MAXIMA_POR_COMPRA, pase.cantidad_maxima);
  }
  return PASE_CANTIDAD_MAXIMA_POR_COMPRA;
}

/**
 * The total of a batch at the effective unit price.
 *
 * `null` when no price is in force: without a price the batch CANNOT be
 * bought, so the browser never shows a total it cannot honour.
 */
export function paseTotal(pase: PaseCatalogo, cantidad: number): number | null {
  const unitario = pasePrecioUnitario(pase);
  if (unitario === null) return null;
  if (!Number.isFinite(cantidad) || cantidad <= 0) return null;
  return redondearMonto(unitario * cantidad);
}

/** Round a monetary amount to two decimals. */
export function redondearMonto(monto: number): number {
  return Math.round((monto + Number.EPSILON) * 100) / 100;
}

/**
 * Format a monetary amount for the UI.
 *
 * The amounts are shown as they come from the backend: the browser never
 * formats a value it did not receive.
 */
export function formatearMontoPase(
  monto: number | null | undefined,
  moneda: string = PASE_MONEDA_POR_DEFECTO,
): string {
  if (monto === null || monto === undefined || !Number.isFinite(monto)) {
    return "—";
  }
  const simbolo = moneda === "PEN" ? "S/" : moneda;
  return `${simbolo} ${monto.toFixed(2)}`;
}

/**
 * Whether the pass can be bought right now.
 *
 * A pass is NOT purchasable when it is unpublished or when no price is in
 * force: the server refuses both cases, so the browser refuses them first.
 */
export function paseComprable(pase: PaseCatalogo): boolean {
  if (!pase.activo) return false;
  if (pase.precio_vigente === null) return false;
  return paseCantidadLimite(pase) > 0;
}
