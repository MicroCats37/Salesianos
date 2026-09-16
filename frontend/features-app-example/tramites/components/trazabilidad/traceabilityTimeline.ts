/**
 * traceabilityTimeline — pure time-range / state-segment builders.
 *
 * Contracts (audit F07/F08/F10):
 * - `buildLifecycleBounds` derives dataStart/dataEnd from real events only;
 *   `now` is included ONLY when an open period exists or the global state is
 *   still active. Closed trámites end at the last real event / fecha_cierre (F08).
 * - Padding is deterministic: 4% of the lifecycle, floored for hours-long
 *   trámites (10 min) and capped for long ones (3 days).
 * - `buildGlobalStateSegments` converts global transitions into contiguous
 *   segments from each change to the next one / closure / now (F10).
 * - Pure: no DOM, no React; `now` is injectable for deterministic tests.
 */

import type {
  AsignacionTrazabilidad,
  HistorialEstadoGlobalTrazabilidad,
  TimelineEvent,
} from "../../schemas/trazabilidad.schema";
import { solicitudEstadoLabel } from "./traceabilityLabels";

const MIN_MS = 60_000;
const HOUR_MS = 3_600_000;
const DAY_MS = 86_400_000;
const MONTH_MS = 30 * DAY_MS;

/** Floor padding so hours-long trámites stay readable. */
export const PAD_FLOOR_MS = 10 * MIN_MS;
/** Ceiling padding so long trámites don't blow up the canvas. */
export const PAD_CAP_MS = 3 * DAY_MS;
/** Fraction of the lifecycle used as padding (audit: 3-5%). */
export const PAD_RATIO = 0.04;

export interface LifecycleInput {
  historial_estados: HistorialEstadoGlobalTrazabilidad[];
  areas: AsignacionTrazabilidad[];
  timeline: TimelineEvent[];
  fecha_registro: string | null;
  fecha_cierre: string | null;
  estado: string | null;
  /** Injectable clock for deterministic tests; defaults to Date.now(). */
  now?: number;
}

export interface LifecycleBounds {
  dataStart: number | null;
  dataEnd: number | null;
  minBound: number | null;
  maxBound: number | null;
  hasOpenPeriod: boolean;
  now: number;
}

export interface SegmentBounds {
  dataStart: number | null;
  dataEnd: number | null;
  hasOpenPeriod: boolean;
}

export interface GlobalStateSegment {
  id: string;
  estado: string;
  label: string;
  start: number;
  end: number;
}

export interface ClampedRange {
  start: number;
  end: number;
}

/**
 * Clamp a requested visible window inside `[minBound, maxBound]` (audit F07).
 *
 * Contract:
 * - Preserves the requested visible duration whenever it fits.
 * - A window wider than the whole domain collapses to the full data range
 *   (max zoom-out is the lifecycle with padding; never empty years).
 * - Shifts the window inside the bounds (pan can never leave the domain).
 */
export function clampVisibleRange(
  requestedStart: number,
  requestedEnd: number,
  minBound: number,
  maxBound: number,
): ClampedRange {
  const avail = maxBound - minBound;
  if (avail <= 0) return { start: minBound, end: maxBound };
  const span = Math.max(requestedEnd - requestedStart, 0);
  if (span >= avail) return { start: minBound, end: maxBound };

  let start = Math.max(requestedStart, minBound);
  let end = start + span;
  if (end > maxBound) {
    end = maxBound;
    start = end - span;
  }
  return { start, end };
}

export type TimelineGranularity =
  | "seconds"
  | "minutes"
  | "hours"
  | "day"
  | "month";

function toMs(iso: string | null | undefined): number | null {
  if (iso == null) return null;
  const ms = Date.parse(iso);
  return Number.isNaN(ms) ? null : ms;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function isGlobalActive(estado: string | null): boolean {
  const u = (estado ?? "").toUpperCase();
  return u !== "" && u !== "FINALIZADA" && u !== "ANULADA";
}

function collectTimestamps(input: LifecycleInput): number[] {
  const points: number[] = [];
  const push = (iso: string | null | undefined): void => {
    const ms = toMs(iso);
    if (ms !== null) points.push(ms);
  };
  push(input.fecha_registro);
  push(input.fecha_cierre);
  for (const entry of input.historial_estados) {
    push(entry.fecha_cambio);
  }
  for (const area of input.areas) {
    push(area.fecha_incorporacion);
    for (const period of area.etapas) {
      push(period.fecha_inicio);
      push(period.fecha_fin);
      for (const participant of period.participantes) {
        push(participant.fecha_inicio);
        push(participant.fecha_fin);
      }
      for (const response of period.respuestas) {
        push(response.fecha_emision);
      }
      for (const change of period.historial_estados) {
        push(change.fecha_cambio);
      }
    }
  }
  for (const event of input.timeline) {
    push(event.timestamp);
  }
  return points;
}

export function buildLifecycleBounds(input: LifecycleInput): LifecycleBounds {
  const now = input.now ?? Date.now();
  const hasOpenPeriod =
    isGlobalActive(input.estado) ||
    input.areas.some((area) =>
      area.etapas.some((period) => period.fecha_fin == null),
    );

  const points = collectTimestamps(input);
  if (points.length === 0) {
    // No real events at all (and closed): no meaningful lifecycle to bound.
    if (!hasOpenPeriod) {
      return {
        dataStart: null,
        dataEnd: null,
        minBound: null,
        maxBound: null,
        hasOpenPeriod,
        now,
      };
    }
    // Open trámite with no events: bound to the injected clock.
    return {
      dataStart: now,
      dataEnd: now,
      minBound: now - PAD_FLOOR_MS,
      maxBound: now + PAD_FLOOR_MS,
      hasOpenPeriod,
      now,
    };
  }

  const dataStart = Math.min(...points);
  let dataEnd = Math.max(...points);
  if (hasOpenPeriod) {
    dataEnd = Math.max(dataEnd, now);
  }

  const span = Math.max(dataEnd - dataStart, 0);
  const pad = clamp(span * PAD_RATIO, PAD_FLOOR_MS, PAD_CAP_MS);

  return {
    dataStart,
    dataEnd,
    minBound: dataStart - pad,
    maxBound: dataEnd + pad,
    hasOpenPeriod,
    now,
  };
}

export function buildGlobalStateSegments(
  historial: HistorialEstadoGlobalTrazabilidad[],
  bounds: SegmentBounds,
  now?: number,
): GlobalStateSegment[] {
  const sorted = [...historial].sort(
    (a, b) => (toMs(a.fecha_cambio) ?? 0) - (toMs(b.fecha_cambio) ?? 0),
  );
  if (sorted.length === 0) return [];

  const nowMs = now ?? Date.now();
  const segments: GlobalStateSegment[] = [];

  for (let i = 0; i < sorted.length; i += 1) {
    const entry = sorted[i];
    const start = toMs(entry.fecha_cambio);
    if (start === null) continue;

    const isLast = i === sorted.length - 1;
    const nextStart = isLast ? null : toMs(sorted[i + 1].fecha_cambio);
    let end: number;
    if (nextStart !== null) {
      end = Math.max(nextStart, start);
    } else if (bounds.hasOpenPeriod) {
      end = Math.max(nowMs, start);
    } else {
      end = bounds.dataEnd !== null ? Math.max(bounds.dataEnd, start) : start;
    }

    segments.push({
      id: `segment-${i}`,
      estado: entry.estado_nuevo,
      label: solicitudEstadoLabel(entry.estado_nuevo),
      start,
      end,
    });
  }

  // Prologue: state before the first recorded change stays contiguous from
  // dataStart (e.g. REGISTRADA between fecha_registro and the first transition).
  const first = sorted[0];
  const firstStart = toMs(first.fecha_cambio);
  if (
    bounds.dataStart !== null &&
    firstStart !== null &&
    bounds.dataStart < firstStart
  ) {
    const prologueEstado = first.estado_anterior ?? first.estado_nuevo;
    segments.unshift({
      id: "segment-initial",
      estado: prologueEstado,
      label: solicitudEstadoLabel(prologueEstado),
      start: bounds.dataStart,
      end: firstStart,
    });
  }

  return segments;
}

/** Human Spanish duration between two instants; null end → "En curso". */
export function formatDuration(start: number, end: number | null): string {
  if (end === null) return "En curso";
  const ms = Math.max(end - start, 0);
  if (ms < MIN_MS) return "0 min";

  const months = Math.floor(ms / MONTH_MS);
  const days = Math.floor((ms % MONTH_MS) / DAY_MS);
  const hours = Math.floor((ms % DAY_MS) / HOUR_MS);
  const minutes = Math.floor((ms % HOUR_MS) / MIN_MS);

  const parts: string[] = [];
  if (months > 0) parts.push(`${months} ${months === 1 ? "mes" : "meses"}`);
  if (days > 0) parts.push(`${days} ${days === 1 ? "día" : "días"}`);
  if (hours > 0) parts.push(`${hours} h`);
  if (minutes > 0) parts.push(`${minutes} min`);
  return parts.length > 0 ? parts.join(" ") : "0 min";
}

const DATE_FORMATTER = new Intl.DateTimeFormat("es-PE", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});
const MONTH_FORMATTER = new Intl.DateTimeFormat("es-PE", {
  month: "short",
  year: "numeric",
});
const TIME_FORMATTER = new Intl.DateTimeFormat("es-PE", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});
const SECOND_FORMATTER = new Intl.DateTimeFormat("es-PE", {
  second: "2-digit",
});

/** Neutral es-PE date formatting for headers/tooltips. */
export function formatTimelineDate(
  ts: number,
  granularity: TimelineGranularity = "minutes",
): string {
  const date = new Date(ts);
  if (granularity === "day") return DATE_FORMATTER.format(date);
  if (granularity === "month") return MONTH_FORMATTER.format(date);
  const datePart = DATE_FORMATTER.format(date);
  const timePart = TIME_FORMATTER.format(date);
  if (granularity === "seconds") {
    return `${datePart}, ${timePart}:${SECOND_FORMATTER.format(date)}`;
  }
  // "minutes" and "hours" share minute-level precision.
  return `${datePart}, ${timePart}`;
}
