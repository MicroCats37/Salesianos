/**
 * Pool eligibility — pure mapping from the backend pool payload to a UI state.
 *
 * Dependency-free on purpose: the module must stay importable without the
 * React/axios runtime so the mapping can be verified deterministically.
 *
 * The backend is the only authority: it decides whether a pre-registered
 * person holds a paid cup and, when it does not, WHY. The UI never re-derives
 * the commercial state — it renders the discriminator it received.
 */

/** UI eligibility states rendered by the pool card. */
export type PoolEstado =
  | "listo"
  | "esperando_pago"
  | "sin_capacidad"
  | "cupo_por_asignar"
  | "bloqueado";

/**
 * Typed eligibility discriminator sent by the backend
 * (`PoolEntryOut.estado_pool`).
 *
 * - `LISTO` — the participant holds an ACTIVA paid cup.
 * - `ESPERANDO_PAGO` — the inscription has NO paid capacity yet: the
 *   participant waits for the payment of its cup.
 * - `SIN_CAPACIDAD` — the paid capacity is exhausted: the participant needs an
 *   amplification.
 * - `CUPO_POR_ASIGNAR` — the payment already exists and there is free paid
 *   capacity, but this participant has no cup assigned yet. It is NEVER
 *   "waiting for a payment".
 */
export const ESTADO_POOL_LISTO = "LISTO";
export const ESTADO_POOL_ESPERANDO_PAGO = "ESPERANDO_PAGO";
export const ESTADO_POOL_SIN_CAPACIDAD = "SIN_CAPACIDAD";
export const ESTADO_POOL_CUPO_POR_ASIGNAR = "CUPO_POR_ASIGNAR";

/**
 * Backend UI-safe blocked reasons (see `domain/constants.py`).
 *
 * They mirror the backend 1:1 and are used ONLY as a fallback for a backend
 * that does not send `estado_pool` yet — the discriminator always wins.
 */
export const MOTIVO_ESPERANDO_PAGO = "Esperando el pago del cupo";
export const MOTIVO_SIN_CAPACIDAD = "No hay cupos pagados disponibles";
export const MOTIVO_CUPO_POR_ASIGNAR = "Cupo pagado disponible sin asignar";

/**
 * Minimal shape needed to classify a pool entry.
 *
 * Structurally compatible with `PoolEntryOut` from the pool service, without
 * importing it (keeps this module free of runtime dependencies).
 */
export interface PoolEligibility {
  /** Backend-authoritative assignment eligibility. */
  tiene_cupo_activo: boolean;
  /** Typed eligibility discriminator. Absent on legacy backends. */
  estado_pool?: string | null;
  /** UI-safe blocked reason. `null` when the person is eligible. */
  motivo_bloqueo: string | null;
}

/**
 * Derive the UI state from a backend pool entry.
 *
 * - `tiene_cupo_activo` → `listo` (ready for a team).
 * - `estado_pool` decides every blocked state — the reason string is only a
 *   fallback, never the primary signal. A contradictory payload (`LISTO`
 *   without an active cup) is treated as blocked, never as assignable.
 *
 * Unknown values fall back to `bloqueado` — the safe state, because a
 * participant without a confirmed cup must never be offered for assignment.
 */
export function poolEstadoDeEntrada(entry: PoolEligibility): PoolEstado {
  if (entry.tiene_cupo_activo) return "listo";

  switch (entry.estado_pool) {
    case ESTADO_POOL_ESPERANDO_PAGO:
      return "esperando_pago";
    case ESTADO_POOL_SIN_CAPACIDAD:
      return "sin_capacidad";
    case ESTADO_POOL_CUPO_POR_ASIGNAR:
      return "cupo_por_asignar";
    default:
      break;
  }

  // Legacy backend: no discriminator, only the reason string.
  if (entry.motivo_bloqueo === MOTIVO_ESPERANDO_PAGO) return "esperando_pago";
  if (entry.motivo_bloqueo === MOTIVO_SIN_CAPACIDAD) return "sin_capacidad";
  if (entry.motivo_bloqueo === MOTIVO_CUPO_POR_ASIGNAR)
    return "cupo_por_asignar";

  return "bloqueado";
}

/**
 * Whether the card may offer its assignment action.
 *
 * The action only appears for entries the backend marked eligible, and never
 * when there is no team to assign to (no target at all).
 */
export function poolEsAsignable(
  entry: PoolEligibility,
  sinDestino = false,
): boolean {
  return !sinDestino && poolEstadoDeEntrada(entry) === "listo";
}
