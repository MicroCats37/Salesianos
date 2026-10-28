"use client";

import {
  BadgeDollarSign,
  Ban,
  CheckCircle2,
  Clock,
  CreditCard,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ResumenPagoOut } from "../services/inscripcion.service";
import { activacionPendiente as hayActivacionPendiente } from "../utils/pago.estado";

interface ResumenPagoCardProps {
  resumen: ResumenPagoOut;
  className?: string;
  /**
   * `compact` adapts the card to a narrow sidebar: two columns of amounts
   * instead of four and a stacked purchase row.
   */
  variant?: "default" | "compact";
}

/**
 * Commercial / payment summary card rendered from presenter-derived `ResumenPagoOut`.
 * Displays global commercial state, aggregate amounts/capacity, and purchase list.
 *
 * Accessibility: the activation-pending banner is a live region (`<output>`),
 * and every purchase badge prefixes its state with a screen-reader-only label.
 * No business logic here — purely renders fields provided by the backend presenter.
 * Does NOT display `metadata` from any purchase or payment order.
 */
export function ResumenPagoCard({
  resumen,
  className,
  variant = "default",
}: ResumenPagoCardProps) {
  const compact = variant === "compact";
  const {
    total_compras,
    total_contratado,
    total_pagado,
    total_pagado_cantidad,
    compras_pendientes,
    compras_pagadas,
    compras_canceladas,
    disponible_pagado,
    estado_mensaje,
    compras,
  } = resumen;

  // ── State classification ───────────────────────────────────────────────────
  const hasNoCompras = total_compras === 0;
  const allCancelled =
    total_compras > 0 && compras_canceladas === total_compras;
  const allPaid =
    total_compras > 0 &&
    compras_pagadas === total_compras &&
    compras_pendientes === 0;
  const hasPartial =
    !hasNoCompras && !allCancelled && !allPaid && total_pagado_cantidad > 0;
  const hasPending = compras_pendientes > 0;

  // The payment was recorded but the commercial activation is not complete:
  // the purchase is still PENDIENTE while its payment order is already paid.
  // The card must say so instead of claiming a completed payment.
  const activacionPendiente = hayActivacionPendiente(resumen);

  // ── Colour palette per state ───────────────────────────────────────────────
  // Mirrors the amber/emerald/slate language used by `EstadoProgresoCard` and
  // the roster badges of `EquipoCard` so the page feels cohesive.
  const stateColor =
    allPaid && !allCancelled
      ? "border-emerald-200 bg-emerald-50/60"
      : hasPartial
        ? "border-amber-200 bg-amber-50/60"
        : hasPending
          ? "border-amber-200 bg-amber-50/40"
          : allCancelled
            ? "border-rose-100 bg-rose-50/40"
            : "border-slate-200/70 bg-white";

  const stateIconColor =
    allPaid && !allCancelled
      ? "text-emerald-600"
      : hasPartial
        ? "text-amber-600"
        : hasPending
          ? "text-amber-500"
          : allCancelled
            ? "text-rose-500"
            : "text-slate-400";

  const stateLabelColor =
    allPaid && !allCancelled
      ? "text-emerald-800"
      : hasPartial
        ? "text-amber-800"
        : hasPending
          ? "text-amber-700"
          : allCancelled
            ? "text-rose-800"
            : "text-slate-600";

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <section
      className={cn(
        "overflow-hidden rounded-3xl border shadow-sm",
        stateColor,
        className,
      )}
    >
      {/* ── Header ── */}
      <div className="flex items-center gap-3 border-b border-black/5 px-4 py-3">
        <div
          className={cn(
            "flex size-9 shrink-0 items-center justify-center rounded-xl",
            allPaid && !allCancelled
              ? "bg-emerald-100"
              : hasPartial
                ? "bg-amber-100"
                : hasPending
                  ? "bg-amber-50"
                  : allCancelled
                    ? "bg-rose-50"
                    : "bg-slate-100",
            stateIconColor,
          )}
        >
          <BadgeDollarSign className="size-4" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-[#312e8e]">
            Resumen comercial
          </h3>
          <p className={cn("truncate text-sm font-bold", stateLabelColor)}>
            {estado_mensaje}
          </p>
        </div>
      </div>

      {/* ── Activation pending (payment recorded, rights not yet allocated) ── */}
      {activacionPendiente && (
        <output className="flex items-start gap-3 border-b border-black/5 bg-amber-50/70 px-4 py-3">
          <Clock className="mt-0.5 size-4 shrink-0 text-amber-600" />
          <div className="min-w-0">
            <p className="text-[10px] font-black uppercase tracking-widest text-amber-700">
              Activación comercial pendiente
            </p>
            <p className="mt-0.5 text-xs leading-snug text-amber-900/80">
              Tu pago está registrado, pero los cupos se activan cuando el
              Organizador complete la confirmación. No realices otro pago.
            </p>
          </div>
        </output>
      )}

      {/* ── Aggregate amounts (only when there are purchases) ── */}
      {!hasNoCompras && (
        <div
          className={cn(
            "grid grid-cols-2 gap-px bg-black/5",
            !compact && "sm:grid-cols-4",
          )}
        >
          <AmountCell
            label="Contratado"
            value={total_contratado}
            unit="lugares"
            className="bg-white"
          />
          <AmountCell
            label="Pagados"
            value={total_pagado_cantidad}
            unit="lugares"
            className="bg-white"
            highlight={allPaid}
          />
          <AmountCell
            label="Monto abonado"
            value={total_pagado}
            unit="PEN"
            isCurrency
            className="bg-white"
          />
          <AmountCell
            label="Disponible"
            value={disponible_pagado}
            unit="lugares"
            className={cn(
              "bg-white",
              disponible_pagado > 0 && "font-bold text-emerald-700",
            )}
            subtitle={
              disponible_pagado > 0
                ? "lugares pagados sin registrar"
                : undefined
            }
          />
        </div>
      )}

      {/* ── Status pills ── */}
      {!hasNoCompras && (
        <div className="flex flex-wrap items-center gap-2 px-4 py-2.5 border-t border-black/5">
          <StatusPill
            count={compras_pagadas}
            label="pagadas"
            icon={<CheckCircle2 className="size-3" />}
            className="bg-emerald-50 text-emerald-700 border-emerald-200"
          />
          <StatusPill
            count={compras_pendientes}
            label="pendientes"
            icon={<Clock className="size-3" />}
            className="bg-amber-50 text-amber-700 border-amber-200"
          />
          <StatusPill
            count={compras_canceladas}
            label="canceladas"
            icon={<Ban className="size-3" />}
            className="bg-rose-50 text-rose-700 border-rose-200"
          />
        </div>
      )}

      {/* ── Purchase list ── */}
      {compras.length > 0 && (
        <ul className="divide-y divide-black/5">
          {compras.map((compra) => (
            <CompraRow key={compra.id} compra={compra} compact={compact} />
          ))}
        </ul>
      )}

      {/* ── Empty state ── */}
      {hasNoCompras && (
        <div className="px-4 py-6 text-center">
          <p className="text-sm text-slate-500 italic">
            Sin actividades de pago registradas.
          </p>
        </div>
      )}
    </section>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

interface AmountCellProps {
  label: string;
  value: number;
  unit: string;
  isCurrency?: boolean;
  highlight?: boolean;
  subtitle?: string;
  className?: string;
}

function AmountCell({
  label,
  value,
  unit,
  isCurrency,
  highlight,
  subtitle,
  className,
}: AmountCellProps) {
  return (
    <div className={cn("px-4 py-3", className)}>
      <p className="text-[10px] font-black uppercase tracking-wider text-slate-500 leading-none mb-1.5">
        {label}
      </p>
      <p
        className={cn(
          "text-lg font-black tabular-nums text-slate-800 leading-none",
          highlight && "text-emerald-700",
        )}
      >
        {isCurrency
          ? value.toLocaleString("es-PE", {
              style: "currency",
              currency: "PEN",
              minimumFractionDigits: 2,
            })
          : value.toLocaleString("es-PE")}
        {!isCurrency && (
          <span className="ml-1 text-xs font-medium text-slate-500">
            {unit}
          </span>
        )}
      </p>
      {subtitle && (
        <p className="mt-0.5 text-[10px] text-slate-500">{subtitle}</p>
      )}
    </div>
  );
}

interface StatusPillProps {
  count: number;
  label: string;
  icon: React.ReactNode;
  className?: string;
}

function StatusPill({ count, label, icon, className }: StatusPillProps) {
  if (count === 0) return null;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold",
        className,
      )}
    >
      {icon}
      {count} {label}
    </span>
  );
}

interface CompraRowProps {
  compra: ResumenPagoOut["compras"][number];
  compact?: boolean;
}

function CompraRow({ compra, compact = false }: CompraRowProps) {
  const { tipo, cantidad, precio_unitario, total, estado, orden_pago } = compra;

  const estadoConfig: Record<
    string,
    { label: string; icon: React.ReactNode; className: string }
  > = {
    PAGADA: {
      label: "Pagada",
      icon: <CheckCircle2 className="size-3.5 text-emerald-600" />,
      className: "bg-emerald-50 text-emerald-700",
    },
    PENDIENTE: {
      label: "Pendiente",
      icon: <Clock className="size-3.5 text-amber-600" />,
      className: "bg-amber-50 text-amber-700",
    },
    CANCELADA: {
      label: "Cancelada",
      icon: <XCircle className="size-3.5 text-rose-600" />,
      className: "bg-rose-50 text-rose-700",
    },
  };

  const cfg = estadoConfig[estado] ?? {
    label: estado,
    icon: null,
    className: "bg-slate-50 text-slate-600",
  };

  const tipoLabel = tipo === "INICIAL" ? "Inscripción inicial" : "Ampliación";

  return (
    <li
      className={cn(
        "px-4 py-3",
        compact ? "flex flex-col gap-2" : "flex items-center gap-3",
      )}
    >
      <div className="flex min-w-0 items-center gap-3">
        {/* Icon */}
        <div
          className={cn(
            "flex size-9 shrink-0 items-center justify-center rounded-lg",
            cfg.className,
          )}
          aria-hidden="true"
        >
          <CreditCard className="size-4" />
        </div>

        {/* Details */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-800">
              {tipoLabel}
            </span>
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold",
                cfg.className,
              )}
            >
              {cfg.icon}
              <span className="sr-only">Estado: </span>
              {cfg.label}
            </span>
          </div>
          <p className="mt-0.5 text-xs text-slate-500">
            {cantidad} lugar{cantidad !== 1 ? "es" : ""} &times;{" "}
            {precio_unitario.toLocaleString("es-PE", {
              style: "currency",
              currency: "PEN",
            })}{" "}
            ={" "}
            <span className="font-medium text-slate-700">
              {total.toLocaleString("es-PE", {
                style: "currency",
                currency: "PEN",
              })}
            </span>
          </p>
          {orden_pago && (
            <p className="mt-0.5 text-xs text-slate-500">
              Orden #{orden_pago.numero}
              {orden_pago.pagada_en && (
                <span className="ml-1 text-emerald-600">
                  — pagada el{" "}
                  {new Date(orden_pago.pagada_en).toLocaleDateString("es-PE")}
                </span>
              )}
            </p>
          )}
        </div>
      </div>

      {/* Total */}
      <div
        className={cn(
          "shrink-0",
          compact ? "flex items-baseline justify-between gap-2" : "text-right",
        )}
      >
        <p className="text-sm font-black text-slate-800">
          {total.toLocaleString("es-PE", {
            style: "currency",
            currency: "PEN",
          })}
        </p>
        <p className="text-xs text-slate-400">
          {cantidad} lugar{cantidad !== 1 ? "es" : ""}
        </p>
      </div>
    </li>
  );
}
