/**
 * graphStatus — semantic status classification + visual encoding for the graph.
 * Never color-only: each status also differs by border, shape, opacity or icon.
 */
import type { PeriodoTrazabilidad } from "../../schemas/trazabilidad.schema";

export type GraphStatus = "active" | "pending" | "closed" | "risk";

export function classifyState(estado: string | null | undefined): GraphStatus {
  const u = (estado ?? "").toUpperCase();
  if (
    u.includes("CANCELAD") ||
    u.includes("RECHAZAD") ||
    u.includes("ERRONEA") ||
    u.includes("BLOQUEAD") ||
    u.includes("ERROR")
  ) {
    return "risk";
  }
  if (
    u.includes("FINALIZAD") ||
    u.includes("CERRAD") ||
    u.includes("DESCARTAD")
  ) {
    return "closed";
  }
  if (
    u.includes("ACTIVO") ||
    u.includes("EN_GESTION") ||
    u.includes("GESTION") ||
    u.includes("PROCESO")
  ) {
    return "active";
  }
  return "pending";
}

export function classifyPeriod(period: PeriodoTrazabilidad): GraphStatus {
  return classifyState(period.estado);
}

export function classifyEvent(event: {
  tipo: string;
  event_estado_nuevo: string | null;
}): GraphStatus {
  return classifyState(`${event.tipo} ${event.event_estado_nuevo ?? ""}`);
}

/**
 * Semantic ordering for same-timestamp clusters: state changes first, then
 * participant/assignment, then formal responses, then the rest. Stable by
 * original payload order on ties.
 */
export function eventPriority(tipo: string): number {
  const u = tipo.toUpperCase();
  if (u.includes("ESTADO")) return 0;
  if (
    u.includes("PARTICIPANT") ||
    u.includes("ASIGNACION") ||
    u.includes("ALTA") ||
    u.includes("RETIRO")
  ) {
    return 1;
  }
  if (
    u.includes("RESPUESTA") ||
    u.includes("CONFORMIDAD") ||
    u.includes("OBSERVACION")
  ) {
    return 2;
  }
  return 3;
}

export const STATUS_BAR_CLASSES: Record<GraphStatus, string> = {
  active: "border-primary/60 bg-primary/10 text-foreground",
  pending: "border-border bg-muted text-muted-foreground",
  closed: "border-border bg-muted/50 text-muted-foreground",
  risk: "border-destructive/60 bg-destructive/10 text-destructive",
};

export const STATUS_DOT_CLASSES: Record<GraphStatus, string> = {
  active: "border-primary bg-primary",
  pending: "border-border bg-muted-foreground",
  closed: "border-border bg-muted-foreground/40",
  risk: "border-destructive bg-destructive",
};

export const STATUS_LABEL_CLASSES: Record<GraphStatus, string> = {
  active: "text-primary",
  pending: "text-foreground",
  closed: "text-muted-foreground",
  risk: "text-destructive",
};
