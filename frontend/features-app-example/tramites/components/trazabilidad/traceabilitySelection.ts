/**
 * traceabilitySelection — the SINGLE selection model shared by calendar, flow
 * and inspector (audit G, F12/F17; work unit U7).
 *
 * Contract:
 * - One discriminated selection derived from STABLE IDs (`global-state`,
 *   `area`, `period`, `participant-event`, `response`, `node`). No parallel
 *   copies like `flowArea/flowPeriod/flowNodeData`; calendar, flow and
 *   inspector all resolve their data from these IDs.
 * - `global-state` uses the transition's ISO timestamp as its stable anchor:
 *   a global state transition is unique per `fecha_cambio`, and both the
 *   timeline and the flow resolve it deterministically.
 * - `parseFlowNodeId` decodes the builder's composite node ids. UUIDs contain
 *   dashes, so parsing is regex-based, never `split("-")`.
 * - `toFlowSelection` maps the unified selection to the flow's own
 *   `SolicitudFlowSelection` (highlight + center only — never rebuilds the
 *   graph). Global-state and participant lookups mirror `buildSolicitudFlow`
 *   so node ids stay identical.
 * - `resolveSelection` materializes entities for the compact inspector.
 * - Pure: no DOM, no React, no Date.now(); same input → same output.
 */

import type {
  AsignacionTrazabilidad,
  HistorialEstadoGlobalTrazabilidad,
  ParticipanteTrazabilidad,
  PeriodoTrazabilidad,
  RespuestaTrazabilidad,
  SolicitudTrazabilidad,
  TimelineEvent,
} from "../../schemas/trazabilidad.schema";
import type {
  FlowNodeKind,
  SolicitudGlobalContext,
} from "./buildSolicitudFlow";

// ── Flow highlight/center selection (shared by card flow and React Flow) ─────────

/**
 * Card-flow highlight + center contract. Mirrors the React Flow contract exactly —
 * same discriminated union, same field names. A `null` means no highlight.
 * Used by both the timeline-to-flow mapper (`toFlowSelection`) and the card
 * renderer to apply `data-selected` / dimming without rebuilding topology.
 */
export type SolicitudFlowSelection =
  | { type: "area"; areaId: string }
  | { type: "period"; areaId: string; periodId: string }
  | { type: "node"; nodeId: string }
  | null;

// ── Stable-ID selection ────────────────────────────────────────────────────────

export type TraceabilitySelection =
  | { type: "global-state"; stateId: string }
  | { type: "area"; areaId: string }
  | { type: "period"; areaId: string; periodId: string }
  | {
      type: "participant-event";
      areaId: string;
      periodId: string;
      participantUserId: string;
    }
  | { type: "response"; areaId: string; periodId: string; responseId: string }
  | { type: "node"; nodeId: string }
  | null;

// ── Resolved selection (entities materialized for the inspector) ───────────────

export type ResolvedTraceabilitySelection =
  | {
      type: "global-state";
      area: null;
      period: null;
      historial: HistorialEstadoGlobalTrazabilidad;
      event: TimelineEvent | null;
    }
  | { type: "area"; area: AsignacionTrazabilidad }
  | {
      type: "period";
      area: AsignacionTrazabilidad;
      period: PeriodoTrazabilidad;
    }
  | {
      type: "participant-event";
      area: AsignacionTrazabilidad;
      period: PeriodoTrazabilidad;
      participant: ParticipanteTrazabilidad;
    }
  | {
      type: "response";
      area: AsignacionTrazabilidad;
      period: PeriodoTrazabilidad;
      response: RespuestaTrazabilidad;
    }
  | {
      type: "node";
      kind: FlowNodeKind;
      label: string;
      timestamp: string;
      sublabel?: string;
      detail?: string;
    }
  | null;

// ── Helpers ────────────────────────────────────────────────────────────────────

function toMs(iso: string | null | undefined): number | null {
  if (iso == null) return null;
  const ms = Date.parse(iso);
  return Number.isNaN(ms) ? null : ms;
}

const UUID_SRC =
  "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}";
const RE_AREA = new RegExp(`^area-(${UUID_SRC})$`);
const RE_AREA_TERMINAL = new RegExp(`^area-(${UUID_SRC})-terminal$`);
const RE_PERIOD = new RegExp(`^area-(${UUID_SRC})-period-(${UUID_SRC})$`);
const RE_PERIOD_TERMINAL = new RegExp(
  `^area-(${UUID_SRC})-period-(${UUID_SRC})-terminal$`,
);
const RE_PARTICIPANT = new RegExp(
  `^area-(${UUID_SRC})-period-(${UUID_SRC})-participant-(${UUID_SRC})-\\d+(-out)?$`,
);
const RE_RESPONSE = new RegExp(
  `^area-(${UUID_SRC})-period-(${UUID_SRC})-response-(${UUID_SRC})$`,
);
const RE_STATE = new RegExp(
  `^area-(${UUID_SRC})-period-(${UUID_SRC})-state-\\d+$`,
);
const RE_GLOBAL_STATE = /^global-state-(\d+)$/;

export type ParsedFlowNode =
  | {
      kind: "global";
      nodeId: "global-start" | "global-merge" | "global-terminal";
    }
  | { kind: "global-state"; globalStateIndex: number }
  | { kind: "area"; areaId: string }
  | { kind: "area-terminal"; areaId: string }
  | { kind: "period"; areaId: string; periodId: string }
  | { kind: "period-terminal"; areaId: string; periodId: string }
  | {
      kind: "participant";
      areaId: string;
      periodId: string;
      participantUserId: string;
    }
  | { kind: "response"; areaId: string; periodId: string; responseId: string }
  | { kind: "state"; areaId: string; periodId: string }
  | null;

/** Decode a builder composite node id (regex-based; UUIDs contain dashes). */
export function parseFlowNodeId(nodeId: string): ParsedFlowNode {
  if (
    nodeId === "global-start" ||
    nodeId === "global-merge" ||
    nodeId === "global-terminal"
  ) {
    return { kind: "global", nodeId };
  }
  const gs = RE_GLOBAL_STATE.exec(nodeId);
  if (gs) return { kind: "global-state", globalStateIndex: Number(gs[1]) };
  const areaTerminal = RE_AREA_TERMINAL.exec(nodeId);
  if (areaTerminal) return { kind: "area-terminal", areaId: areaTerminal[1] };
  const area = RE_AREA.exec(nodeId);
  if (area) return { kind: "area", areaId: area[1] };
  const periodTerminal = RE_PERIOD_TERMINAL.exec(nodeId);
  if (periodTerminal)
    return {
      kind: "period-terminal",
      areaId: periodTerminal[1],
      periodId: periodTerminal[2],
    };
  const period = RE_PERIOD.exec(nodeId);
  if (period) return { kind: "period", areaId: period[1], periodId: period[2] };
  const participant = RE_PARTICIPANT.exec(nodeId);
  if (participant)
    return {
      kind: "participant",
      areaId: participant[1],
      periodId: participant[2],
      participantUserId: participant[3],
    };
  const response = RE_RESPONSE.exec(nodeId);
  if (response)
    return {
      kind: "response",
      areaId: response[1],
      periodId: response[2],
      responseId: response[3],
    };
  const state = RE_STATE.exec(nodeId);
  if (state) return { kind: "state", areaId: state[1], periodId: state[2] };
  return null;
}

function findArea(
  trazabilidad: SolicitudTrazabilidad,
  areaId: string,
): AsignacionTrazabilidad | undefined {
  return trazabilidad.areas.find((area) => area.id === areaId);
}

function findPeriod(
  area: AsignacionTrazabilidad,
  periodId: string,
): PeriodoTrazabilidad | undefined {
  return area.etapas.find((period) => period.id === periodId);
}

// ── Global-state ↔ flow node mirror (mirrors buildSolicitudFlow's skip rule) ──

function sortedGlobal(
  historial: HistorialEstadoGlobalTrazabilidad[],
): HistorialEstadoGlobalTrazabilidad[] {
  return [...historial].sort(
    (a, b) => (toMs(a.fecha_cambio) ?? 0) - (toMs(b.fecha_cambio) ?? 0),
  );
}

function isSkippedRegistrada(
  entry: HistorialEstadoGlobalTrazabilidad,
  idx: number,
  registroMs: number | null,
): boolean {
  return (
    idx === 0 &&
    entry.estado_nuevo === "REGISTRADA" &&
    toMs(entry.fecha_cambio) === registroMs
  );
}

/**
 * Map a global-state transition timestamp to its flow node id, mirroring the
 * builder's skip of the initial REGISTRADA dupe. `null` when the transition is
 * not represented in the flow (e.g. the skipped initial REGISTRADA).
 */
export function globalStateNodeIdForTimestamp(
  historial: HistorialEstadoGlobalTrazabilidad[],
  registroIso: string | null,
  tsMs: number,
): string | null {
  const registroMs = toMs(registroIso);
  const sorted = sortedGlobal(historial);
  for (let idx = 0; idx < sorted.length; idx += 1) {
    const entry = sorted[idx];
    if (isSkippedRegistrada(entry, idx, registroMs)) continue;
    if (toMs(entry.fecha_cambio) === tsMs) return `global-state-${idx}`;
  }
  return null;
}

/**
 * Resolve a flow `global-state-<idx>` node back to its historial entry.
 * Node ids use the ORIGINAL sorted index (the builder's `forEach` index), so
 * the entry is `sorted[idx]`; the only node that never exists is
 * `global-state-0` when the initial REGISTRADA dupe was skipped.
 */
export function globalStateEntryForNodeId(
  historial: HistorialEstadoGlobalTrazabilidad[],
  registroIso: string | null,
  nodeId: string,
): HistorialEstadoGlobalTrazabilidad | null {
  const parsed = parseFlowNodeId(nodeId);
  if (!parsed || parsed.kind !== "global-state") return null;
  const registroMs = toMs(registroIso);
  const sorted = sortedGlobal(historial);
  const entry = sorted[parsed.globalStateIndex];
  if (!entry) return null;
  if (
    parsed.globalStateIndex === 0 &&
    isSkippedRegistrada(entry, 0, registroMs)
  ) {
    return null;
  }
  return entry;
}

// ── Flow selection mapping ─────────────────────────────────────────────────────

function participantNodeIdFor(
  selection: Extract<TraceabilitySelection, { type: "participant-event" }>,
  trazabilidad: SolicitudTrazabilidad,
): string | null {
  const area = findArea(trazabilidad, selection.areaId);
  if (!area) return null;
  const period = findPeriod(area, selection.periodId);
  if (!period) return null;
  const idx = period.participantes.findIndex(
    (p) => p.usuario_id === selection.participantUserId,
  );
  if (idx < 0) return null;
  return `area-${selection.areaId}-period-${selection.periodId}-participant-${selection.participantUserId}-${idx}`;
}

/**
 * Map the unified selection to the flow's highlight/center contract. Never
 * rebuilds topology — only identifies the branch/subgraph to keep bright.
 */
export function toFlowSelection(
  selection: TraceabilitySelection,
  trazabilidad: SolicitudTrazabilidad,
  globalCtx: SolicitudGlobalContext,
): SolicitudFlowSelection {
  if (!selection) return null;
  switch (selection.type) {
    case "period":
      return {
        type: "period",
        areaId: selection.areaId,
        periodId: selection.periodId,
      };
    case "area":
      return { type: "area", areaId: selection.areaId };
    case "node":
      return { type: "node", nodeId: selection.nodeId };
    case "response":
      return {
        type: "node",
        nodeId: `area-${selection.areaId}-period-${selection.periodId}-response-${selection.responseId}`,
      };
    case "participant-event": {
      const nodeId = participantNodeIdFor(selection, trazabilidad);
      if (nodeId) return { type: "node", nodeId };
      return {
        type: "period",
        areaId: selection.areaId,
        periodId: selection.periodId,
      };
    }
    case "global-state": {
      const tsMs = toMs(selection.stateId);
      if (tsMs === null) return null;
      const nodeId = globalStateNodeIdForTimestamp(
        trazabilidad.historial_estados,
        globalCtx.fecha_registro,
        tsMs,
      );
      return nodeId ? { type: "node", nodeId } : null;
    }
  }
}

// ── Inspector resolution ───────────────────────────────────────────────────────

function lastAreaTimestampMs(area: AsignacionTrazabilidad): number | null {
  let last = toMs(area.fecha_incorporacion);
  const consider = (iso: string | null | undefined): void => {
    const t = toMs(iso);
    if (t !== null && (last === null || t > last)) last = t;
  };
  for (const period of area.etapas) {
    consider(period.fecha_inicio);
    consider(period.fecha_fin);
    for (const participant of period.participantes) {
      consider(participant.fecha_inicio);
      consider(participant.fecha_fin);
    }
    for (const response of period.respuestas) consider(response.fecha_emision);
    for (const change of period.historial_estados)
      consider(change.fecha_cambio);
  }
  return last;
}

function resolveGlobalNode(
  kind: "global-start" | "global-merge" | "global-terminal",
  trazabilidad: SolicitudTrazabilidad,
  globalCtx: SolicitudGlobalContext,
): ResolvedTraceabilitySelection {
  if (kind === "global-start") {
    return {
      type: "node",
      kind: "global-start",
      label: "Solicitud registrada",
      timestamp: globalCtx.fecha_registro,
      detail: globalCtx.id_publico
        ? `Solicitud ${globalCtx.id_publico}`
        : undefined,
    };
  }
  if (kind === "global-merge") {
    let mergeMs = toMs(globalCtx.fecha_registro) ?? 0;
    for (const area of trazabilidad.areas) {
      const tail = lastAreaTimestampMs(area);
      if (tail !== null && tail > mergeMs) mergeMs = tail;
    }
    return {
      type: "node",
      kind: "global-merge",
      label: "Convergencia",
      timestamp: new Date(mergeMs).toISOString(),
      detail: "Las ramas convergen según precedencia registrada",
    };
  }
  const label =
    globalCtx.estado === "FINALIZADA"
      ? "Finalizada"
      : globalCtx.estado === "ANULADA"
        ? "Anulada"
        : "Estado actual";
  let terminalMs = toMs(globalCtx.fecha_cierre);
  let lastRealMs = toMs(globalCtx.fecha_registro) ?? 0;
  for (const entry of trazabilidad.historial_estados) {
    const t = toMs(entry.fecha_cambio);
    if (t !== null && t > lastRealMs) lastRealMs = t;
  }
  for (const area of trazabilidad.areas) {
    const t = lastAreaTimestampMs(area);
    if (t !== null && t > lastRealMs) lastRealMs = t;
  }
  if (terminalMs === null || terminalMs < lastRealMs) terminalMs = lastRealMs;
  return {
    type: "node",
    kind: "global-terminal",
    label,
    timestamp: new Date(terminalMs).toISOString(),
    detail: globalCtx.fecha_cierre ? "Solicitud cerrada" : undefined,
  };
}

function resolveNodeSelection(
  nodeId: string,
  trazabilidad: SolicitudTrazabilidad,
  globalCtx: SolicitudGlobalContext,
): ResolvedTraceabilitySelection {
  const parsed = parseFlowNodeId(nodeId);
  if (!parsed) return null;

  if (parsed.kind === "global")
    return resolveGlobalNode(parsed.nodeId, trazabilidad, globalCtx);

  if (parsed.kind === "global-state") {
    const entry = globalStateEntryForNodeId(
      trazabilidad.historial_estados,
      globalCtx.fecha_registro,
      nodeId,
    );
    if (!entry) return null;
    const tsMs = toMs(entry.fecha_cambio);
    const event =
      trazabilidad.timeline.find(
        (candidate) => toMs(candidate.timestamp) === tsMs,
      ) ?? null;
    return {
      type: "global-state",
      area: null,
      period: null,
      historial: entry,
      event,
    };
  }

  if (parsed.kind === "area" || parsed.kind === "area-terminal") {
    const area = findArea(trazabilidad, parsed.areaId);
    return area ? { type: "area", area } : null;
  }

  const area = findArea(trazabilidad, parsed.areaId);
  const period = area ? findPeriod(area, parsed.periodId) : undefined;
  if (!area || !period) return area ? { type: "area", area } : null;

  if (parsed.kind === "participant") {
    const participant = period.participantes.find(
      (p) => p.usuario_id === parsed.participantUserId,
    );
    if (participant)
      return { type: "participant-event", area, period, participant };
    return { type: "period", area, period };
  }

  if (parsed.kind === "response") {
    const response = period.respuestas.find((r) => r.id === parsed.responseId);
    if (response) return { type: "response", area, period, response };
    return { type: "period", area, period };
  }

  return { type: "period", area, period };
}

/** Materialize entities for the compact inspector from the stable-ID selection. */
export function resolveSelection(
  selection: TraceabilitySelection,
  trazabilidad: SolicitudTrazabilidad,
  globalCtx: SolicitudGlobalContext,
): ResolvedTraceabilitySelection {
  if (!selection) return null;
  switch (selection.type) {
    case "node":
      return resolveNodeSelection(selection.nodeId, trazabilidad, globalCtx);
    case "global-state": {
      const tsMs = toMs(selection.stateId);
      const entry =
        tsMs === null
          ? undefined
          : trazabilidad.historial_estados.find(
              (candidate) => toMs(candidate.fecha_cambio) === tsMs,
            );
      if (!entry) return null;
      const event =
        tsMs === null
          ? null
          : (trazabilidad.timeline.find(
              (candidate) => toMs(candidate.timestamp) === tsMs,
            ) ?? null);
      return {
        type: "global-state",
        area: null,
        period: null,
        historial: entry,
        event,
      };
    }
    case "area": {
      const area = findArea(trazabilidad, selection.areaId);
      return area ? { type: "area", area } : null;
    }
    case "period": {
      const area = findArea(trazabilidad, selection.areaId);
      const period = area ? findPeriod(area, selection.periodId) : undefined;
      return area && period ? { type: "period", area, period } : null;
    }
    case "participant-event": {
      const area = findArea(trazabilidad, selection.areaId);
      const period = area ? findPeriod(area, selection.periodId) : undefined;
      const participant = period?.participantes.find(
        (p) => p.usuario_id === selection.participantUserId,
      );
      if (area && period && participant) {
        return { type: "participant-event", area, period, participant };
      }
      return area && period ? { type: "period", area, period } : null;
    }
    case "response": {
      const area = findArea(trazabilidad, selection.areaId);
      const period = area ? findPeriod(area, selection.periodId) : undefined;
      const response = period?.respuestas.find(
        (r) => r.id === selection.responseId,
      );
      if (area && period && response) {
        return { type: "response", area, period, response };
      }
      return area && period ? { type: "period", area, period } : null;
    }
  }
}
