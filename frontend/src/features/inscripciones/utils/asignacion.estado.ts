/**
 * Assignment eligibility — pure mapping from the backend candidate payload to
 * a UI state.
 *
 * Dependency-free on purpose: the module must stay importable without the
 * React/axios runtime so the mapping can be verified deterministically.
 *
 * The backend is the only authority: it decides whether a candidate may join
 * the target team (`asignable`) and reports the reasons with TYPED fields —
 * `ya_en_disciplina` (R11) and `estado_pool` (commercial). The UI never
 * parses a reason string to decide what to render.
 *
 * When the backend reports a candidate that HAS a paid cup, is NOT in the
 * target discipline and is still not assignable, the block comes from another
 * domain rule (e.g. the discipline modality vs. the persisted gender). The
 * frontend does NOT know which rule it is — it only knows the candidate is
 * blocked, and the backend reason is rendered verbatim next to the row.
 */

/** UI states of a candidate row inside the selector modal. */
export type AsignacionEstado =
  /** The candidate can be added to the target team right now. */
  | "asignable"
  /** The candidate already plays in the target discipline (R11). */
  | "ya_en_disciplina"
  /** The candidate has no paid cup — the commercial block. */
  | "sin_cupo"
  /**
   * The backend reports the candidate as not assignable for a reason OTHER
   * than the commercial block (it has a paid cup and does not play in the
   * target discipline yet). The reason is rendered verbatim from the backend.
   */
  | "no_asignable";

/**
 * Minimal shape needed to classify a candidate.
 *
 * Structurally compatible with `ElegibleOut` from the eligible service, without
 * importing it (keeps this module free of runtime dependencies).
 */
export interface CandidatoAsignacion {
  /** Backend verdict for the target team. */
  asignable: boolean;
  /** Typed R11 flag: the person already plays in the target discipline. */
  ya_en_disciplina: boolean;
  /** Backend-authoritative paid-cup eligibility. */
  tiene_cupo_activo: boolean;
}

/**
 * Derive the UI state of a candidate.
 *
 * The order matters: R11 (already in this discipline) wins over the commercial
 * block, because "you already play here" is the actionable reason — the cup
 * is fine, the discipline is not.
 *
 * A contradictory payload (`asignable` true but no paid cup) is treated as
 * blocked: a candidate without a confirmed cup must never be offered.
 */
export function asignacionEstadoDeCandidato(
  candidato: CandidatoAsignacion,
): AsignacionEstado {
  if (candidato.ya_en_disciplina) return "ya_en_disciplina";
  if (candidato.asignable && candidato.tiene_cupo_activo) return "asignable";
  if (!candidato.tiene_cupo_activo) return "sin_cupo";
  // The backend said no and the cup is fine: the block is a domain rule.
  return "no_asignable";
}

/**
 * Whether a candidate row can be selected.
 *
 * Only the `asignable` state is selectable — every other state is rendered as
 * a disabled row with the backend-provided reason.
 */
export function candidatoEsSeleccionable(
  candidato: CandidatoAsignacion,
): boolean {
  return asignacionEstadoDeCandidato(candidato) === "asignable";
}
