/**
 * SolicitudResumenOperativo — executive summary strip for Solicitud detail.
 *
 * Presents operational state at a glance:
 * - Estado + Prioridad (badge row)
 * - Expediente público ID + asunto
 * - Registration date, management start, deadline
 * - Active area count, period count, participant count
 * - Latest operational signal (most recent historial_global entry)
 *
 * Desktop: single compact horizontal row of labelled fields.
 * Mobile: stacked two-column grid.
 */
"use client";

import { Calendar, Clock, Layers, Users } from "lucide-react";
import type { SolicitudDetail } from "@/features/tramites/schemas/tramite.schema";
import {
  ESTADO_SOLICITUD,
  type EstadoSolicitud,
  PRIORIDAD_SOLICITUD,
  type PrioridadSolicitud,
} from "@/shared/constants/tramite.tokens";

interface SolicitudResumenOperativoProps {
  item: SolicitudDetail;
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("es-PE", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return "—";
  }
}

function deriveActiveCounts(item: SolicitudDetail) {
  const activeAreas = item.asignaciones.filter((a) =>
    a.periodos?.some(
      (p) =>
        p.estado !== "CERRADO" &&
        p.estado !== "FINALIZADO" &&
        p.estado !== "CANCELADO",
    ),
  );
  const activePeriodos = item.asignaciones.flatMap((a) =>
    (a.periodos ?? []).filter(
      (p) =>
        p.estado !== "CERRADO" &&
        p.estado !== "FINALIZADO" &&
        p.estado !== "CANCELADO",
    ),
  );
  const activeParticipants = activeAreas.flatMap((a) =>
    (a.participantes ?? []).filter((p) => p.activo),
  );
  return {
    activeAreaCount: activeAreas.length,
    activePeriodCount: activePeriodos.length,
    activeParticipantCount: activeParticipants.length,
  };
}

function deriveLatestSignal(item: SolicitudDetail): string | null {
  const entries = item.historial_global ?? [];
  if (entries.length === 0) return null;
  // Most recent entry is last (ascending order)
  const latest = entries[entries.length - 1];
  const dateStr = formatDate(latest.fecha_cambio);
  if (latest.observacion) {
    return `${latest.estado_nuevo} — ${latest.observacion} (${dateStr})`;
  }
  return `${latest.estado_nuevo} (${dateStr})`;
}

export function SolicitudResumenOperativo({
  item,
}: SolicitudResumenOperativoProps) {
  const { activeAreaCount, activePeriodCount, activeParticipantCount } =
    deriveActiveCounts(item);
  const latestSignal = deriveLatestSignal(item);

  const estadoToken = ESTADO_SOLICITUD[item.estado as EstadoSolicitud];
  const prioridadToken =
    PRIORIDAD_SOLICITUD[item.prioridad as PrioridadSolicitud];

  return (
    <div className="app-card p-4">
      {/* Badge row */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span
          className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${estadoToken?.badgeClass ?? "bg-muted text-muted-foreground border-border"}`}
        >
          {estadoToken?.label ?? item.estado}
        </span>
        <span
          className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${prioridadToken?.badgeClass ?? "bg-muted text-muted-foreground border-border"}`}
        >
          {prioridadToken?.label ?? item.prioridad}
        </span>
        {item.expediente?.id_publico && (
          <span className="text-xs font-mono text-muted-foreground ml-auto">
            {item.expediente.id_publico}
            {item.expediente.asunto && (
              <span className="text-muted-foreground/70 ml-1">
                — {item.expediente.asunto}
              </span>
            )}
          </span>
        )}
      </div>

      {/* Desktop: horizontal compact row | Mobile: stacked grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-x-4 gap-y-2 text-xs">
        {/* Registration date */}
        <div className="flex flex-col gap-0.5">
          <span className="text-muted-foreground flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            Registro
          </span>
          <span className="font-medium">{formatDate(item.fecha_registro)}</span>
        </div>

        {/* Management start */}
        {item.fecha_inicio_gestion && (
          <div className="flex flex-col gap-0.5">
            <span className="text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Inicio gestión
            </span>
            <span className="font-medium">
              {formatDate(item.fecha_inicio_gestion)}
            </span>
          </div>
        )}

        {/* Deadline */}
        {item.fecha_limite && (
          <div className="flex flex-col gap-0.5">
            <span className="text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Fecha límite
            </span>
            <span className="font-medium">{formatDate(item.fecha_limite)}</span>
          </div>
        )}

        {/* Active areas + periods */}
        <div className="flex flex-col gap-0.5">
          <span className="text-muted-foreground flex items-center gap-1">
            <Layers className="h-3 w-3" />
            Áreas activas
          </span>
          <span className="font-medium">
            {activeAreaCount}
            {activePeriodCount > 0 && (
              <span className="text-muted-foreground ml-1">
                ({activePeriodCount} período{activePeriodCount !== 1 ? "s" : ""}
                )
              </span>
            )}
          </span>
        </div>

        {/* Participants */}
        <div className="flex flex-col gap-0.5">
          <span className="text-muted-foreground flex items-center gap-1">
            <Users className="h-3 w-3" />
            Participantes
          </span>
          <span className="font-medium">
            {activeParticipantCount} activo
            {activeParticipantCount !== 1 ? "s" : ""}
          </span>
        </div>

        {/* Latest signal — spans full width on mobile, part of row on desktop */}
        {latestSignal && (
          <div className="col-span-2 sm:col-span-3 lg:col-span-5 flex flex-col gap-0.5 pt-2 border-t border-border mt-1">
            <span className="text-muted-foreground text-[10px] uppercase tracking-wide">
              Último movimiento
            </span>
            <span className="text-xs">{latestSignal}</span>
          </div>
        )}
      </div>
    </div>
  );
}
