/**
 * TraceabilityInspector — the SINGLE compact inspector (audit F12/F17, J; U8).
 *
 * Replaces both `ProcessInspector.tsx` (deleted) and the parallel
 * `OperationalSelectionPanel.tsx` (absorbed). Informational-only:
 *
 *  1. Header: humanized type, main title, state badge, close.
 *  2. Immediate context: date/time, area, cycle, Principal/Adjunta, actor or
 *     participant + role — only fields present, never inventing "responsable".
 *  3. Summary: previous→new change, duration, response or motivo (≤5 rows).
 *  4. Progressive disclosure: `Ver ciclo completo` / `Ver historial` /
 *     `Ver respuesta` — expands ONE section at a time inside the same
 *     container, composing compact `PeriodDetailContent` pieces (never the
 *     monolithic card mounted twice).
 *
 * Operational actions (Tomar, Marcar erronea, Cambiar participacion) are
 * rendered in GestionOperativaSolicitud exclusively. This inspector is
 * informational-only.
 *
 * Lives inside the main content column below the flow — not a second rail.
 */
"use client";

import { X } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type {
  AsignacionTrazabilidad,
  ParticipanteTrazabilidad,
  PeriodoTrazabilidad,
  SolicitudTrazabilidad,
} from "../../schemas/trazabilidad.schema";
import { classifyPeriod, classifyState, type GraphStatus } from "./graphStatus";
import {
  GlobalStateHistory,
  PeriodParticipants,
  PeriodResponses,
  PeriodStateHistory,
} from "./PeriodDetailContent";
import {
  participacionLabel,
  periodoEstadoLabel,
  respuestaEstadoLabel,
  respuestaLabel,
  solicitudEstadoLabel,
  tipoCierreLabel,
} from "./traceabilityLabels";
import type {
  ResolvedTraceabilitySelection,
  TraceabilitySelection,
} from "./traceabilitySelection";
import { formatDuration, formatTimelineDate } from "./traceabilityTimeline";

// ── Formatting ─────────────────────────────────────────────────────────────────

function safeMs(iso: string | null): number | null {
  if (!iso) return null;
  const ms = Date.parse(iso);
  return Number.isNaN(ms) ? null : ms;
}

function formatIso(iso: string | null): string {
  const ms = safeMs(iso);
  if (ms === null) return iso ? iso : "—";
  return formatTimelineDate(ms, "minutes");
}

// ── Status badge ───────────────────────────────────────────────────────────────

const STATUS_BADGE_CLASSES: Record<GraphStatus, string> = {
  active: "border-primary/40 bg-primary/10 text-primary",
  pending: "border-border bg-muted text-muted-foreground",
  closed: "border-border bg-muted/50 text-muted-foreground/70",
  risk: "border-destructive/40 bg-destructive/10 text-destructive",
};

function StatusBadge({
  status,
  label,
}: {
  status: GraphStatus;
  label: string;
}) {
  return (
    <span
      className={cn(
        "rounded-full border px-2 py-0.5 text-[10px] font-semibold",
        STATUS_BADGE_CLASSES[status],
      )}
    >
      {label}
    </span>
  );
}

// ── Header meta ────────────────────────────────────────────────────────────────

const NODE_KIND_LABELS: Record<string, string> = {
  "global-start": "Registro",
  "global-merge": "Convergencia",
  "global-terminal": "Estado final",
  "area-start": "Área incorporada",
  "area-terminal": "Rama",
  "period-start": "Ciclo iniciado",
  "period-terminal": "Ciclo",
  "participant-added": "Participante agregado",
  "participant-removed": "Participante retirado",
  response: "Respuesta",
  "period-state-change": "Cambio de estado",
};

interface InspectorMeta {
  typeLabel: string;
  title: string;
  badge: { label: string; status: GraphStatus } | null;
}

function metaFor(
  selection: Exclude<ResolvedTraceabilitySelection, null>,
): InspectorMeta {
  switch (selection.type) {
    case "period":
      return {
        typeLabel: "Ciclo",
        title: `Ciclo ${selection.period.numero_ciclo} · ${participacionLabel(selection.period.tipo_participacion)}`,
        badge: {
          label: periodoEstadoLabel(selection.period.estado),
          status: classifyPeriod(selection.period),
        },
      };
    case "participant-event":
      return {
        typeLabel: "Participante",
        title: selection.participant.usuario_nombres,
        badge: {
          label: selection.participant.activo ? "Activo" : "Retirado",
          status: selection.participant.activo ? "active" : "closed",
        },
      };
    case "response":
      return {
        typeLabel: "Respuesta",
        title: respuestaLabel(selection.response.tipo_respuesta),
        badge: {
          label: respuestaEstadoLabel(selection.response.estado),
          status: classifyState(selection.response.estado),
        },
      };
    case "global-state":
      return {
        typeLabel: "Estado de la solicitud",
        title: solicitudEstadoLabel(selection.historial.estado_nuevo),
        badge: {
          label: solicitudEstadoLabel(selection.historial.estado_nuevo),
          status: classifyState(selection.historial.estado_nuevo),
        },
      };
    case "area":
      return {
        typeLabel: "Área",
        title: selection.area.area_nombre,
        badge: selection.area.tipo_actual
          ? {
              label: participacionLabel(selection.area.tipo_actual),
              status: classifyState(selection.area.tipo_actual),
            }
          : null,
      };
    case "node":
      return {
        typeLabel: NODE_KIND_LABELS[selection.kind] ?? "Evento",
        title: selection.label,
        badge: null,
      };
  }
}

// ── Immediate context (only present fields) ────────────────────────────────────

interface ContextRow {
  label: string;
  value: string;
}

function contextRowsFor(
  selection: Exclude<ResolvedTraceabilitySelection, null>,
): ContextRow[] {
  switch (selection.type) {
    case "period": {
      const rows: ContextRow[] = [
        { label: "Área", value: selection.area.area_nombre },
        { label: "Ciclo", value: `Ciclo ${selection.period.numero_ciclo}` },
        {
          label: "Participación",
          value: participacionLabel(selection.period.tipo_participacion),
        },
        { label: "Inicio", value: formatIso(selection.period.fecha_inicio) },
        {
          label: "Fin",
          value: selection.period.fecha_fin
            ? formatIso(selection.period.fecha_fin)
            : "En curso",
        },
      ];
      if (selection.period.iniciado_por_nombres) {
        rows.push({
          label: "Iniciado por",
          value: selection.period.iniciado_por_nombres,
        });
      }
      if (selection.period.finalizado_por_nombres) {
        rows.push({
          label: "Finalizado por",
          value: selection.period.finalizado_por_nombres,
        });
      }
      return rows;
    }
    case "participant-event": {
      const rows: ContextRow[] = [
        { label: "Área", value: selection.area.area_nombre },
        { label: "Ciclo", value: `Ciclo ${selection.period.numero_ciclo}` },
      ];
      if (selection.participant.rol) {
        rows.push({ label: "Rol", value: selection.participant.rol });
      }
      rows.push({
        label: "Fecha inicio",
        value: formatIso(selection.participant.fecha_inicio),
      });
      if (selection.participant.fecha_fin) {
        rows.push({
          label: "Fecha fin",
          value: formatIso(selection.participant.fecha_fin),
        });
      }
      if (selection.participant.asignado_por_nombres) {
        rows.push({
          label: "Asignado por",
          value: selection.participant.asignado_por_nombres,
        });
      }
      if (selection.participant.retirado_por_nombres) {
        rows.push({
          label: "Retirado por",
          value: selection.participant.retirado_por_nombres,
        });
      }
      return rows;
    }
    case "response": {
      const rows: ContextRow[] = [
        { label: "Área", value: selection.area.area_nombre },
        { label: "Ciclo", value: `Ciclo ${selection.period.numero_ciclo}` },
      ];
      if (selection.response.emitido_por_nombres) {
        rows.push({
          label: "Emitida por",
          value: selection.response.emitido_por_nombres,
        });
      }
      rows.push({
        label: "Fecha",
        value: formatIso(selection.response.fecha_emision),
      });
      return rows;
    }
    case "global-state": {
      const rows: ContextRow[] = [
        { label: "Fecha", value: formatIso(selection.historial.fecha_cambio) },
      ];
      if (selection.historial.cambiado_por_nombres) {
        rows.push({
          label: "Actor",
          value: selection.historial.cambiado_por_nombres,
        });
      }
      return rows;
    }
    case "area": {
      const rows: ContextRow[] = [
        { label: "Ciclos", value: `${selection.area.etapas.length}` },
      ];
      if (selection.area.tipo_actual) {
        rows.push({
          label: "Participación",
          value: participacionLabel(selection.area.tipo_actual),
        });
      }
      if (selection.area.incorporado_por_nombres) {
        rows.push({
          label: "Incorporada por",
          value: selection.area.incorporado_por_nombres,
        });
      }
      return rows;
    }
    case "node": {
      const rows: ContextRow[] = [
        { label: "Fecha", value: formatIso(selection.timestamp) },
      ];
      if (selection.sublabel) {
        rows.push({ label: "Contexto", value: selection.sublabel });
      }
      if (selection.detail) {
        rows.push({ label: "Detalle", value: selection.detail });
      }
      return rows;
    }
  }
}

// ── Summary (≤5 visible rows) ──────────────────────────────────────────────────

function summaryRowsFor(
  selection: Exclude<ResolvedTraceabilitySelection, null>,
): string[] {
  switch (selection.type) {
    case "period": {
      const start = safeMs(selection.period.fecha_inicio);
      const end = safeMs(selection.period.fecha_fin);
      const activeCount = selection.period.participantes.filter(
        (p) => p.activo,
      ).length;
      const rows = [
        `Duración: ${start === null ? "—" : formatDuration(start, end)}`,
        `Estado: ${periodoEstadoLabel(selection.period.estado)}`,
        `Participantes: ${activeCount} activo(s) de ${selection.period.participantes.length}`,
      ];
      if (selection.period.tipo_cierre) {
        rows.push(`Cierre: ${tipoCierreLabel(selection.period.tipo_cierre)}`);
      }
      if (selection.period.motivo_cierre) {
        rows.push(`Motivo: ${selection.period.motivo_cierre}`);
      }
      return rows.slice(0, 5);
    }
    case "participant-event": {
      const start = safeMs(selection.participant.fecha_inicio);
      const end = safeMs(selection.participant.fecha_fin);
      const rows = [
        `Estado: ${selection.participant.activo ? "Activo" : "Retirado"}`,
        `Duración: ${start === null ? "—" : formatDuration(start, end)}`,
      ];
      if (selection.participant.motivo_retiro) {
        rows.push(`Motivo de retiro: ${selection.participant.motivo_retiro}`);
      }
      return rows.slice(0, 5);
    }
    case "response": {
      const rows = [
        `Estado: ${respuestaEstadoLabel(selection.response.estado)}`,
      ];
      if (selection.response.contenido) {
        rows.push(selection.response.contenido);
      }
      return rows.slice(0, 5);
    }
    case "global-state": {
      const rows: string[] = [];
      if (selection.historial.estado_anterior) {
        rows.push(
          `${solicitudEstadoLabel(selection.historial.estado_anterior)} → ${solicitudEstadoLabel(selection.historial.estado_nuevo)}`,
        );
      } else {
        rows.push(
          `Estado: ${solicitudEstadoLabel(selection.historial.estado_nuevo)}`,
        );
      }
      if (selection.historial.observacion) {
        rows.push(selection.historial.observacion);
      }
      return rows.slice(0, 5);
    }
    case "area": {
      const lastPeriod =
        selection.area.etapas[selection.area.etapas.length - 1];
      const rows = [
        `Bloquea cierre: ${selection.area.bloquea_cierre ? "Sí" : "No"}`,
      ];
      if (lastPeriod) {
        rows.push(`Último estado: ${periodoEstadoLabel(lastPeriod.estado)}`);
      }
      if (selection.area.observacion) {
        rows.push(selection.area.observacion);
      }
      return rows.slice(0, 5);
    }
    case "node":
      return [];
  }
}

// ── Progressive disclosure ─────────────────────────────────────────────────────

type DisclosureOption = "cycle" | "history" | "response";
type DisclosureKey = DisclosureOption | null;

function disclosureOptionsFor(
  selection: Exclude<ResolvedTraceabilitySelection, null>,
): DisclosureOption[] {
  switch (selection.type) {
    case "period":
    case "participant-event":
      return ["cycle", "history"];
    case "response":
      return ["cycle", "history", "response"];
    case "global-state":
      return ["history"];
    default:
      return [];
  }
}

const DISCLOSURE_LABELS: Record<DisclosureOption, string> = {
  cycle: "Ver ciclo completo",
  history: "Ver historial",
  response: "Ver respuesta",
};

function DisclosureContent({
  selection,
  disclosed,
  historial,
  formatDateTime,
  onParticipantClick,
}: {
  selection: Exclude<ResolvedTraceabilitySelection, null>;
  disclosed: Exclude<DisclosureKey, null>;
  historial: SolicitudTrazabilidad["historial_estados"];
  formatDateTime: (iso: string | null) => string;
  onParticipantClick?: (
    participant: ParticipanteTrazabilidad,
    period: PeriodoTrazabilidad,
    area: AsignacionTrazabilidad,
  ) => void;
}) {
  const hasCycle =
    selection.type === "period" ||
    selection.type === "participant-event" ||
    selection.type === "response";

  if (disclosed === "cycle" && hasCycle) {
    const { period, area } = selection;
    return (
      <div className="flex flex-col gap-4">
        <PeriodParticipants
          period={period}
          area={area}
          formatDateTime={formatDateTime}
          onParticipantClick={onParticipantClick}
        />
        <PeriodStateHistory period={period} formatDateTime={formatDateTime} />
        <PeriodResponses period={period} formatDateTime={formatDateTime} />
      </div>
    );
  }

  if (disclosed === "history") {
    if (selection.type === "global-state") {
      return (
        <GlobalStateHistory
          historial={historial}
          formatDateTime={formatDateTime}
        />
      );
    }
    if (hasCycle) {
      return (
        <PeriodStateHistory
          period={selection.period}
          formatDateTime={formatDateTime}
        />
      );
    }
    return null;
  }

  if (disclosed === "response" && selection.type === "response") {
    return (
      <section className="flex flex-col gap-2">
        <p className="text-[10px] font-black uppercase tracking-wide text-muted-foreground">
          Respuesta completa
        </p>
        <p className="text-xs text-foreground">
          {selection.response.contenido ?? "Sin contenido"}
        </p>
      </section>
    );
  }

  return null;
}

// ── Main component ─────────────────────────────────────────────────────────────

export interface TraceabilityInspectorProps {
  /** Resolved entities for the current stable-ID selection. */
  selection: Exclude<ResolvedTraceabilitySelection, null>;
  /** Full model used by disclosure lists (Ver historial global). */
  trazabilidad: SolicitudTrazabilidad;
  onClose: () => void;
  containerRef?: React.Ref<HTMLElement>;
  /** Participant rows inside disclosure emit the ID-based selection. */
  onSelectParticipant: (
    selection: Exclude<TraceabilitySelection, null>,
  ) => void;
}

export function TraceabilityInspector({
  selection,
  trazabilidad,
  onClose,
  containerRef,
  onSelectParticipant,
}: TraceabilityInspectorProps) {
  const [disclosed, setDisclosed] = useState<DisclosureKey>(null);
  const meta = metaFor(selection);
  const contextRows = contextRowsFor(selection);
  const summaryRows = summaryRowsFor(selection);
  const options = disclosureOptionsFor(selection);

  const handleParticipantClick = (
    participant: ParticipanteTrazabilidad,
    participantPeriod: PeriodoTrazabilidad,
    participantArea: AsignacionTrazabilidad,
  ) => {
    onSelectParticipant({
      type: "participant-event",
      areaId: participantArea.id,
      periodId: participantPeriod.id,
      participantUserId: participant.usuario_id,
    });
  };

  return (
    <section
      ref={containerRef}
      aria-labelledby="traceability-inspector-heading"
      className="app-card flex flex-col"
    >
      {/* 1. Header */}
      <header className="flex items-start justify-between gap-3 border-b border-border p-4">
        <div className="flex min-w-0 flex-col gap-1">
          <p className="text-[10px] font-black uppercase tracking-wide text-muted-foreground">
            {meta.typeLabel}
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <h3
              id="traceability-inspector-heading"
              className="text-sm font-semibold text-foreground"
            >
              {meta.title}
            </h3>
            {meta.badge && (
              <StatusBadge
                status={meta.badge.status}
                label={meta.badge.label}
              />
            )}
          </div>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onClose}
          aria-label="Cerrar detalle"
          className="shrink-0 gap-1.5"
        >
          <X className="size-4" aria-hidden="true" />
          <span className="hidden sm:inline">Cerrar</span>
        </Button>
      </header>

      {/* 2. Immediate context */}
      {contextRows.length > 0 && (
        <dl className="grid grid-cols-1 gap-x-4 gap-y-1 px-4 pt-3 text-xs sm:grid-cols-2">
          {contextRows.map((row) => (
            <div key={row.label} className="flex justify-between gap-3">
              <dt className="shrink-0 text-muted-foreground">{row.label}</dt>
              <dd className="truncate text-right font-medium text-foreground">
                {row.value}
              </dd>
            </div>
          ))}
        </dl>
      )}

      {/* 3. Summary — max 5 visible rows */}
      {summaryRows.length > 0 && (
        <ul className="flex flex-col gap-1 px-4 py-3 text-xs text-muted-foreground">
          {summaryRows.map((row) => (
            <li key={row} className="line-clamp-2">
              {row}
            </li>
          ))}
        </ul>
      )}

      {/* 4. Progressive disclosure — one section at a time */}
      {options.length > 0 && (
        <div className="flex flex-wrap gap-2 px-4 pb-3">
          {options.map((key) => {
            const active = disclosed === key;
            return (
              <Button
                key={key}
                type="button"
                variant={active ? "default" : "outline"}
                size="sm"
                onClick={() => setDisclosed(active ? null : key)}
                aria-expanded={active}
              >
                {DISCLOSURE_LABELS[key]}
              </Button>
            );
          })}
        </div>
      )}

      {disclosed && (
        <div className="border-t border-border px-4 py-3">
          <DisclosureContent
            selection={selection}
            disclosed={disclosed}
            historial={trazabilidad.historial_estados}
            formatDateTime={formatIso}
            onParticipantClick={handleParticipantClick}
          />
        </div>
      )}
    </section>
  );
}
