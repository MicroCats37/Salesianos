import type { ErrorAdmin } from "@/features/admin/operaciones/services/admin.service";

/**
 * The pure rules of the ADMINISTRATIVE PASSES.
 *
 * They are dependency-free on purpose: the module stays importable without
 * the React runtime so the rules can be verified deterministically.
 */

/** The state of a courtesy that the backend published as `ACTIVA`. */
export const CORTESIA_ACTIVA = "ACTIVA";

/** The state of a courtesy that the backend published as `REVOCADA`. */
export const CORTESIA_REVOCADA = "REVOCADA";

/**
 * The label of the state of a courtesy.
 *
 * The label is a PRESENTATION: the state itself is the one the presenter
 * published. An unknown state is printed verbatim instead of being guessed.
 */
export function cortesiaEstadoLabel(estado: string): string {
  if (estado === CORTESIA_ACTIVA) return "Activa";
  if (estado === CORTESIA_REVOCADA) return "Revocada";
  return estado;
}

/**
 * Whether a courtesy can still be revoked.
 *
 * Only an ACTIVE courtesy is revocable: the revocation of a revoked courtesy
 * is idempotent and answers `ya_revocado = true`, so the interface does not
 * offer an action that would change nothing.
 */
export function cortesiaEsRevocable(estado: string): boolean {
  return estado === CORTESIA_ACTIVA;
}

/**
 * The kind of a failure of the backend.
 *
 * The interface branches on the HTTP STATUS and NEVER on the machine code:
 * the catalogue of public codes is not closed.
 */
export type TipoFallo =
  | "conflicto"
  | "validacion"
  | "permiso"
  | "sesion"
  | "desconocido";

/** A failure, already translated into the language of the interface. */
export interface EstadoDeFallo {
  /** The kind of the failure. */
  tipo: TipoFallo;
  /** The title of the notice. */
  titulo: string;
  /** The public prose of the backend, printed verbatim. */
  mensaje: string;
}

/**
 * Turns a failure into the state that the interface draws.
 *
 * The prose of the backend is NEVER translated nor re-written: it is the
 * public message of the frozen catalogue and it is printed as it came.
 */
export function estadoDeFallo(error: unknown): EstadoDeFallo {
  const admin = error as Partial<ErrorAdmin> | undefined;
  const status = typeof admin?.status === "number" ? admin.status : undefined;
  const mensaje =
    error instanceof Error
      ? error.message
      : "No se pudo completar la operación.";

  if (status === 409) {
    return {
      tipo: "conflicto",
      titulo: "El servidor rechazó la operación",
      mensaje,
    };
  }

  if (status === 422) {
    return {
      tipo: "validacion",
      titulo: "El servidor encontró datos que hay que corregir",
      mensaje,
    };
  }

  if (status === 403) {
    return {
      tipo: "permiso",
      titulo: "No tienes permiso para esta operación",
      mensaje,
    };
  }

  if (status === 401) {
    return {
      tipo: "sesion",
      titulo: "Tu sesión no está vigente",
      mensaje,
    };
  }

  return {
    tipo: "desconocido",
    titulo: "No se pudo completar la operación",
    mensaje,
  };
}
