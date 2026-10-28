/**
 * Commercial state of a pass purchase — pure interpretation of the state the
 * backend reports.
 *
 * Dependency-free on purpose: the module stays importable without the
 * React/axios runtime so the mapping can be verified deterministically.
 *
 * The states come from the backend:
 *   - `Compra.estado` (EstadoCompraChoices): PENDIENTE | PAGADA | CANCELADA.
 *   - `OrdenPago.estado` (OrdenPagoStatus): PENDIENTE | PAGADA | CANCELADA |
 *     VENCIDA.
 *
 * The UI must never claim a completed activation it cannot prove: only a
 * PAGADA purchase is presented as paid.
 */

import type { PaseOrigenPago } from "../schemas/pase.schema";

/** Commercial states of a purchase — backend `EstadoCompraChoices`. */
export const COMPRA_PENDIENTE = "PENDIENTE";
export const COMPRA_PAGADA = "PAGADA";
export const COMPRA_CANCELADA = "CANCELADA";

/** Commercial states of a payment order — backend `OrdenPagoStatus`. */
export const ORDEN_PENDIENTE = "PENDIENTE";
export const ORDEN_PAGADA = "PAGADA";
export const ORDEN_CANCELADA = "CANCELADA";
export const ORDEN_VENCIDA = "VENCIDA";

/** Minimal shape of the commercial state needed to decide the tone. */
export interface PaseEstadoLike {
  /** `Compra.estado` of the purchase. */
  estado_compra: string;
  /** `OrdenPago.estado` of the order that funds the purchase. */
  estado_orden: string;
}

/** UI tone of the commercial state of a purchase. */
export type PaseEstadoTone = "pagada" | "pendiente" | "vencida" | "cancelada";

/**
 * The tone of the commercial state of a purchase.
 *
 * The tone is decided by the WORST of the two states: a paid order of a
 * cancelled purchase is a cancelled purchase.
 */
export function paseEstadoTone(estado: PaseEstadoLike): PaseEstadoTone {
  if (estado.estado_compra === COMPRA_CANCELADA) return "cancelada";
  if (estado.estado_orden === ORDEN_CANCELADA) return "cancelada";
  if (estado.estado_orden === ORDEN_VENCIDA) return "vencida";
  if (estado.estado_compra === COMPRA_PAGADA) return "pagada";
  return "pendiente";
}

/**
 * Whether the purchase can still be paid.
 *
 * A purchase is payable while it is PENDIENTE and its order has not been paid
 * yet: an order that is already paid is NOT payable again — the money is
 * recorded and only the commercial activation may be pending.
 */
export function paseCompraPagable(estado: PaseEstadoLike): boolean {
  return (
    estado.estado_compra === COMPRA_PENDIENTE &&
    estado.estado_orden === ORDEN_PENDIENTE
  );
}

/**
 * Whether the purchase is PAID.
 *
 * Only a PAGADA purchase grants rights: the nominative rights of a batch are
 * assigned over a paid pass.
 */
export function paseCompraPagada(estado: PaseEstadoLike): boolean {
  return estado.estado_compra === COMPRA_PAGADA;
}

/**
 * Whether the payment was recorded but the commercial activation is pending.
 *
 * That is the state of a purchase that is still PENDIENTE while its order is
 * already PAGADA. The UI must communicate it instead of claiming a completed
 * payment.
 */
export function paseActivacionPendiente(estado: PaseEstadoLike): boolean {
  return (
    estado.estado_compra === COMPRA_PENDIENTE &&
    estado.estado_orden === ORDEN_PAGADA
  );
}

/** Whether the purchase was cancelled. */
export function paseCompraCancelada(estado: PaseEstadoLike): boolean {
  return (
    estado.estado_compra === COMPRA_CANCELADA ||
    estado.estado_orden === ORDEN_CANCELADA
  );
}

/**
 * The next step the buyer must follow.
 *
 * The message is the one the result panel shows: it states what happened and
 * what to do next, without ever promising an activation that the backend did
 * not confirm.
 */
export function paseSiguientePaso(estado: PaseEstadoLike): string {
  if (paseActivacionPendiente(estado)) {
    return "El pago se registró, pero la activación comercial sigue pendiente. El backend la cerrará en cuanto pueda confirmar el pago.";
  }

  switch (paseEstadoTone(estado)) {
    case "pagada":
      return "Tu pase está pagado. El siguiente paso es asignar las personas que lo usarán.";
    case "vencida":
      return "La orden de pago venció. Vuelve a comprar el pase para generar una orden nueva.";
    case "cancelada":
      return "La compra fue cancelada y sus pases quedaron liberados. Puedes comprar el pase de nuevo.";
    default:
      return "Completa el pago para activar tu pase.";
  }
}

/**
 * The label of the origin of the payment.
 *
 * The origin is DERIVED by the backend from the payment evidence: it is never
 * a field the buyer sends nor the provider imposes.
 */
export function paseOrigenPagoLabel(
  origen: PaseOrigenPago | null | undefined,
): string {
  switch (origen) {
    case "IZIPAY":
      return "Pago verificado con la pasarela";
    case "MANUAL":
      return "Pago verificado por la administración";
    case "SIN_PAGO":
      return "Sin pago verificado";
    default:
      return "Origen del pago desconocido";
  }
}
