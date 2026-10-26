/**
 * Commercial settlement state — pure interpretation of the backend
 * `settlement_status`.
 *
 * The browser NEVER triggers the commercial settlement: the backend settles the
 * purchase and allocates the rights when it verifies the payment. This module
 * only reads the state the backend reports so the UI never claims a completed
 * activation that did not happen.
 *
 * Dependency-free on purpose: it stays importable without the React/axios
 * runtime so the mapping can be verified deterministically.
 */

import type { SettlementStatus } from "../schemas/pago.schema";

/**
 * UI tone of a settlement state.
 *
 * - `completada` — the purchase is paid and its rights are allocated.
 * - `pendiente` — the payment is recorded but the activation is not complete.
 */
export type SettlementTone = "completada" | "pendiente";

/**
 * Map a settlement state to its UI tone.
 *
 * Only `SETTLED` means the commercial activation completed. Every other state
 * (`PENDING`, `NOT_APPLICABLE`, or an unknown value) keeps the conservative
 * tone: the UI must not claim a completed activation it cannot prove.
 */
export function settlementTone(
  status: SettlementStatus | null | undefined,
): SettlementTone {
  return status === "SETTLED" ? "completada" : "pendiente";
}
