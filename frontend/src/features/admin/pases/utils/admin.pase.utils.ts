/**
 * Administrative rules of the party passes — pure helpers over the payloads of
 * the administration area.
 *
 * Dependency-free on purpose: the module must stay importable without the
 * React/axios runtime so the mapping can be verified deterministically.
 *
 * The rules MIRROR the backend:
 *   - a cancellation is NOT a monetary refund: it revokes rights and cancels
 *     the purchase, it never returns money;
 *   - a revoked right keeps its slot forever, so the counts of active and
 *     revoked rights are reported SEPARATELY;
 *   - the QR credential never travels in an administrative read.
 */

import type { AdminTone } from "@/features/admin/utils/admin.estado.utils";

/** State of an ACTIVE right — backend `EstadoPaseBeneficiarioChoices`. */
export const ADMIN_BENEFICIARIO_ACTIVA = "ACTIVA";

/** State of a REVOKED right — its slot is consumed forever. */
export const ADMIN_BENEFICIARIO_REVOCADA = "REVOCADA";

/** Tone of the state of a nominative right. */
export function adminBeneficiarioEstadoTone(estado: string): AdminTone {
  return estado === ADMIN_BENEFICIARIO_ACTIVA ? "emerald" : "red";
}

/** Label of the state of a nominative right. */
export function adminBeneficiarioEstadoLabel(estado: string): string {
  return estado === ADMIN_BENEFICIARIO_ACTIVA ? "Activo" : "Revocado";
}

/**
 * Whether a pass purchase can still be cancelled.
 *
 * A purchase that is already CANCELLED is closed: the operation is idempotent
 * on the server, but the administration does not offer the action twice.
 */
export function adminPaseCancelable(
  estadoCompra: string,
  estadoOrden: string | null | undefined,
): boolean {
  if (estadoCompra === "CANCELADA") return false;
  if (estadoOrden === "CANCELADA") return false;
  if (estadoOrden === "VENCIDA") return false;
  return true;
}

/**
 * The counts of the nominative rights, reported SEPARATELY.
 *
 * The active rights still grant access; the revoked ones keep their slot
 * forever. The text NEVER merges them into a single number.
 */
export function adminPaseConteosTexto(
  activos: number,
  revocados: number,
): string {
  return `${activos} activo(s) · ${revocados} revocado(s)`;
}

/**
 * The warning of the cancellation: it is NOT a refund.
 *
 * The administration never implies that money was returned.
 */
export function adminPaseCancelacionAviso(): string {
  return "La cancelación no devuelve dinero: cancela la compra y revoca los pases ya entregados.";
}
