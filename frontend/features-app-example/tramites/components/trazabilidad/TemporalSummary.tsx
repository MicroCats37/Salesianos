/**
 * TemporalSummary — compact lifecycle strip for TrazabilidadView.
 *
 * Displays:
 * - Inicio: earliest real timestamp (from buildLifecycleBounds dataStart).
 * - Fin: last real event / fecha_cierre for closed; "En curso" when open.
 * - Duración total: formatDuration between start and end.
 * - Áreas: unique assignments + active/total breakdown when meaningful.
 *
 * Pure presentation; all data derived from trazabilidad + globalCtx + bounds.
 */
"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import type { SolicitudTrazabilidad } from "../../schemas/trazabilidad.schema";
import type { SolicitudGlobalContext } from "./buildSolicitudFlow";
import { buildLifecycleBounds, formatDuration } from "./traceabilityTimeline";

interface TemporalSummaryProps {
  trazabilidad: SolicitudTrazabilidad;
  global: SolicitudGlobalContext;
}

interface SummaryItem {
  label: string;
  value: string;
  className?: string;
}

function safeMs(iso: string | null | undefined): number | null {
  if (!iso) return null;
  const ms = Date.parse(iso);
  return Number.isNaN(ms) ? null : ms;
}

function formatShortDate(iso: string | null): string {
  const ms = safeMs(iso);
  if (ms === null) return "—";
  const d = new Date(ms);
  return d.toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatShortDateTime(iso: string | null): string {
  const ms = safeMs(iso);
  if (ms === null) return "—";
  const d = new Date(ms);
  return d.toLocaleString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function TemporalSummary({
  trazabilidad,
  global,
}: TemporalSummaryProps) {
  const bounds = useMemo(
    () =>
      buildLifecycleBounds({
        historial_estados: trazabilidad.historial_estados,
        areas: trazabilidad.areas,
        timeline: trazabilidad.timeline,
        fecha_registro: global.fecha_registro,
        fecha_cierre: global.fecha_cierre,
        estado: global.estado,
      }),
    [trazabilidad, global],
  );

  // Inicio: earliest real event timestamp
  const inicio = useMemo(() => {
    if (bounds.dataStart === null) return "—";
    return formatShortDateTime(
      global.fecha_registro && safeMs(global.fecha_registro) !== null
        ? global.fecha_registro
        : bounds.dataStart !== null
          ? new Date(bounds.dataStart).toISOString()
          : null,
    );
  }, [bounds.dataStart, global.fecha_registro]);

  // Fin: last real event or explicit closure; "En curso" when open
  const fin = useMemo(() => {
    if (!bounds.hasOpenPeriod && global.fecha_cierre) {
      return formatShortDate(global.fecha_cierre);
    }
    if (!bounds.hasOpenPeriod && bounds.dataEnd !== null) {
      return formatShortDate(new Date(bounds.dataEnd).toISOString());
    }
    return "En curso";
  }, [bounds, global.fecha_cierre]);

  // Duración total
  const duracion = useMemo(() => {
    if (bounds.dataStart === null) return "—";
    const endMs = bounds.hasOpenPeriod ? null : bounds.dataEnd;
    if (endMs === null) return formatDuration(bounds.dataStart, null);
    return formatDuration(bounds.dataStart, endMs);
  }, [bounds]);

  // Áreas involucradas
  const areaCount = trazabilidad.areas.length;
  const activeAreas = useMemo(
    () =>
      trazabilidad.areas.filter((a) =>
        a.etapas.some((p) => p.fecha_fin == null),
      ).length,
    [trazabilidad.areas],
  );

  const items: SummaryItem[] = [
    { label: "Inicio", value: inicio },
    { label: "Fin", value: fin },
    { label: "Duración", value: duracion },
    {
      label: "Áreas",
      value:
        areaCount === 0
          ? "Sin áreas"
          : activeAreas > 0 && activeAreas < areaCount
            ? `${activeAreas} activa(s) / ${areaCount} total`
            : activeAreas === areaCount && activeAreas > 0
              ? `${areaCount} área${areaCount !== 1 ? "s" : ""}`
              : `${areaCount} área${areaCount !== 1 ? "s" : ""}`,
    },
  ];

  return (
    <section
      aria-label="Resumen temporal del trámite"
      className={cn(
        "flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg border border-border/60 bg-muted/20 px-4 py-2.5",
        "text-xs text-muted-foreground",
      )}
    >
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5">
          <span className="font-semibold">{item.label}:</span>
          <span className={cn("text-foreground", item.className)}>
            {item.value}
          </span>
        </div>
      ))}
    </section>
  );
}
