import type { AdminTone } from "@/features/admin/utils";

/**
 * State vocabularies of the `competencias` module — the CLIENT mirror of the
 * `TextChoices` of `modules.competencias.domain.constants`.
 *
 * Dependency-free on purpose: the module must stay importable without the
 * React/axios runtime so the mapping can be verified deterministically (same
 * pattern as `features/admin/utils/admin.estado.utils.ts`). That is also why
 * its only import is a TYPE, which disappears when the types are stripped.
 *
 * A state the UI does not know about is rendered NEUTRALLY (`slate`) and
 * keeps its raw value: the UI never invents a semantic it was not told.
 */

/** `EstadoCompetenciaChoices` — PLANIFICADA / EN_CURSO / FINALIZADA / CANCELADA. */
const ESTADO_COMPETENCIA_TONE: Record<string, AdminTone> = {
  PLANIFICADA: "blue",
  EN_CURSO: "amber",
  FINALIZADA: "emerald",
  CANCELADA: "slate",
};

const ESTADO_COMPETENCIA_LABEL: Record<string, string> = {
  PLANIFICADA: "Planificada",
  EN_CURSO: "En curso",
  FINALIZADA: "Finalizada",
  CANCELADA: "Cancelada",
};

/** `EstadoCompetenciaEquipoChoices` — ACTIVO / RETIRADO. */
const ESTADO_EQUIPO_COMPETENCIA_TONE: Record<string, AdminTone> = {
  ACTIVO: "emerald",
  RETIRADO: "slate",
};

const ESTADO_EQUIPO_COMPETENCIA_LABEL: Record<string, string> = {
  ACTIVO: "Activo",
  RETIRADO: "Retirado",
};

/** `EstadoRondaChoices` — ACTIVA / INVALIDADA. */
const ESTADO_RONDA_TONE: Record<string, AdminTone> = {
  ACTIVA: "emerald",
  INVALIDADA: "slate",
};

const ESTADO_RONDA_LABEL: Record<string, string> = {
  ACTIVA: "Activa",
  INVALIDADA: "Invalidada",
};

/** `EstadoEncuentroChoices` — the lifecycle of a single encounter. */
const ESTADO_ENCUENTRO_TONE: Record<string, AdminTone> = {
  BORRADOR: "slate",
  PROGRAMADO: "blue",
  EN_CURSO: "amber",
  SUSPENDIDO: "orange",
  FINALIZADO: "emerald",
  CANCELADO: "slate",
};

const ESTADO_ENCUENTRO_LABEL: Record<string, string> = {
  BORRADOR: "Borrador",
  PROGRAMADO: "Programado",
  EN_CURSO: "En curso",
  SUSPENDIDO: "Suspendido",
  FINALIZADO: "Finalizado",
  CANCELADO: "Cancelado",
};

function tono(mapa: Record<string, AdminTone>, valor: string): AdminTone {
  return mapa[valor] ?? "slate";
}

function etiqueta(
  mapa: Record<string, string>,
  valor: string | null | undefined,
): string {
  if (!valor) return "—";
  return mapa[valor] ?? valor;
}

/** Tone of the lifecycle state of a competition. */
export function estadoCompetenciaTone(estado: string): AdminTone {
  return tono(ESTADO_COMPETENCIA_TONE, estado);
}

/** Label of the lifecycle state of a competition. */
export function estadoCompetenciaLabel(estado: string): string {
  return etiqueta(ESTADO_COMPETENCIA_LABEL, estado);
}

/** Tone of the state of the participation of a team. */
export function estadoEquipoCompetenciaTone(estado: string): AdminTone {
  return tono(ESTADO_EQUIPO_COMPETENCIA_TONE, estado);
}

/** Label of the state of the participation of a team. */
export function estadoEquipoCompetenciaLabel(estado: string): string {
  return etiqueta(ESTADO_EQUIPO_COMPETENCIA_LABEL, estado);
}

/** Tone of the state of a round. */
export function estadoRondaTone(estado: string): AdminTone {
  return tono(ESTADO_RONDA_TONE, estado);
}

/** Label of the state of a round. */
export function estadoRondaLabel(estado: string): string {
  return etiqueta(ESTADO_RONDA_LABEL, estado);
}

/** Tone of the lifecycle state of an encounter. */
export function estadoEncuentroTone(estado: string): AdminTone {
  return tono(ESTADO_ENCUENTRO_TONE, estado);
}

/** Label of the lifecycle state of an encounter. */
export function estadoEncuentroLabel(estado: string): string {
  return etiqueta(ESTADO_ENCUENTRO_LABEL, estado);
}

/** Every state of a competition, in the order of its lifecycle. */
export const COMPETENCIA_ESTADOS = [
  "PLANIFICADA",
  "EN_CURSO",
  "FINALIZADA",
  "CANCELADA",
] as const;

/** Every state of an encounter, in the order of its lifecycle. */
export const ENCUENTRO_ESTADOS = [
  "BORRADOR",
  "PROGRAMADO",
  "EN_CURSO",
  "SUSPENDIDO",
  "FINALIZADO",
  "CANCELADO",
] as const;
