/**
 * buildSolicitudFlow — pure, deterministic normalization of SolicitudTrazabilidad
 * into a { nodes, edges, areaGroups } graph ready for layout.
 *
 * Contracts (audit F02/F04):
 * - IDs are stable composites of entity ids + deterministic indices; never
 *   timestamp-only, so selection sync (audit G) has stable anchors.
 * - Events inside a cycle are sorted by timestamp FIRST (no category bucketing),
 *   so interleaved participants/state/responses keep their true order (F04).
 * - Edges express chronological precedence ONLY, never causality: area branches
 *   hang off the chronologically compatible global event and converge into a
 *   merge node before the final state (F02). No edge is added where the data
 *   does not support ordering.
 * - Pure: no DOM, no React, no Date.now(); same input → same output.
 */

import type { SolicitudTrazabilidad } from "../../schemas/trazabilidad.schema";
import {
  participacionLabel,
  periodoEstadoLabel,
  respuestaEstadoLabel,
  respuestaLabel,
  solicitudEstadoLabel,
  tipoCierreLabel,
} from "./traceabilityLabels";

/** Minimal global context mirroring SolicitudDetail fields passed by page.tsx. */
export interface SolicitudGlobalContext {
  fecha_registro: string;
  estado: string;
  fecha_cierre: string | null;
  id_publico: string | null;
}

export type FlowNodeKind =
  | "global-start"
  | "global-state"
  | "global-merge"
  | "global-terminal"
  | "area-start"
  | "area-terminal"
  | "period-start"
  | "period-terminal"
  | "participant-added"
  | "participant-removed"
  | "response"
  | "period-state-change";

export interface FlowNode {
  id: string;
  kind: FlowNodeKind;
  label: string;
  timestamp: string;
  /** Stable entity references for calendar/flow/inspector selection sync. */
  areaId?: string;
  periodId?: string;
  participantUserId?: string;
  responseId?: string;
  /** Free-form human detail (observation, motivo, nombre). */
  detail?: string;
  /** Secondary line, e.g. "Anterior → Nuevo" or the participant name. */
  sublabel?: string;
  /** true when the entity is still open (period without fecha_fin). */
  open?: boolean;
  /** Handle capability contract so the renderer can expose source/target Handles (F01). */
  handles: { input: boolean; output: boolean };
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
}

export interface FlowAreaGroup {
  areaId: string;
  areaNombre: string;
  tipoActual: string | null;
  bloqueaCierre: boolean;
  /** All node ids belonging to this area branch, in deterministic order. */
  nodeIds: string[];
}

export interface SolicitudFlow {
  nodes: FlowNode[];
  edges: FlowEdge[];
  areaGroups: FlowAreaGroup[];
  mergeNodeId: string | null;
  terminalNodeId: string | null;
}

function toMs(iso: string | null | undefined): number | null {
  if (iso == null) return null;
  const ms = Date.parse(iso);
  return Number.isNaN(ms) ? null : ms;
}

/** Deterministic tie-break rank for events sharing a timestamp. */
const KIND_RANK: Record<FlowNodeKind, number> = {
  "global-start": 0,
  "global-state": 1,
  "area-start": 2,
  "period-start": 10,
  "participant-added": 20,
  "period-state-change": 21,
  response: 22,
  "participant-removed": 23,
  "period-terminal": 30,
  "area-terminal": 40,
  "global-merge": 50,
  "global-terminal": 60,
};

function compareNodes(a: FlowNode, b: FlowNode): number {
  const ta = toMs(a.timestamp) ?? 0;
  const tb = toMs(b.timestamp) ?? 0;
  if (ta !== tb) return ta - tb;
  const ra = KIND_RANK[a.kind];
  const rb = KIND_RANK[b.kind];
  if (ra !== rb) return ra - rb;
  return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
}

export function buildSolicitudFlow(
  trazabilidad: SolicitudTrazabilidad,
  ctx: SolicitudGlobalContext,
): SolicitudFlow {
  const nodes: FlowNode[] = [];
  const edges: FlowEdge[] = [];
  const areaGroups: FlowAreaGroup[] = [];

  const addEdge = (source: string, target: string): void => {
    edges.push({ id: `edge-${source}__${target}`, source, target });
  };

  // ── Global rail ──────────────────────────────────────────────────────────────
  const registroMs = toMs(ctx.fecha_registro);
  const startNode: FlowNode = {
    id: "global-start",
    kind: "global-start",
    label: "Solicitud registrada",
    timestamp: ctx.fecha_registro,
    detail: ctx.id_publico ? `Solicitud ${ctx.id_publico}` : undefined,
    handles: { input: false, output: true },
  };
  nodes.push(startNode);

  const sortedGlobal = [...trazabilidad.historial_estados].sort(
    (a, b) => (toMs(a.fecha_cambio) ?? 0) - (toMs(b.fecha_cambio) ?? 0),
  );
  const globalStates: FlowNode[] = [];
  sortedGlobal.forEach((entry, idx) => {
    // The backend always records the initial REGISTRADA transition at
    // fecha_registro; the start node already represents it, so skip the dupe.
    if (
      idx === 0 &&
      entry.estado_nuevo === "REGISTRADA" &&
      toMs(entry.fecha_cambio) === registroMs
    ) {
      return;
    }
    const node: FlowNode = {
      id: `global-state-${idx}`,
      kind: "global-state",
      label: solicitudEstadoLabel(entry.estado_nuevo),
      timestamp: entry.fecha_cambio,
      detail: entry.observacion ?? undefined,
      sublabel: entry.estado_anterior
        ? `Desde ${solicitudEstadoLabel(entry.estado_anterior)}`
        : undefined,
      handles: { input: true, output: true },
    };
    globalStates.push(node);
    nodes.push(node);
  });

  // ── Area branches ────────────────────────────────────────────────────────────
  const areas = [...trazabilidad.areas].sort(
    (a, b) =>
      (toMs(a.fecha_incorporacion) ?? 0) - (toMs(b.fecha_incorporacion) ?? 0),
  );

  for (const area of areas) {
    const areaStartId = `area-${area.id}`;
    nodes.push({
      id: areaStartId,
      kind: "area-start",
      label: "Área incorporada",
      timestamp: area.fecha_incorporacion,
      areaId: area.id,
      detail: area.area_nombre,
      sublabel: area.observacion ?? undefined,
      handles: { input: true, output: true },
    });

    const periods = [...area.etapas].sort((a, b) => {
      const byCiclo = a.numero_ciclo - b.numero_ciclo;
      if (byCiclo !== 0) return byCiclo;
      return (toMs(a.fecha_inicio) ?? 0) - (toMs(b.fecha_inicio) ?? 0);
    });

    const areaEventIds: string[] = [areaStartId];
    let lastAreaTs: string = area.fecha_incorporacion;
    let firstPeriodStartId: string | null = null;
    let prevPeriod: { id: string; closed: boolean } | null = null;

    for (const period of periods) {
      const periodStartId = `area-${area.id}-period-${period.id}`;
      if (firstPeriodStartId === null) firstPeriodStartId = periodStartId;
      nodes.push({
        id: periodStartId,
        kind: "period-start",
        label: `Ciclo ${period.numero_ciclo}`,
        timestamp: period.fecha_inicio,
        areaId: area.id,
        periodId: period.id,
        sublabel: participacionLabel(period.tipo_participacion),
        handles: { input: true, output: true },
      });
      areaEventIds.push(periodStartId);
      if (toMs(period.fecha_inicio) !== null) {
        lastAreaTs = period.fecha_inicio;
      }

      // Inner events of the cycle, sorted chronologically (F04).
      const inner: FlowNode[] = [];
      period.participantes.forEach((p, pIdx) => {
        inner.push({
          id: `area-${area.id}-period-${period.id}-participant-${p.usuario_id}-${pIdx}`,
          kind: "participant-added",
          label: "Participante agregado",
          timestamp: p.fecha_inicio,
          areaId: area.id,
          periodId: period.id,
          participantUserId: p.usuario_id,
          sublabel: p.usuario_nombres,
          detail: p.rol ?? undefined,
          handles: { input: true, output: true },
        });
        if (p.fecha_fin) {
          inner.push({
            id: `area-${area.id}-period-${period.id}-participant-${p.usuario_id}-${pIdx}-out`,
            kind: "participant-removed",
            label: "Participante retirado",
            timestamp: p.fecha_fin,
            areaId: area.id,
            periodId: period.id,
            participantUserId: p.usuario_id,
            sublabel: p.usuario_nombres,
            detail: p.motivo_retiro ?? undefined,
            handles: { input: true, output: true },
          });
        }
      });
      period.historial_estados.forEach((h, hIdx) => {
        inner.push({
          id: `area-${area.id}-period-${period.id}-state-${hIdx}`,
          kind: "period-state-change",
          label: "Cambio de estado del ciclo",
          timestamp: h.fecha_cambio,
          areaId: area.id,
          periodId: period.id,
          sublabel: `${periodoEstadoLabel(h.estado_anterior)} → ${periodoEstadoLabel(h.estado_nuevo)}`,
          detail: h.motivo ?? undefined,
          handles: { input: true, output: true },
        });
      });
      period.respuestas.forEach((r) => {
        inner.push({
          id: `area-${area.id}-period-${period.id}-response-${r.id}`,
          kind: "response",
          label: respuestaLabel(r.tipo_respuesta),
          timestamp: r.fecha_emision,
          areaId: area.id,
          periodId: period.id,
          responseId: r.id,
          sublabel: r.estado ? respuestaEstadoLabel(r.estado) : undefined,
          handles: { input: true, output: true },
        });
      });
      inner.sort(compareNodes);

      const isClosed = period.fecha_fin != null;
      const terminalTs =
        period.fecha_fin ??
        (inner.length > 0
          ? inner[inner.length - 1].timestamp
          : period.fecha_inicio);
      const periodTerminalId = `area-${area.id}-period-${period.id}-terminal`;
      const periodTerminalNode: FlowNode = {
        id: periodTerminalId,
        kind: "period-terminal",
        label: isClosed
          ? `Ciclo ${period.numero_ciclo} cerrado`
          : `Ciclo ${period.numero_ciclo} en curso`,
        timestamp: terminalTs,
        areaId: area.id,
        periodId: period.id,
        sublabel:
          isClosed && period.tipo_cierre
            ? tipoCierreLabel(period.tipo_cierre)
            : undefined,
        detail: period.motivo_cierre ?? undefined,
        open: !isClosed,
        handles: { input: true, output: true },
      };

      // Cycle spine: start → inner events (chronological) → terminal.
      addEdge(periodStartId, inner.length > 0 ? inner[0].id : periodTerminalId);
      for (let i = 0; i < inner.length - 1; i += 1) {
        addEdge(inner[i].id, inner[i + 1].id);
      }
      if (inner.length > 0) {
        addEdge(inner[inner.length - 1].id, periodTerminalId);
      }
      for (const node of inner) {
        nodes.push(node);
        areaEventIds.push(node.id);
      }
      nodes.push(periodTerminalNode);
      areaEventIds.push(periodTerminalId);

      // Consecutive cycles connect only when the previous one has a real end.
      if (prevPeriod?.closed === true) {
        addEdge(prevPeriod.id, periodStartId);
      }
      prevPeriod = { id: periodTerminalId, closed: isClosed };
      if (toMs(terminalTs) !== null) {
        lastAreaTs = terminalTs;
      }
    }

    // Area terminal — factual summary of the branch state.
    const areaOpen =
      periods.length > 0
        ? periods[periods.length - 1].fecha_fin == null
        : false;
    const areaTerminalId = `area-${area.id}-terminal`;
    nodes.push({
      id: areaTerminalId,
      kind: "area-terminal",
      label: areaOpen ? "Rama en curso" : "Rama completada",
      timestamp: lastAreaTs,
      areaId: area.id,
      detail: area.bloquea_cierre
        ? `${area.area_nombre} · bloquea cierre`
        : area.area_nombre,
      handles: { input: true, output: true },
    });
    const areaTail = areaEventIds[areaEventIds.length - 1] ?? areaStartId;
    addEdge(areaTail, areaTerminalId);
    if (firstPeriodStartId !== null) {
      addEdge(areaStartId, firstPeriodStartId);
    }

    areaGroups.push({
      areaId: area.id,
      areaNombre: area.area_nombre,
      tipoActual: area.tipo_actual,
      bloqueaCierre: area.bloquea_cierre,
      nodeIds: [...areaEventIds, areaTerminalId],
    });

    // Area branch hangs off the chronologically compatible global event.
    const areaStartMs = toMs(area.fecha_incorporacion) ?? 0;
    let sourceGlobal: string = startNode.id;
    for (const g of globalStates) {
      const gMs = toMs(g.timestamp) ?? 0;
      if (gMs <= areaStartMs) {
        sourceGlobal = g.id;
      } else {
        break;
      }
    }
    addEdge(sourceGlobal, areaStartId);
  }

  // ── Global rail wiring ───────────────────────────────────────────────────────
  let lastGlobalId: string = startNode.id;
  if (globalStates.length > 0) {
    addEdge(startNode.id, globalStates[0].id);
    for (let i = 0; i < globalStates.length - 1; i += 1) {
      addEdge(globalStates[i].id, globalStates[i + 1].id);
    }
    lastGlobalId = globalStates[globalStates.length - 1].id;
  }

  const mergeNodeId = areas.length > 0 ? "global-merge" : null;
  if (mergeNodeId !== null) {
    const mergeTs = areas.reduce<string>((acc, area) => {
      const tail = nodes.find((n) => n.id === `area-${area.id}-terminal`);
      if (!tail) return acc;
      const accMs = toMs(acc) ?? 0;
      const tailMs = toMs(tail.timestamp) ?? 0;
      return tailMs > accMs ? tail.timestamp : acc;
    }, startNode.timestamp);
    nodes.push({
      id: mergeNodeId,
      kind: "global-merge",
      label: "Convergencia",
      timestamp: mergeTs,
      detail: "Las ramas convergen según precedencia registrada",
      handles: { input: true, output: true },
    });
    for (const area of areas) {
      addEdge(`area-${area.id}-terminal`, mergeNodeId);
    }
    addEdge(lastGlobalId, mergeNodeId);
  }

  // ── Global terminal ──────────────────────────────────────────────────────────
  const terminalLabel =
    ctx.estado === "FINALIZADA"
      ? "Finalizada"
      : ctx.estado === "ANULADA"
        ? "Anulada"
        : "Estado actual";
  let terminalMs = toMs(ctx.fecha_cierre);
  let lastRealMs = 0;
  for (const node of nodes) {
    const t = toMs(node.timestamp);
    if (t !== null && t > lastRealMs) lastRealMs = t;
  }
  if (terminalMs === null || terminalMs < lastRealMs) {
    terminalMs = lastRealMs;
  }
  if (terminalMs === null) {
    terminalMs = registroMs ?? 0;
  }
  const terminalId = "global-terminal";
  nodes.push({
    id: terminalId,
    kind: "global-terminal",
    label: terminalLabel,
    timestamp: new Date(terminalMs).toISOString(),
    detail: ctx.fecha_cierre ? "Solicitud cerrada" : undefined,
    handles: { input: true, output: false },
  });
  addEdge(mergeNodeId ?? lastGlobalId, terminalId);

  // ── Determinism safeguard: canonical edge order (nodes keep generation order). ──
  edges.sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));

  return {
    nodes,
    edges,
    areaGroups,
    mergeNodeId,
    terminalNodeId: terminalId,
  };
}
