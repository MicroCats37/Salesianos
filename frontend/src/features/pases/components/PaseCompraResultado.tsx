"use client";

import { CheckCircle2, Clock, TriangleAlert, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PaseOrigenPago } from "../schemas";
import {
  type PaseEstadoLike,
  paseActivacionPendiente,
  paseEstadoTone,
  paseOrigenPagoLabel,
  paseSiguientePaso,
} from "../utils/pase.estado";
import {
  formatearMontoPase,
  PASE_MONEDA_POR_DEFECTO,
} from "../utils/pase.precio";

/**
 * PaseCompraResultado — what happened to the purchase, in the words of the
 * buyer.
 *
 * The panel NEVER claims an activation the backend did not confirm: a paid
 * order of a pending purchase is presented as an ACTIVATION PENDING, not as a
 * completed payment.
 */

export interface PaseCompraResultadoProps {
  /** Number of the payment order. */
  numeroOrden: string;
  /** Commercial name of the purchased pass. */
  paseNombre: string;
  /** Number of passes of the batch. */
  cantidad: number;
  /** Unit price frozen at purchase time. */
  precioUnitario: number;
  /** Total frozen at purchase time. */
  total: number;
  /** Currency of the amounts. */
  moneda?: string | null;
  /** The commercial state of the purchase. */
  estado: PaseEstadoLike;
  /** Origin of the payment evidence — `null` before the payment. */
  origenPago?: PaseOrigenPago | null;
  /** Active rights already assigned. */
  beneficiariosAsignados?: number | null;
  /** Free slots of the batch. */
  beneficiariosPendientes?: number | null;
  /** Called when the buyer asks to pay a purchase that is still pending. */
  onPagar?: () => void;
  /** Whether the payment action is available. */
  pagable?: boolean;
}

/** The badge of the commercial state. */
function badgeEstado(estado: PaseEstadoLike): {
  texto: string;
  clases: string;
  icono: typeof CheckCircle2;
} {
  if (paseActivacionPendiente(estado)) {
    return {
      texto: "Pago registrado · activación pendiente",
      clases: "border-amber-300 bg-amber-50 text-amber-800",
      icono: Clock,
    };
  }

  switch (paseEstadoTone(estado)) {
    case "pagada":
      return {
        texto: "Pago verificado",
        clases: "border-emerald-300 bg-emerald-50 text-emerald-800",
        icono: CheckCircle2,
      };
    case "vencida":
      return {
        texto: "Orden de pago vencida",
        clases: "border-orange-300 bg-orange-50 text-orange-800",
        icono: TriangleAlert,
      };
    case "cancelada":
      return {
        texto: "Compra cancelada",
        clases: "border-red-300 bg-red-50 text-red-800",
        icono: XCircle,
      };
    default:
      return {
        texto: "Pago pendiente",
        clases: "border-slate-300 bg-slate-100 text-slate-700",
        icono: Clock,
      };
  }
}

export function PaseCompraResultado({
  numeroOrden,
  paseNombre,
  cantidad,
  precioUnitario,
  total,
  moneda,
  estado,
  origenPago,
  beneficiariosAsignados,
  beneficiariosPendientes,
  onPagar,
  pagable = false,
}: PaseCompraResultadoProps) {
  const badge = badgeEstado(estado);
  const Icono = badge.icono;

  return (
    <section
      aria-labelledby="pase-resultado-titulo"
      className="rounded-3xl border border-slate-200 bg-white p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2
          id="pase-resultado-titulo"
          className="text-lg font-black text-slate-900"
        >
          Tu compra de pases
        </h2>
        <Badge variant="outline" className={badge.clases}>
          <Icono className="mr-1 size-3.5" aria-hidden="true" />
          {badge.texto}
        </Badge>
      </div>

      <p className="mt-1 text-sm font-medium text-slate-600">
        {paseSiguientePaso(estado)}
      </p>

      {origenPago ? (
        <p className="mt-1 text-xs font-bold uppercase tracking-wider text-slate-500">
          {paseOrigenPagoLabel(origenPago)}
        </p>
      ) : null}

      <dl className="mt-4 grid gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm sm:grid-cols-2">
        <div className="flex items-baseline justify-between gap-2">
          <dt className="font-bold text-slate-600">Orden</dt>
          <dd className="font-bold text-slate-900">{numeroOrden}</dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="font-bold text-slate-600">Pase</dt>
          <dd className="font-bold text-slate-900">{paseNombre}</dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="font-bold text-slate-600">Cantidad</dt>
          <dd className="font-bold text-slate-900">{cantidad}</dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="font-bold text-slate-600">Precio por pase</dt>
          <dd className="font-bold text-slate-900">
            {formatearMontoPase(
              precioUnitario,
              moneda ?? PASE_MONEDA_POR_DEFECTO,
            )}
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-2 sm:col-span-2">
          <dt className="text-xs font-black uppercase tracking-wider text-slate-500">
            Total
          </dt>
          <dd className="text-xl font-black text-[#312e8e]">
            {formatearMontoPase(total, moneda ?? PASE_MONEDA_POR_DEFECTO)}
          </dd>
        </div>
      </dl>

      {typeof beneficiariosPendientes === "number" ? (
        <p className="mt-3 text-sm font-medium text-slate-600">
          {`Pasas por asignar: ${beneficiariosPendientes}.`}
          {typeof beneficiariosAsignados === "number"
            ? ` Ya asignados: ${beneficiariosAsignados}.`
            : ""}
        </p>
      ) : null}

      {pagable && onPagar ? (
        <Button
          type="button"
          onClick={onPagar}
          className="btn-brand-gradient mt-4 w-full rounded-full font-black text-white"
        >
          Pagar con Izipay
        </Button>
      ) : null}
    </section>
  );
}
