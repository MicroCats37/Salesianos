"use client";

import { CheckCircle2, Clock, Lock, UserCheck, UserPlus } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { PoolEntryOut } from "../services/pool.service";
import {
  type PoolEstado,
  poolEsAsignable,
  poolEstadoDeEntrada,
} from "../utils/pool.estado";

/**
 * Visual configuration of every pool eligibility state.
 *
 * Shared by the pool card and the participant selector so the responsible
 * sees ONE visual language, not two.
 */
export const estadoConfig: Record<
  PoolEstado,
  {
    label: string;
    description: string;
    icon: React.ReactNode;
    chip: string;
    border: string;
  }
> = {
  listo: {
    label: "Listo para equipo",
    description: "Tiene cupo pagado: puede asignarse a un equipo.",
    icon: <CheckCircle2 className="size-3" />,
    chip: "bg-emerald-50 text-emerald-700 border-emerald-200",
    border: "border-emerald-200/70",
  },
  esperando_pago: {
    label: "Esperando pago",
    description:
      "La inscripcion todavia no tiene cupo pagado: el pago habilita su cupo.",
    icon: <Clock className="size-3" />,
    chip: "bg-amber-50 text-amber-700 border-amber-200",
    border: "border-amber-200/70",
  },
  sin_capacidad: {
    label: "Sin cupo pagado",
    description:
      "Los cupos pagados estan agotados: solicita una ampliacion de cupos.",
    icon: <Lock className="size-3" />,
    chip: "bg-rose-50 text-rose-700 border-rose-200",
    border: "border-rose-200/70",
  },
  cupo_por_asignar: {
    label: "Cupo por asignar",
    description:
      "El pago ya esta registrado y hay cupos pagados libres, pero este participante todavia no tiene su cupo asignado.",
    icon: <Clock className="size-3" />,
    chip: "bg-sky-50 text-sky-700 border-sky-200",
    border: "border-sky-200/70",
  },
  bloqueado: {
    label: "Sin cupo disponible",
    description: "No hay cupos pagados disponibles.",
    icon: <Lock className="size-3" />,
    chip: "bg-rose-50 text-rose-700 border-rose-200",
    border: "border-rose-200/70",
  },
};

export interface PoolParticipanteCardProps {
  /** Backend pool entry — the single source of assignment eligibility. */
  entry: PoolEntryOut;
  /**
   * Opens the participant selector with this person preselected. When it is
   * not provided the card is read-only.
   */
  onAsignar?: (inscripcionPersonaId: string) => void;
  /** Disable the action (e.g. there is no team to assign to). */
  sinDestino?: boolean;
}

/**
 * Card for one pre-registered participant of the pool.
 *
 * The action is only rendered when the backend says the person has an active
 * cup (`tiene_cupo_activo`). Blocked participants show a lock and the
 * backend-provided reason instead, so the UI never offers an action the
 * backend would reject.
 */
export function PoolParticipanteCard({
  entry,
  onAsignar,
  sinDestino = false,
}: PoolParticipanteCardProps) {
  const estado = poolEstadoDeEntrada(entry);
  const config = estadoConfig[estado];
  const puedeAsignar = poolEsAsignable(entry, sinDestino) && !!onAsignar;

  const nombre = entry.persona.nombre;

  return (
    <TooltipProvider delayDuration={150} skipDelayDuration={300}>
      <div
        className={cn(
          "flex items-start gap-3 rounded-xl border bg-white px-3 py-2.5 shadow-sm transition-colors",
          config.border,
        )}
      >
        {/* Identity */}
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium text-gray-900">{nombre}</p>
          <p className="text-xs text-gray-500">
            {entry.persona.numero_documento || "—"}
          </p>
          {estado !== "listo" && entry.motivo_bloqueo && (
            <p className="mt-0.5 text-xs text-slate-500">
              {entry.motivo_bloqueo}
            </p>
          )}
        </div>

        {/* Eligibility badge */}
        <span
          className={cn(
            "inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold",
            config.chip,
          )}
          title={`Estado: ${config.label}`}
        >
          {config.icon}
          {config.label}
        </span>

        {/* Assignment action — replaces the drag handle */}
        {puedeAsignar ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={() => onAsignar?.(entry.id)}
                aria-label={`Asignar a ${nombre} a un equipo`}
                className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-lg border border-primary/30 px-2.5 text-xs font-semibold text-primary transition-colors hover:bg-primary/10"
              >
                <UserPlus className="size-3.5" />
                <span className="hidden sm:inline">Asignar</span>
              </button>
            </TooltipTrigger>
            <TooltipContent side="left">
              <p className="font-semibold">Asignar a un equipo</p>
              <p className="text-[11px] opacity-80">
                Abre el selector de participantes del equipo
              </p>
            </TooltipContent>
          </Tooltip>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <span
                role="img"
                aria-label={
                  sinDestino
                    ? "Asignacion no disponible: no hay equipos para asignar"
                    : `Asignacion no disponible: ${config.description}`
                }
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted-foreground/60"
              >
                <Lock className="size-3.5" />
              </span>
            </TooltipTrigger>
            <TooltipContent side="left">
              <p className="font-semibold">{config.label}</p>
              <p className="text-[11px] opacity-80">
                {entry.motivo_bloqueo ?? config.description}
              </p>
            </TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  );
}

/**
 * Read-only row for a participant that already sits in a team.
 *
 * Kept visually distinct from the actionable pool cards: no action, no
 * eligibility badge — only where the person ended up.
 *
 * The row is keyed by the PARTICIPATION id (not by the person): one person can
 * play in several disciplines, so one row per participation is the only shape
 * that keeps the React keys unique.
 */
export function ParticipanteColocadoRow({
  nombre,
  equipoNombre,
  disciplinaSigla,
}: {
  nombre: string;
  equipoNombre: string;
  disciplinaSigla?: string | null;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50/60 px-3 py-2.5">
      <span
        className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500"
        aria-hidden="true"
      >
        <UserCheck className="size-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium text-slate-700">{nombre}</p>
        <p className="truncate text-xs text-slate-500">
          Ya asignado en {equipoNombre}
        </p>
      </div>
      {disciplinaSigla && (
        <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-violet-200 bg-violet-50 px-2 py-0.5 text-xs font-semibold text-violet-700">
          {disciplinaSigla}
        </span>
      )}
      <span
        className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2 py-0.5 text-xs font-semibold text-slate-600"
        title="Estado: Ya asignado"
      >
        <UserCheck className="size-3" />
        Ya asignado
      </span>
    </div>
  );
}
