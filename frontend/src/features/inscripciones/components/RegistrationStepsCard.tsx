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
  /**
   * `compact` adapts the guide to a narrow sidebar: tighter spacing and a
   * shorter footer. The steps, their states and their actions stay the same.
   */
  variant?: "default" | "compact";
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
  BORRADOR: "Borrador",
  RECIBIDA: "Recibida",
  EN_REVISION: "En revision",
  OBSERVADA: "Observada",
  VALIDADA: "Validada",
  CONFIRMADA: "Confirmada",
  RECHAZADA: "Rechazada",
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
  variant = "default",
}: RegistrationStepsCardProps) {
  // The guide is secondary information: in the compact (sidebar) variant it
  // starts collapsed so the mobile flow reaches the roster faster.
  const [expanded, setExpanded] = useState(variant !== "compact");
  const compact = variant === "compact";

  // ── Compute step states from presenter data ───────────────────────────
  // Payment step state derives from resumen_pago (backend presenter), NOT from
  // Inscripcion.estado inference. This ensures the step reflects actual
  // commercial activity regardless of the inscription's administrative state.
  const resumenPago = inscripcion.resumen_pago;
  const resumenEquipos = inscripcion.resumen_equipos;

  const equipos = inscripcion.equipos;
  const totalEquipos = equipos.length;
  const equiposConJugadores = equipos.filter(
    (e: EquipoItem) => e.participantes.length > 0,
  ).length;
  const totalJugadores = equipos.reduce(
    (acc, e) => acc + e.participantes.length,
    0,
  );

  // Roster display only — does NOT block commercial actions.
  const jugadoresCompletos =
    resumenEquipos.completos === totalEquipos && totalEquipos > 0;

  // Payment state from presenter — never inferred from Inscripcion.estado.
  // estado_mensaje values: "Sin actividades de pago" | "Pago pendiente" |
  // "Pago parcial" | "Pago confirmado"
  const pagoEstadoMensaje =
    resumenPago.estado_mensaje ?? "Sin actividades de pago";
  const pagoHecho = pagoEstadoMensaje === "Pago confirmado";
  const pagoParcial = pagoEstadoMensaje === "Pago parcial";
  const pagoPendiente = pagoEstadoMensaje === "Pago pendiente";
  const sinActividadPago = pagoEstadoMensaje === "Sin actividades de pago";

  // Administrative estado still governs confirmation step and payment blocking.
  const estado = inscripcion.estado;
  const pagoBloqueado = estado === "CANCELADA" || estado === "RECHAZADA";
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
        : pagoParcial
          ? "Pago parcial"
          : "Completa el pago",
      description: pagoHecho
        ? "El comité recibió la confirmación del pago."
        : pagoParcial
          ? "Has cubierto parte de tu inscripción. Completa el pago restante."
          : sinActividadPago
            ? "Registra tu primera compra para activar el proceso de pago."
            : IZIPAY_ENABLED
              ? "Paga con tarjeta o Yape desde Izipay para que el comité valide tu inscripción."
              : "Coordina el pago con el comité organizador.",
      icon: CreditCard,
      // Payment step is blocked only by inscription cancellation/rejection.
      // Roster completeness (INCOMPLETO) NEVER blocks payment — confirmed in Phase 7.
      state: pagoHecho
        ? "done"
        : pagoBloqueado
          ? "blocked"
          : pagoPendiente || pagoParcial
            ? "active"
            : sinActividadPago
              ? "pending"
              : "pending",
      hint:
        !pagoHecho && !pagoBloqueado && IZIPAY_ENABLED
          ? "Tip: el botón 'Proceder al Pago' aparece arriba."
          : undefined,
      actionLabel:
        !pagoHecho && !pagoBloqueado && IZIPAY_ENABLED && onOpenPayment
          ? "Pagar ahora"
          : undefined,
      onAction:
        !pagoHecho && !pagoBloqueado && IZIPAY_ENABLED
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
      <div className="pointer-events-none absolute -right-12 -top-12 size-40 rounded-full bg-sky-300/30 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-12 -left-12 size-40 rounded-full bg-violet-300/30 blur-3xl" />

      <div className="relative">
        {/* Header */}
        <header
          className={cn(
            "flex items-center justify-between gap-3",
            compact ? "px-4 py-3" : "px-5 py-4 sm:px-6",
          )}
        >
          <div className="flex min-w-0 items-center gap-3">
            <div
              className={cn(
                "flex shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 to-violet-500 text-white shadow-md",
                compact ? "size-9" : "size-11",
              )}
            >
              <ListChecks className={compact ? "size-4" : "size-5"} />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-sky-700">
                Guia
              </p>
              <h3
                className={cn(
                  "truncate font-black tracking-tight text-slate-900",
                  compact ? "text-sm" : "text-base",
                )}
              >
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
            aria-expanded={expanded}
          >
            {expanded ? "Ocultar" : "Ver"}
          </Button>
        </header>

        {/* Progress bar */}
        <div className={cn("pb-2", compact ? "px-4" : "px-5 sm:px-6")}>
          <div className="flex items-center justify-between gap-2 text-xs">
            <span className="font-semibold text-slate-600">
              {completedCount} de {steps.length} pasos completos
            </span>
            <span className="font-black tabular-nums text-slate-900">
              {progressPct}%
            </span>
          </div>
          <div
            className={cn(
              "mt-2 w-full overflow-hidden rounded-full bg-slate-200/70",
              compact ? "h-1.5" : "h-2",
            )}
            role="progressbar"
            aria-valuenow={completedCount}
            aria-valuemin={0}
            aria-valuemax={steps.length}
            aria-label="Pasos completados"
          >
            <div
              className="h-full rounded-full bg-gradient-to-r from-sky-500 via-violet-500 to-emerald-500 transition-all duration-700"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        {/* Steps body */}
        {expanded && (
          <ol
            className={cn(
              "space-y-1",
              compact ? "px-2 pb-3" : "px-3 pb-4 sm:px-4",
            )}
          >
            {steps.map((step, idx) => (
              <StepRow
                key={step.id}
                step={step}
                isLast={idx === steps.length - 1}
                compact={compact}
              />
            ))}
          </ol>
        )}

        {/* Footer info */}
        {expanded && (
          <footer
            className={cn(
              "mx-4 mb-4 flex items-start gap-2 rounded-2xl border border-slate-200/70 bg-white/60 text-xs text-slate-600",
              compact ? "p-2.5" : "p-3",
            )}
          >
            <Info className="mt-0.5 size-4 shrink-0 text-sky-600" />
            <p className="leading-relaxed">
              {compact ? (
                <>
                  Revisa las{" "}
                  <span className="font-semibold text-slate-900">
                    bases del evento
                  </span>{" "}
                  o contacta al comité organizador. Estado actual:{" "}
                  <span className="font-bold uppercase tracking-wide text-slate-900">
                    {STATUS_LABELS[estado] ?? estado}
                  </span>
                  .
                </>
              ) : (
                <>
                  ¿Tienes dudas? Revisa las{" "}
                  <span className="font-semibold text-slate-900">
                    bases del evento
                  </span>{" "}
                  o contacta al comité organizador. Estado actual:{" "}
                  <span className="font-bold uppercase tracking-wide text-slate-900">
                    {STATUS_LABELS[estado] ?? estado}
                  </span>
                  .
                </>
              )}
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
  compact?: boolean;
}

function StepRow({ step, isLast, compact = false }: StepRowProps) {
  const Icon = step.icon;
  const stateStyle = STATE_STYLES[step.state];
  const markerSize = compact ? "size-8" : "size-9";
  const markerOffset = compact ? "left-[15px] top-8" : "left-[18px] top-9";

  return (
    <li className="relative flex gap-3 pl-1">
      {/* Connector line */}
      {!isLast && (
        <span
          className={cn(
            "absolute w-px",
            markerOffset,
            "bottom-0",
            step.state === "done"
              ? "bg-gradient-to-b from-emerald-300 to-emerald-200"
              : "bg-slate-200",
          )}
          aria-hidden="true"
        />
      )}

      <div
        className={cn(
          "relative z-10 flex shrink-0 items-center justify-center rounded-full shadow-sm transition-all",
          markerSize,
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

      <div className="min-w-0 flex-1 pt-0.5 pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p
              className={cn(
                "font-bold leading-tight",
                compact ? "text-xs" : "text-sm",
                stateStyle.titleColor,
              )}
            >
              {step.title}
            </p>
            <p
              className={cn(
                "mt-0.5 leading-snug",
                compact ? "text-xs" : "text-sm",
                stateStyle.descColor,
              )}
            >
              {step.description}
            </p>
            {step.hint && (
              <p className="mt-1 text-xs leading-snug italic text-sky-700">
                {step.hint}
              </p>
            )}
          </div>
          {step.actionLabel && step.onAction && (
            <button
              type="button"
              onClick={step.onAction}
              className="shrink-0 text-[11px] font-bold uppercase tracking-wider text-sky-700 underline underline-offset-4 transition-colors hover:text-sky-900"
            >
              {step.actionLabel}
            </button>
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
    descColor: "text-slate-500",
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
