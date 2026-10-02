"use client";

import {
  Check,
  CircleAlert,
  Clock,
  CreditCard,
  Info,
  ListChecks,
  Package,
  Sparkles,
  Users,
} from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { InscripcionDetalleOut } from "../services/inscripcion.service";

type EquipoItem = InscripcionDetalleOut["equipos"][number];

interface RegistrationStepsCardProps {
  inscripcion: InscripcionDetalleOut;
  /** IDs de equipos expandidos — el card usa esto para mostrar tips relevantes. */
  expandedEquipoIds?: Record<string, boolean>;
  onScrollToTeams?: () => void;
  onOpenPayment?: () => void;
  className?: string;
}

type StepState = "done" | "active" | "pending" | "blocked";

interface StepDescriptor {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  state: StepState;
  hint?: string;
  actionLabel?: string;
  onAction?: () => void;
}

const IZIPAY_ENABLED = process.env.NEXT_PUBLIC_IZIPAY_ENABLED === "true";

const STATUS_LABELS: Record<string, string> = {
  RECIBIDA: "Recibida",
  PENDIENTE: "Pendiente",
  PAGO_PENDIENTE: "Pago pendiente",
  PAGADA: "Pagada",
  CONFIRMADA: "Confirmada",
  CANCELADA: "Cancelada",
};

/**
 * Card informativo con los pasos para completar una inscripción.
 *
 * Calcula el estado de cada paso a partir de los datos de la inscripción y
 * muestra tips contextuales con acciones para continuar el flujo.
 */
export function RegistrationStepsCard({
  inscripcion,
  onScrollToTeams,
  onOpenPayment,
  className,
}: RegistrationStepsCardProps) {
  const [expanded, setExpanded] = useState(true);

  // ── Compute step states ───────────────────────────────────────────────
  const equipos = inscripcion.equipos;
  const totalEquipos = equipos.length;
  const equiposConJugadores = equipos.filter(
    (e: EquipoItem) => e.participantes.length > 0,
  ).length;
  const totalJugadores = equipos.reduce(
    (acc, e) => acc + e.participantes.length,
    0,
  );

  const jugadoresCompletos =
    equiposConJugadores === totalEquipos && totalEquipos > 0;
  const estado = inscripcion.estado;
  const pagoBloqueado = estado === "CANCELADA";
  const pagoHecho = estado === "PAGADA" || estado === "CONFIRMADA";
  const pagoEnCurso = estado === "PAGO_PENDIENTE";
  const confirmada = estado === "CONFIRMADA";

  const steps: StepDescriptor[] = [
    {
      id: "crear",
      title: "Inscripción creada",
      description: "Tu preinscripción está registrada en el sistema.",
      icon: Package,
      state: "done",
    },
    {
      id: "jugadores",
      title:
        totalEquipos > 0
          ? `Jugadores agregados (${equiposConJugadores}/${totalEquipos})`
          : "Agrega jugadores a tus equipos",
      description: jugadoresCompletos
        ? `Todos los equipos tienen ${totalJugadores} jugadores en total.`
        : "Agrega al menos un jugador por cada equipo incluido en tu paquete.",
      icon: Users,
      state: jugadoresCompletos ? "done" : "active",
      hint: jugadoresCompletos
        ? undefined
        : "Tip: usa el botón + en cada equipo, o el ícono de usuario y sumarte tú mismo.",
      actionLabel: jugadoresCompletos ? undefined : "Ir a los equipos",
      onAction: jugadoresCompletos ? undefined : onScrollToTeams,
    },
    {
      id: "pago",
      title: pagoHecho
        ? "Pago completado"
        : pagoEnCurso
          ? "Pago en proceso"
          : "Completa el pago",
      description: pagoHecho
        ? "El comité recibió la confirmación del pago."
        : pagoEnCurso
          ? "Tu pago está siendo procesado por Izipay."
          : IZIPAY_ENABLED
            ? "Paga con tarjeta o Yape desde Izipay para que el comité valide tu inscripción."
            : "Coordina el pago con el comité organizador.",
      icon: CreditCard,
      state: pagoHecho
        ? "done"
        : pagoBloqueado
          ? "blocked"
          : jugadoresCompletos
            ? pagoEnCurso
              ? "active"
              : "active"
            : "pending",
      hint:
        !pagoHecho && jugadoresCompletos && IZIPAY_ENABLED
          ? "Tip: el botón 'Proceder al Pago' aparece arriba cuando los equipos están listos."
          : undefined,
      actionLabel:
        !pagoHecho && jugadoresCompletos && IZIPAY_ENABLED && onOpenPayment
          ? "Pagar ahora"
          : undefined,
      onAction:
        !pagoHecho && jugadoresCompletos && IZIPAY_ENABLED
          ? onOpenPayment
          : undefined,
    },
    {
      id: "confirmacion",
      title: confirmada ? "Inscripción confirmada" : "Confirma el comité",
      description: confirmada
        ? "¡Todo listo! Tu inscripción está validada."
        : "El comité organizador validará tu inscripción y envió al equipo una confirmación final.",
      icon: confirmada ? Sparkles : Clock,
      state: confirmada ? "done" : pagoHecho ? "active" : "pending",
    },
  ];

  const completedCount = steps.filter((s) => s.state === "done").length;
  const progressPct = Math.round((completedCount / steps.length) * 100);

  return (
    <section
      className={cn(
        "relative overflow-hidden rounded-3xl border border-sky-200/70 bg-gradient-to-br from-sky-50/80 via-white to-violet-50/70 shadow-sm",
        className,
      )}
    >
      <div className="pointer-events-none absolute -right-12 -top-12 h-40 w-40 rounded-full bg-sky-300/30 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-12 -left-12 h-40 w-40 rounded-full bg-violet-300/30 blur-3xl" />

      <div className="relative">
        {/* Header */}
        <header className="flex items-center justify-between gap-3 px-5 py-4 sm:px-6">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 to-violet-500 text-white shadow-md">
              <ListChecks className="size-5" />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-sky-700">
                Guía
              </p>
              <h3 className="text-base font-black tracking-tight text-slate-900 truncate">
                Cómo completar tu inscripción
              </h3>
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setExpanded((v) => !v)}
            className="shrink-0 rounded-full text-xs font-bold uppercase tracking-wider text-slate-600"
          >
            {expanded ? "Ocultar" : "Ver"}
          </Button>
        </header>

        {/* Progress bar */}
        <div className="px-5 sm:px-6 pb-2">
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="font-semibold text-slate-600">
              {completedCount} de {steps.length} pasos completos
            </span>
            <span className="font-black tabular-nums text-slate-900">
              {progressPct}%
            </span>
          </div>
          <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200/70">
            <div
              className="h-full rounded-full bg-gradient-to-r from-sky-500 via-violet-500 to-emerald-500 transition-all duration-700"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        {/* Steps body */}
        {expanded && (
          <ol className="space-y-1 px-3 pb-4 sm:px-4">
            {steps.map((step, idx) => (
              <StepRow
                key={step.id}
                step={step}
                isLast={idx === steps.length - 1}
              />
            ))}
          </ol>
        )}

        {/* Footer info */}
        {expanded && (
          <footer className="mx-5 mb-5 sm:mx-6 flex items-start gap-2 rounded-2xl border border-slate-200/70 bg-white/60 p-3 text-xs text-slate-600">
            <Info className="size-4 shrink-0 mt-0.5 text-sky-600" />
            <p className="leading-relaxed">
              ¿Tienes dudas? Revisa las{" "}
              <span className="font-semibold text-slate-900">
                bases del evento
              </span>{" "}
              o contacta al comité organizador. Estado actual:{" "}
              <span className="font-bold uppercase tracking-wide text-slate-900">
                {STATUS_LABELS[estado] ?? estado}
              </span>
              .
            </p>
          </footer>
        )}
      </div>
    </section>
  );
}

interface StepRowProps {
  step: StepDescriptor;
  isLast: boolean;
}

function StepRow({ step, isLast }: StepRowProps) {
  const Icon = step.icon;
  const stateStyle = STATE_STYLES[step.state];

  return (
    <li className="relative flex gap-3 pl-1">
      {/* Connector line */}
      {!isLast && (
        <span
          className={cn(
            "absolute left-[18px] top-9 bottom-0 w-px",
            step.state === "done"
              ? "bg-gradient-to-b from-emerald-300 to-emerald-200"
              : "bg-slate-200",
          )}
          aria-hidden="true"
        />
      )}

      <div
        className={cn(
          "relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full shadow-sm transition-all",
          stateStyle.iconBg,
        )}
      >
        {step.state === "done" ? (
          <Check className="size-4 text-white" strokeWidth={3} />
        ) : step.state === "blocked" ? (
          <CircleAlert className="size-4 text-white" />
        ) : (
          <Icon className={cn("size-4", stateStyle.iconColor)} />
        )}
      </div>

      <div className="flex-1 min-w-0 pt-1 pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p
              className={cn(
                "text-sm font-bold leading-tight",
                stateStyle.titleColor,
              )}
            >
              {step.title}
            </p>
            <p
              className={cn(
                "text-xs mt-0.5 leading-snug",
                stateStyle.descColor,
              )}
            >
              {step.description}
            </p>
            {step.hint && (
              <p className="text-[11px] mt-1 text-sky-700 leading-snug italic">
                {step.hint}
              </p>
            )}
          </div>
          {step.actionLabel && step.onAction && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={step.onAction}
              className="shrink-0 rounded-full text-xs font-bold uppercase tracking-wider border-sky-300 text-sky-700 hover:bg-sky-50"
            >
              {step.actionLabel}
            </Button>
          )}
        </div>
      </div>
    </li>
  );
}

const STATE_STYLES: Record<
  StepState,
  {
    iconBg: string;
    iconColor: string;
    titleColor: string;
    descColor: string;
  }
> = {
  done: {
    iconBg: "bg-gradient-to-br from-emerald-400 to-emerald-600",
    iconColor: "text-white",
    titleColor: "text-emerald-900",
    descColor: "text-slate-600",
  },
  active: {
    iconBg: "bg-gradient-to-br from-sky-400 to-sky-600",
    iconColor: "text-white",
    titleColor: "text-slate-900",
    descColor: "text-slate-600",
  },
  pending: {
    iconBg: "bg-slate-200",
    iconColor: "text-slate-400",
    titleColor: "text-slate-500",
    descColor: "text-slate-400",
  },
  blocked: {
    iconBg: "bg-gradient-to-br from-rose-400 to-rose-600",
    iconColor: "text-white",
    titleColor: "text-rose-900",
    descColor: "text-rose-700",
  },
};

// Re-export for backwards compat / testing
export type { StepState };
