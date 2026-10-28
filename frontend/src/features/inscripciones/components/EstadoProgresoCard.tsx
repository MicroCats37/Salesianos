"use client";

import {
  Check,
  CircleAlert,
  ClipboardCheck,
  CreditCard,
  Package,
  Sparkles,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { InscripcionDetalleOut } from "../services/inscripcion.service";
import {
  estadoInscripcionMeta,
  InscripcionEstadoBadge,
} from "./InscripcionEstadoBadge";

interface EstadoProgresoCardProps {
  inscripcion: InscripcionDetalleOut;
  /** Scrolls to the teams section — the only action this panel offers. */
  onScrollToTeams?: () => void;
  className?: string;
}

type StepState = "done" | "active" | "pending" | "blocked";

interface StepDescriptor {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  state: StepState;
  actionLabel?: string;
  onAction?: () => void;
}

const IZIPAY_ENABLED = process.env.NEXT_PUBLIC_IZIPAY_ENABLED === "true";

/**
 * Single panel that answers "how is my inscription going?".
 *
 * It is the ONLY place on the page that shows:
 *
 * - the administrative state (badge + plain-language meaning),
 * - the observation of the committee,
 * - the progress of the registration flow (one progress bar + one checklist).
 *
 * Every counter it renders comes from the backend presenter
 * (`resumen_equipos`, `resumen_pago`, `estado`) — the panel never counts
 * anything locally. The commercial amounts live in `ResumenPagoCard` and the
 * payment action lives in `PaymentCallout`, so no fact is repeated.
 */
export function EstadoProgresoCard({
  inscripcion,
  onScrollToTeams,
  className,
}: EstadoProgresoCardProps) {
  const meta = estadoInscripcionMeta(inscripcion.estado);

  const resumenPago = inscripcion.resumen_pago;
  const resumenEquipos = inscripcion.resumen_equipos;
  const totalEquipos = inscripcion.equipos.length;
  const equiposCompletos = resumenEquipos.completos;
  const rosterCompleto = totalEquipos > 0 && equiposCompletos === totalEquipos;

  // Payment state comes from the presenter, never from `Inscripcion.estado`.
  const pagoEstado = resumenPago.estado_mensaje ?? "Sin actividades de pago";
  const pagoHecho = pagoEstado === "Pago confirmado";
  const pagoParcial = pagoEstado === "Pago parcial";
  const pagoPendiente = pagoEstado === "Pago pendiente";
  const sinActividadPago = pagoEstado === "Sin actividades de pago";

  // The administrative state only vetoes the payment, it never describes it.
  const pagoBloqueado =
    inscripcion.estado === "CANCELADA" || inscripcion.estado === "RECHAZADA";
  const confirmada = inscripcion.estado === "CONFIRMADA";

  const steps: StepDescriptor[] = [
    {
      id: "crear",
      title: "Inscripcion creada",
      description: "Tu preinscripcion quedo registrada en el sistema.",
      icon: Package,
      state: "done",
    },
    {
      id: "jugadores",
      title: `Equipos completos (${equiposCompletos}/${totalEquipos})`,
      description: rosterCompleto
        ? "Todos los equipos tienen el numero de jugadores que pide su disciplina."
        : "Agrega los jugadores que faltan en cada equipo de tu paquete.",
      icon: Users,
      state: rosterCompleto ? "done" : "active",
      actionLabel: rosterCompleto ? undefined : "Ir a los equipos",
      onAction: rosterCompleto ? undefined : onScrollToTeams,
    },
    {
      id: "pago",
      title: "Pago",
      description: pagoHecho
        ? "No tienes nada pendiente que pagar."
        : pagoBloqueado
          ? "Esta inscripcion esta cancelada o rechazada, asi que no admite pagos."
          : sinActividadPago
            ? "Registra tu primera compra para activar el proceso de pago."
            : IZIPAY_ENABLED
              ? "Paga con tarjeta o Yape desde Izipay para que el comite valide tu inscripcion."
              : "Coordina el pago con el comite organizador.",
      icon: CreditCard,
      state: pagoHecho
        ? "done"
        : pagoBloqueado
          ? "blocked"
          : pagoPendiente || pagoParcial
            ? "active"
            : "pending",
    },
    {
      id: "confirmacion",
      title: "Confirmacion del comite",
      description: confirmada
        ? "Tu inscripcion esta validada y el equipo queda inscrito en el festival."
        : "El comite organizador valida tu inscripcion y envia la confirmacion final.",
      icon: confirmada ? Sparkles : ClipboardCheck,
      state: confirmada ? "done" : pagoHecho ? "active" : "pending",
    },
  ];

  const completedCount = steps.filter((step) => step.state === "done").length;
  const progressPct = Math.round((completedCount / steps.length) * 100);

  return (
    <section
      aria-labelledby="estado-progreso-titulo"
      className={cn(
        "rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200/70 sm:p-6",
        className,
      )}
    >
      {/* ── Estado ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#312e8e]">
            Estado y progreso
          </p>
          <h2
            id="estado-progreso-titulo"
            className="mt-1 text-xl font-black tracking-tight text-[#17214b] sm:text-2xl"
          >
            {meta.label}
          </h2>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600">
            {meta.description}
          </p>
        </div>
        <InscripcionEstadoBadge estado={inscripcion.estado} size="lg" />
      </div>

      {inscripcion.observacion && (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-3">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-700">
            Observacion del Comite
          </p>
          <p className="mt-1 text-xs leading-relaxed text-amber-900">
            {inscripcion.observacion}
          </p>
        </div>
      )}

      {/* ── One progress bar for the whole flow ── */}
      <div className="mt-5 rounded-2xl border border-slate-200/70 bg-slate-50/70 p-4">
        <div className="flex items-center justify-between gap-2 text-xs">
          <span className="font-semibold text-slate-600">
            {completedCount} de {steps.length} pasos completados
          </span>
          <span className="font-black tabular-nums text-slate-900">
            {progressPct}%
          </span>
        </div>
        <div
          className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-200/70"
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

      {/* ── One checklist for the whole flow ── */}
      <ol className="mt-4 space-y-1">
        {steps.map((step, index) => (
          <StepRow
            key={step.id}
            step={step}
            isLast={index === steps.length - 1}
          />
        ))}
      </ol>
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
      {!isLast && (
        <span
          className={cn(
            "absolute left-[15px] top-8 bottom-0 w-px",
            step.state === "done"
              ? "bg-gradient-to-b from-emerald-300 to-emerald-200"
              : "bg-slate-200",
          )}
          aria-hidden="true"
        />
      )}

      <div
        className={cn(
          "relative z-10 flex size-8 shrink-0 items-center justify-center rounded-full shadow-sm",
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
        <div className="flex items-start justify-between gap-3">
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
                "mt-0.5 text-sm leading-snug",
                stateStyle.descColor,
              )}
            >
              {step.description}
            </p>
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
