/**
 * ChronologicalHistory — collapsible chronological audit list for TrazabilidadView.
 *
 * Renders `historial_estados` (global state transitions) sorted ascending
 * (oldest first — narrative and state-oriented). Each row shows:
 * humanized event, timestamp, actor, area/cycle where present.
 *
 * Selecting a row emits the same `TraceabilitySelection` as the rest of the
 * system so the inspector opens for that event.
 *
 * Closed by default; toggled via the trigger button.
 */
"use client";

import { ChevronDown, ChevronUp, History } from "lucide-react";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { HistorialEstadoGlobalTrazabilidad } from "../../schemas/trazabilidad.schema";
import { solicitudEstadoLabel } from "./traceabilityLabels";
import { formatTimelineDate } from "./traceabilityTimeline";

interface ChronologicalHistoryProps {
  historial: HistorialEstadoGlobalTrazabilidad[];
  /** Emit a selection for a global state transition. */
  onSelect: (stateId: string) => void;
  selectedStateId?: string | null;
}

function safeMs(iso: string | null): number | null {
  if (!iso) return null;
  const ms = Date.parse(iso);
  return Number.isNaN(ms) ? null : ms;
}

function formatIso(iso: string | null): string {
  const ms = safeMs(iso);
  if (ms === null) return "—";
  return formatTimelineDate(ms, "minutes");
}

export function ChronologicalHistory({
  historial,
  onSelect,
  selectedStateId,
}: ChronologicalHistoryProps) {
  const [open, setOpen] = useState(false);

  const sorted = useMemo<HistorialEstadoGlobalTrazabilidad[]>(() => {
    return [...historial].sort(
      (a, b) => (safeMs(a.fecha_cambio) ?? 0) - (safeMs(b.fecha_cambio) ?? 0),
    );
  }, [historial]);

  if (historial.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="w-full justify-between gap-2 text-muted-foreground hover:text-foreground"
      >
        <span className="flex items-center gap-2">
          <History className="size-4" aria-hidden="true" />
          <span className="text-xs font-semibold uppercase tracking-wide">
            Ver historial cronológico
          </span>
          <span className="text-[10px] text-muted-foreground">
            ({historial.length} evento{historial.length !== 1 ? "s" : ""})
          </span>
        </span>
        {open ? (
          <ChevronUp className="size-4" aria-hidden="true" />
        ) : (
          <ChevronDown className="size-4" aria-hidden="true" />
        )}
      </Button>

      {open && (
        <ul
          className="flex flex-col gap-1 rounded-lg border border-border/60 bg-card p-3"
          aria-label="Historial cronológico de estados"
        >
          {sorted.map((entry) => {
            const isSelected = selectedStateId === entry.fecha_cambio;
            const transition =
              entry.estado_anterior &&
              entry.estado_anterior !== entry.estado_nuevo
                ? `${solicitudEstadoLabel(entry.estado_anterior)} → ${solicitudEstadoLabel(entry.estado_nuevo)}`
                : solicitudEstadoLabel(entry.estado_nuevo);

            return (
              <li key={entry.fecha_cambio} className="list-none">
                <button
                  type="button"
                  onClick={() => onSelect(entry.fecha_cambio)}
                  aria-current={isSelected ? "true" : undefined}
                  className={cn(
                    "flex w-full items-start justify-between gap-3 rounded-md px-2 py-1.5 text-left text-xs transition-colors",
                    "hover:bg-muted/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    isSelected
                      ? "bg-primary/5 text-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  <div className="flex min-w-0 flex-col gap-0.5">
                    <span className="truncate font-medium text-foreground">
                      {transition}
                    </span>
                    {entry.observacion && (
                      <span className="line-clamp-1 text-[10px] text-muted-foreground/70">
                        {entry.observacion}
                      </span>
                    )}
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-0.5">
                    <time
                      dateTime={entry.fecha_cambio ?? undefined}
                      className="text-[10px]"
                    >
                      {formatIso(entry.fecha_cambio)}
                    </time>
                    {entry.cambiado_por_nombres && (
                      <span className="text-[10px] text-muted-foreground/60">
                        {entry.cambiado_por_nombres}
                      </span>
                    )}
                  </div>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
