/**
 * SolicitudResumenEjecutivo — purpose-built executive summary for Solicitud detail.
 *
 * Follows the operational report's Resumen ejecutivo spec:
 * - Asunto first (up to two lines), then technical identifiers.
 * - Estado as semantic token badge; prioridad adjacent but visually secondary.
 * - Key dates: Registrada, Inicio de gestión, Fecha límite.
 * - Current scope: active areas, active etapas, active participants.
 * - Responsibility: principal / adjunta areas by participation type.
 * - Last movement from historial_global (state, date, actor).
 *
 * Desktop: compact horizontal card that reflows to fewer columns via container
 * queries when the conversation panel narrows the main column.
 * Mobile: stacked grid.
 */
"use client";

import { Calendar, Clock, Layers, LinkIcon, Users } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import type { SolicitudDetail } from "@/features/tramites/schemas/tramite.schema";
import {
  ESTADO_SOLICITUD,
  type EstadoSolicitud,
  PRIORIDAD_SOLICITUD,
  type PrioridadSolicitud,
  TIPO_PARTICIPACION,
  type TipoParticipacion,
} from "@/shared/constants/tramite.tokens";

interface SolicitudResumenEjecutivoProps {
  item: SolicitudDetail;
}

const CLOSED_PERIOD_STATES = new Set(["CERRADO", "FINALIZADO", "CANCELADO"]);

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

function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("es-PE", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

function deriveActiveScope(item: SolicitudDetail) {
  const activeAreas = item.asignaciones.filter((a) =>
    (a.periodos ?? []).some((p) => !CLOSED_PERIOD_STATES.has(p.estado)),
  );
  const activeEtapas = item.asignaciones.flatMap((a) =>
    (a.periodos ?? []).filter((p) => !CLOSED_PERIOD_STATES.has(p.estado)),
  );
  const activeParticipants = new Set<string>();
  for (const area of activeAreas) {
    for (const participant of area.participantes ?? []) {
      if (participant.activo) activeParticipants.add(participant.usuario_id);
    }
  }
  return {
    activeAreaCount: activeAreas.length,
    activeEtapaCount: activeEtapas.length,
    activeParticipantCount: activeParticipants.size,
  };
}

function deriveResponsabilidad(item: SolicitudDetail) {
  const areas = item.asignaciones.map((a) => ({
    nombre: a.area_nombre,
    tipo: (a.periodos?.[0]?.tipo_participacion ??
      "ADJUNTA") as TipoParticipacion,
  }));
  return {
    principal: areas.filter((a) => a.tipo === "PRINCIPAL"),
    adjunta: areas.filter((a) => a.tipo === "ADJUNTA"),
  };
}

function deriveUltimoMovimiento(item: SolicitudDetail): string | null {
  const entries = item.historial_global ?? [];
  if (entries.length === 0) return null;
  const latest = entries[entries.length - 1];
  const estadoLabel =
    ESTADO_SOLICITUD[latest.estado_nuevo as EstadoSolicitud]?.label ??
    latest.estado_nuevo;
  const fecha = formatDateTime(latest.fecha_cambio);
  return latest.cambiado_por_nombres
    ? `${estadoLabel} · ${fecha} · ${latest.cambiado_por_nombres}`
    : `${estadoLabel} · ${fecha}`;
}

export function SolicitudResumenEjecutivo({
  item,
}: SolicitudResumenEjecutivoProps) {
  const router = useRouter();
  const { activeAreaCount, activeEtapaCount, activeParticipantCount } =
    deriveActiveScope(item);
  const responsabilidad = deriveResponsabilidad(item);
  const ultimoMovimiento = deriveUltimoMovimiento(item);

  const estadoToken = ESTADO_SOLICITUD[item.estado as EstadoSolicitud];
  const prioridadToken =
    PRIORIDAD_SOLICITUD[item.prioridad as PrioridadSolicitud];

  return (
    <section
      aria-labelledby="resumen-ejecutivo-heading"
      className="app-card @container p-5 lg:p-6"
    >
      <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
        <div className="min-w-0">
          <h2
            id="resumen-ejecutivo-heading"
            className="text-sm font-semibold text-foreground"
          >
            Resumen ejecutivo
          </h2>
          {item.expediente?.asunto && (
            <p className="mt-1.5 text-lg font-semibold leading-snug text-foreground line-clamp-2">
              {item.expediente.asunto}
            </p>
          )}
          {item.expediente?.id_publico && (
            <p className="mt-1 text-xs font-mono text-muted-foreground">
              Expediente {item.expediente.id_publico} · Solicitud{" "}
              {item.expediente.id_publico}
            </p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span
            className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold ${estadoToken?.badgeClass ?? "bg-muted text-muted-foreground border-border"}`}
          >
            {estadoToken?.label ?? item.estado}
          </span>
          <span className="inline-flex items-center rounded-md border border-border bg-muted/40 px-2 py-0.5 text-xs font-medium text-muted-foreground">
            {prioridadToken?.label ?? item.prioridad}
          </span>
          {item.expediente?.id && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 gap-1.5 text-xs"
              onClick={() => router.push(`/expedientes/${item.expediente.id}`)}
            >
              <LinkIcon className="h-3 w-3" aria-hidden="true" />
              <span className="hidden sm:inline">Ver Expediente</span>
              <span className="sm:hidden">Expediente</span>
            </Button>
          )}
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 text-sm @md:grid-cols-3 @4xl:grid-cols-6">
        <div className="flex flex-col gap-0.5">
          <dt className="flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            Registrada
          </dt>
          <dd className="font-medium">
            <time dateTime={item.fecha_registro}>
              {formatDate(item.fecha_registro)}
            </time>
          </dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            Inicio de gestión
          </dt>
          <dd className="font-medium">
            {item.fecha_inicio_gestion ? (
              <time dateTime={item.fecha_inicio_gestion}>
                {formatDate(item.fecha_inicio_gestion)}
              </time>
            ) : (
              <span className="text-muted-foreground">No definida</span>
            )}
          </dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            Fecha límite
          </dt>
          <dd className="font-medium">
            {item.fecha_limite ? (
              <time dateTime={item.fecha_limite}>
                {formatDate(item.fecha_limite)}
              </time>
            ) : (
              <span className="text-muted-foreground">No definida</span>
            )}
          </dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="flex items-center gap-1 text-xs text-muted-foreground">
            <Layers className="h-3 w-3" />
            Áreas activas
          </dt>
          <dd className="font-medium">{activeAreaCount}</dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="flex items-center gap-1 text-xs text-muted-foreground">
            <Layers className="h-3 w-3" />
            Etapas activas
          </dt>
          <dd className="font-medium">{activeEtapaCount}</dd>
        </div>
        <div className="flex flex-col gap-0.5">
          <dt className="flex items-center gap-1 text-xs text-muted-foreground">
            <Users className="h-3 w-3" />
            Participantes activos
          </dt>
          <dd className="font-medium">{activeParticipantCount}</dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-col gap-3 border-t border-border pt-3 @xl:flex-row @xl:justify-between @xl:gap-6">
        <div className="flex min-w-0 flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground">
            Responsable
          </span>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
            {responsabilidad.principal.length === 0 &&
            responsabilidad.adjunta.length === 0 ? (
              <span className="text-muted-foreground">Sin áreas asignadas</span>
            ) : (
              <>
                {responsabilidad.principal.map((area) => (
                  <span
                    key={area.nombre}
                    className="inline-flex items-center gap-1.5"
                  >
                    <span className="font-medium">{area.nombre}</span>
                    <span className="rounded-md border border-border bg-muted/40 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                      {TIPO_PARTICIPACION[area.tipo]?.label ?? area.tipo}
                    </span>
                  </span>
                ))}
                {responsabilidad.adjunta.map((area) => (
                  <span
                    key={area.nombre}
                    className="inline-flex items-center gap-1.5"
                  >
                    <span className="font-medium text-muted-foreground">
                      {area.nombre}
                    </span>
                    <span className="rounded-md border border-border bg-muted/40 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                      {TIPO_PARTICIPACION[area.tipo]?.label ?? area.tipo}
                    </span>
                  </span>
                ))}
              </>
            )}
          </div>
        </div>
        {ultimoMovimiento && (
          <div className="flex min-w-0 flex-col gap-1">
            <span className="text-xs font-medium text-muted-foreground">
              Último movimiento
            </span>
            <span className="text-sm text-foreground">{ultimoMovimiento}</span>
          </div>
        )}
      </div>
    </section>
  );
}
