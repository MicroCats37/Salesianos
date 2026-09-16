/**
 * PeriodDetailContent — compact, humanized detail sections reused ONLY by the
 * single TraceabilityInspector's progressive disclosure (audit J/F12, U8).
 *
 * The monolithic card that used to be mounted twice (ProcessInspector +
 * OperationalSelectionPanel) is gone. Each section is a small composed piece
 * that takes the resolved entities directly and humanizes every enum via
 * `traceabilityLabels.ts` (audit F14). No section is a full screen card; the
 * inspector composes them compactly inside one container.
 */
"use client";

import { Badge } from "@/components/ui/badge";
import type {
  AsignacionTrazabilidad,
  HistorialEstadoGlobalTrazabilidad,
  ParticipanteTrazabilidad,
  PeriodoTrazabilidad,
} from "../../schemas/trazabilidad.schema";
import {
  periodoEstadoLabel,
  respuestaEstadoLabel,
  respuestaLabel,
  solicitudEstadoLabel,
} from "./traceabilityLabels";

export interface TraceabilitySectionProps {
  formatDateTime: (iso: string | null) => string;
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-black uppercase tracking-wide text-muted-foreground">
      {children}
    </p>
  );
}

export function PeriodParticipants({
  period,
  area,
  formatDateTime,
  onParticipantClick,
}: TraceabilitySectionProps & {
  period: PeriodoTrazabilidad;
  area: AsignacionTrazabilidad;
  onParticipantClick?: (
    participant: ParticipanteTrazabilidad,
    period: PeriodoTrazabilidad,
    area: AsignacionTrazabilidad,
  ) => void;
}) {
  const activeCount = period.participantes.filter((p) => p.activo).length;
  return (
    <section className="flex flex-col gap-2">
      <SectionTitle>Participantes ({period.participantes.length})</SectionTitle>
      {period.participantes.length === 0 ? (
        <p className="text-xs italic text-muted-foreground">
          Sin participantes
        </p>
      ) : (
        <ul className="flex flex-col gap-1">
          {period.participantes.map((pt) => {
            const row = (
              <div className="flex items-center justify-between gap-2 rounded-lg border border-border bg-card p-2 text-xs">
                <div className="flex min-w-0 flex-col gap-0.5">
                  <span className="truncate font-medium text-foreground">
                    {pt.usuario_nombres}
                  </span>
                  {pt.rol && (
                    <span className="truncate text-[10px] text-muted-foreground">
                      {pt.rol}
                    </span>
                  )}
                </div>
                <div className="flex shrink-0 flex-col items-end gap-0.5">
                  <Badge
                    variant={pt.activo ? "default" : "secondary"}
                    className="text-[10px]"
                  >
                    {pt.activo ? "Activo" : "Retirado"}
                  </Badge>
                  <time
                    dateTime={pt.fecha_inicio}
                    className="text-[10px] text-muted-foreground"
                  >
                    {formatDateTime(pt.fecha_inicio)}
                  </time>
                </div>
              </div>
            );
            return (
              <li key={pt.usuario_id}>
                {onParticipantClick ? (
                  <button
                    type="button"
                    onClick={() => onParticipantClick(pt, period, area)}
                    className="w-full rounded-lg text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    aria-label={`${pt.usuario_nombres}${pt.rol ? `, ${pt.rol}` : ""}${pt.activo ? "" : " (retirado)"}`}
                  >
                    {row}
                  </button>
                ) : (
                  row
                )}
              </li>
            );
          })}
        </ul>
      )}
      {period.participantes.length > 0 && activeCount === 0 && (
        <p className="text-[10px] italic text-muted-foreground">
          Sin participantes activos
        </p>
      )}
    </section>
  );
}

export function PeriodStateHistory({
  period,
  formatDateTime,
}: TraceabilitySectionProps & { period: PeriodoTrazabilidad }) {
  return (
    <section className="flex flex-col gap-2">
      <SectionTitle>Historial de estados del ciclo</SectionTitle>
      {period.historial_estados.length === 0 ? (
        <p className="text-xs italic text-muted-foreground">
          Sin historial de estados
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {period.historial_estados.map((h) => (
            <li
              key={h.fecha_cambio}
              className="flex flex-col gap-1 rounded-lg border border-border bg-muted/20 p-2"
            >
              <div className="flex items-center justify-between gap-2">
                <Badge variant="outline" className="text-xs">
                  {periodoEstadoLabel(h.estado_nuevo)}
                </Badge>
                <span className="text-[10px] text-muted-foreground">
                  <time dateTime={h.fecha_cambio}>
                    {formatDateTime(h.fecha_cambio)}
                  </time>
                </span>
              </div>
              {h.estado_anterior && (
                <p className="text-[10px] text-muted-foreground">
                  Anterior: {periodoEstadoLabel(h.estado_anterior)}
                </p>
              )}
              <p className="text-[10px] text-muted-foreground">
                {h.cambiado_por_nombres}
              </p>
              {h.motivo && (
                <p className="line-clamp-2 text-[10px] italic text-muted-foreground">
                  {h.motivo}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function PeriodResponses({
  period,
  formatDateTime,
}: TraceabilitySectionProps & { period: PeriodoTrazabilidad }) {
  return (
    <section className="flex flex-col gap-2">
      <SectionTitle>Respuestas ({period.respuestas.length})</SectionTitle>
      {period.respuestas.length === 0 ? (
        <p className="text-xs italic text-muted-foreground">
          Sin respuestas registradas
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {period.respuestas.map((r) => (
            <li
              key={r.id}
              className="flex flex-col gap-1 rounded-lg border border-border p-2"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-xs font-medium text-foreground">
                  {respuestaLabel(r.tipo_respuesta)}
                </span>
                <Badge variant="outline" className="shrink-0 text-xs">
                  {respuestaEstadoLabel(r.estado)}
                </Badge>
              </div>
              {r.contenido && (
                <p className="line-clamp-3 text-xs text-muted-foreground">
                  {r.contenido}
                </p>
              )}
              <div className="flex justify-between gap-2 text-[10px] text-muted-foreground">
                <span>{r.emitido_por_nombres ?? "—"}</span>
                <time dateTime={r.fecha_emision}>
                  {formatDateTime(r.fecha_emision)}
                </time>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function GlobalStateHistory({
  historial,
  formatDateTime,
}: TraceabilitySectionProps & {
  historial: HistorialEstadoGlobalTrazabilidad[];
}) {
  return (
    <section className="flex flex-col gap-2">
      <SectionTitle>Historial de la solicitud</SectionTitle>
      {historial.length === 0 ? (
        <p className="text-xs italic text-muted-foreground">
          Sin historial registrado
        </p>
      ) : (
        <ol className="flex flex-col gap-2">
          {[...historial]
            .sort(
              (a, b) => Date.parse(a.fecha_cambio) - Date.parse(b.fecha_cambio),
            )
            .map((entry) => (
              <li
                key={entry.fecha_cambio}
                className="flex flex-col gap-1 rounded-lg border border-border bg-muted/20 p-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <Badge variant="outline" className="text-xs">
                    {solicitudEstadoLabel(entry.estado_nuevo)}
                  </Badge>
                  <span className="text-[10px] text-muted-foreground">
                    <time dateTime={entry.fecha_cambio}>
                      {formatDateTime(entry.fecha_cambio)}
                    </time>
                  </span>
                </div>
                {entry.estado_anterior && (
                  <p className="text-[10px] text-muted-foreground">
                    Anterior: {solicitudEstadoLabel(entry.estado_anterior)}
                  </p>
                )}
                <p className="text-[10px] text-muted-foreground">
                  {entry.cambiado_por_nombres}
                </p>
                {entry.observacion && (
                  <p className="line-clamp-2 text-[10px] italic text-muted-foreground">
                    {entry.observacion}
                  </p>
                )}
              </li>
            ))}
        </ol>
      )}
    </section>
  );
}
