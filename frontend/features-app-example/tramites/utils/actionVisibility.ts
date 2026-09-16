/**
 * Action visibility helpers — presentation-only UX gating.
 * These checks decide whether an operational action is RENDERED at all.
 * They are NOT authorization/security: no Guardian rule, permission or
 * backend restriction is added by using them.
 */

export function normalizeId(id: string): string {
  return id.toLowerCase();
}

export function isUserAssignedToArea(
  areaId: string,
  userAreaIds: Set<string>,
): boolean {
  return userAreaIds.has(normalizeId(areaId));
}

export interface ActiveParticipantLike {
  usuario_id: string;
  activo: boolean;
}

/**
 * True when the current user is an ACTIVE participant in the given period.
 * Shared by the detail page (detail contract participants) and the
 * TraceabilityInspector (traceability contract period participants);
 * both expose usuario_id + activo.
 */
export function isActiveParticipantInPeriod(
  participantes: ActiveParticipantLike[] | undefined,
  currentUserId: string | null,
): boolean {
  if (!currentUserId) return false;
  return (participantes ?? []).some(
    (p) => normalizeId(p.usuario_id) === normalizeId(currentUserId) && p.activo,
  );
}

const CLOSED_PERIOD_STATES = new Set(["CERRADO", "FINALIZADO", "CANCELADO"]);

/**
 * A period is operable when it is not closed/finalized/cancelled.
 * Mirrors the gates used by the detail page and PeriodoOperacionesMenu.
 */
export function isPeriodOperable(estado: string | null | undefined): boolean {
  return !estado || !CLOSED_PERIOD_STATES.has(estado);
}
