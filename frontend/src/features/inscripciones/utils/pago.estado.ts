/**
 * Commercial payment state — pure mapping from the authoritative
 * `resumen_pago` payload to the UI decisions.
 *
 * Dependency-free on purpose: the module must stay importable without the
 * React/axios runtime so the mapping can be verified deterministically.
 *
 * Contract: `Inscripcion.estado` is ADMINISTRATIVE. It never describes the
 * commercial state and it is never used to infer it — the commercial state
 * lives in `resumen_pago` (backend presenter). The administrative state is
 * only consulted to block a cancelled/rejected inscription, exactly like the
 * registration steps card does.
 */

/** Minimal shape of a purchase summary needed to decide the payment state. */
export interface CompraPagoLike {
  /** `Compra.id`. */
  id: string;
  /** `Compra.estado`: PENDIENTE | PAGADA | CANCELADA. */
  estado: string;
  /** Payment order of the purchase — `null` when it has none yet. */
  orden_pago: { estado: string } | null;
}

/** Minimal shape of the commercial summary needed to decide the payment state. */
export interface ResumenPagoLike {
  /** Number of purchases still pending. */
  compras_pendientes: number;
  /** Purchase summaries. */
  compras: CompraPagoLike[];
}

/** Commercial states of a purchase. */
export const COMPRA_PENDIENTE = "PENDIENTE";
export const COMPRA_PAGADA = "PAGADA";
export const COMPRA_CANCELADA = "CANCELADA";

/** Commercial states of a payment order. */
export const ORDEN_PENDIENTE = "PENDIENTE";
export const ORDEN_PAGADA = "PAGADA";

/**
 * The purchase that can still be paid, if any.
 *
 * A purchase is payable when it is still PENDIENTE **and** its payment order
 * has not been paid yet. A purchase whose order is already paid is NOT
 * payable: the money is recorded and only the commercial activation is
 * pending, so the backend refuses a second charge.
 */
export function compraPagable(
  resumen: ResumenPagoLike | null | undefined,
): CompraPagoLike | null {
  if (!resumen) return null;
  return (
    resumen.compras.find(
      (compra) =>
        compra.estado === COMPRA_PENDIENTE &&
        compra.orden_pago?.estado !== ORDEN_PAGADA,
    ) ?? null
  );
}

/** Id of the purchase that can still be paid — `null` when there is none. */
export function compraPagableId(
  resumen: ResumenPagoLike | null | undefined,
): string | null {
  return compraPagable(resumen)?.id ?? null;
}

/**
 * Whether the payment was recorded but the commercial activation is still
 * pending.
 *
 * That is the state of a purchase that is still PENDIENTE while its payment
 * order is already PAGADA. The UI must communicate it instead of claiming a
 * completed payment.
 */
export function activacionPendiente(
  resumen: ResumenPagoLike | null | undefined,
): boolean {
  if (!resumen) return false;
  return resumen.compras.some(
    (compra) =>
      compra.estado === COMPRA_PENDIENTE &&
      compra.orden_pago?.estado === ORDEN_PAGADA,
  );
}

/**
 * Whether the administrative state closes the inscription to payment.
 *
 * Only a cancelled or rejected inscription is closed. Every other
 * administrative state (BORRADOR, RECIBIDA, EN_REVISION, OBSERVADA,
 * VALIDADA, CONFIRMADA) keeps the payment available when the commercial
 * summary says there is something payable.
 */
export function pagoBloqueadoPorEstado(estado: string): boolean {
  return estado === "CANCELADA" || estado === "RECHAZADA";
}

/**
 * Whether the payment action can be offered.
 *
 * The decision is commercial (there is a payable purchase) and it is only
 * vetoed by an inscription that was cancelled or rejected.
 */
export function puedeIniciarPago(
  resumen: ResumenPagoLike | null | undefined,
  estado: string,
): boolean {
  if (pagoBloqueadoPorEstado(estado)) return false;
  return compraPagable(resumen) !== null;
}
