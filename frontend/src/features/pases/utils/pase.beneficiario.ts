/**
 * Commercial rules of the nominative rights of a pass — pure helpers over the
 * beneficiary payload.
 *
 * Dependency-free on purpose: the module stays importable without the
 * React/axios runtime so the rules can be verified deterministically.
 *
 * The rules MIRROR the backend:
 *   - the slots are IMMUTABLE: a revoked slot is consumed forever and the
 *     free slots never grow back;
 *   - the free slots are the LOWEST free ones: `1..cantidad_pases` minus the
 *     slots that are already used;
 *   - a right is NEVER transferred: a revoked person cannot be reused in the
 *     same batch.
 */

import type {
  PaseBeneficiarioAuditado,
  PaseConteosBeneficiarios,
} from "../schemas/pase.beneficiario.schema";
import type { PersonaResuelta } from "../schemas/persona.schema";

/** State of an ACTIVE right — backend `EstadoPaseBeneficiarioChoices`. */
export const BENEFICIARIO_ACTIVA = "ACTIVA";

/** State of a REVOKED right — its slot is consumed forever. */
export const BENEFICIARIO_REVOCADA = "REVOCADA";

/** UI tone of the state of a right. */
export type PaseBeneficiarioTone = "activa" | "revocada";

/** Tone of the state of a right: an unknown state is rendered as revoked. */
export function paseBeneficiarioTone(estado: string): PaseBeneficiarioTone {
  return estado === BENEFICIARIO_ACTIVA ? "activa" : "revocada";
}

/** Label of the state of a right. */
export function paseBeneficiarioEstadoLabel(estado: string): string {
  return estado === BENEFICIARIO_ACTIVA ? "Activo" : "Revocado";
}

/**
 * The slots that are already consumed by the batch.
 *
 * The numbers come from the rights themselves: the slot of a REVOKED right is
 * consumed too, so it is reported as used.
 */
export function paseSlotsUsados(
  beneficiarios: PaseBeneficiarioAuditado[],
): number[] {
  return beneficiarios
    .map((beneficiario) => beneficiario.slot)
    .sort((a, b) => a - b);
}

/**
 * The slots that are still free, in ascending order.
 *
 * The backend allocates the LOWEST free ones, so the browser shows exactly the
 * numbers the server will use.
 */
export function paseSlotsLibres(
  cantidadPases: number,
  beneficiarios: PaseBeneficiarioAuditado[],
): number[] {
  const usados = new Set(paseSlotsUsados(beneficiarios));
  const libres: number[] = [];

  for (let slot = 1; slot <= cantidadPases; slot += 1) {
    if (!usados.has(slot)) libres.push(slot);
  }

  return libres;
}

/** The rights that are still active. */
export function paseBeneficiariosActivos(
  beneficiarios: PaseBeneficiarioAuditado[],
): PaseBeneficiarioAuditado[] {
  return beneficiarios.filter(
    (beneficiario) => beneficiario.estado === BENEFICIARIO_ACTIVA,
  );
}

/**
 * The summary of the immutable slot accounting.
 *
 * The numbers come from the backend; the browser only groups them.
 */
export interface PaseSlotsResumen {
  /** Number of passes of the batch. */
  total: number;
  /** Active rights. */
  activos: number;
  /** Revoked rights (their slot is consumed forever). */
  revocados: number;
  /** Slots consumed. */
  usados: number;
  /** Slots still free. */
  disponibles: number;
}

/** The summary of the slot accounting of a batch. */
export function paseSlotsResumen(
  conteos: PaseConteosBeneficiarios,
): PaseSlotsResumen {
  return {
    total: conteos.cantidad_pases,
    activos: conteos.activos,
    revocados: conteos.revocados,
    usados: conteos.slots_usados,
    disponibles: conteos.slots_disponibles,
  };
}

/**
 * Whether a selection of persons fits the free slots.
 *
 * The server is the authority (it revalidates under the lock of the batch),
 * but the browser refuses an obvious excess instead of sending it.
 */
export function pasePuedeAsignar(
  conteos: PaseConteosBeneficiarios,
  seleccion: number,
): boolean {
  if (seleccion <= 0) return false;
  return seleccion <= conteos.slots_disponibles;
}

/**
 * Whether the buyer can still assign somebody.
 *
 * A batch with no free slot is closed: the slots are immutable and a revoked
 * slot never comes back.
 */
export function paseAsignacionAbierta(
  conteos: PaseConteosBeneficiarios,
): boolean {
  return conteos.slots_disponibles > 0;
}

/**
 * The label of the person that holds a right.
 *
 * The name is the one the backend reported; the browser never composes a
 * name out of free text.
 */
export function pasePersonaNombre(
  beneficiario: PaseBeneficiarioAuditado,
): string {
  return beneficiario.nombre_completo || "Persona sin nombre";
}

// ── Selección de personas ────────────────────────────────────────────────────

/**
 * Whether the person is ALREADY in the selection.
 *
 * The exact lookup resolves one person at a time, so the UI refuses to add
 * the same person twice: the backend would treat it as an idempotent no-op.
 */
export function pasePersonaYaSeleccionada(
  personas: PersonaResuelta[],
  personaId: string,
): boolean {
  return personas.some((persona) => persona.persona_id === personaId);
}
