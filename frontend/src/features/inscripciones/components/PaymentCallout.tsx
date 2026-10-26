"use client";

import { AlertCircle, CreditCard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ResumenPagoOut } from "../services/inscripcion.service";
import { puedeIniciarPago } from "../utils/pago.estado";

interface PaymentCalloutProps {
  resumenPago: ResumenPagoOut | null;
  estado: string;
  onOpenPayment: () => void;
  className?: string;
}

/**
 * Primary call to action of the inscription detail.
 *
 * The payment entry point is a COMMERCIAL decision: it exists while the
 * commercial summary reports a payable purchase. It disappears once the
 * purchase is paid, even though `Inscripcion.estado` did not change — the
 * administrative state never describes the commercial state.
 */
export function PaymentCallout({
  resumenPago,
  estado,
  onOpenPayment,
  className,
}: PaymentCalloutProps) {
  const isIzipayEnabled = process.env.NEXT_PUBLIC_IZIPAY_ENABLED === "true";
  const canContinuePayment =
    puedeIniciarPago(resumenPago, estado) && isIzipayEnabled;
  if (!canContinuePayment) return null;

  return (
    <section
      aria-labelledby="payment-callout-title"
      className={cn(
        "relative overflow-hidden rounded-3xl border border-amber-300 bg-gradient-to-br from-amber-100 via-amber-50 to-rose-100 p-5 shadow-xl shadow-amber-200/40 sm:p-6",
        className,
      )}
    >
      <div className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full bg-amber-400/40 blur-2xl" />
      <div className="pointer-events-none absolute -bottom-16 -left-12 h-32 w-32 rounded-full bg-rose-300/40 blur-2xl" />

      <div className="relative flex flex-col gap-4">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-md">
            <AlertCircle className="size-5" />
          </span>
          <div className="min-w-0 space-y-1">
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-amber-700">
              Pago pendiente
            </p>
            <h2
              id="payment-callout-title"
              className="text-lg font-black tracking-tight text-amber-900 sm:text-xl"
            >
              Completa el pago para procesar tu inscripcion
            </h2>
            <p className="text-xs leading-relaxed text-amber-900/80 sm:text-sm">
              Tu inscripcion esta guardando confirmacion de pago. Pagala con
              izipay para que el Comite Organizador la valide.
            </p>
          </div>
        </div>

        <Button
          type="button"
          onClick={onOpenPayment}
          className="btn-brand-gradient btn-shine h-12 w-full rounded-full px-6 text-sm font-black uppercase tracking-widest shadow-lg"
        >
          <CreditCard className="size-4" />
          Proceder al Pago
        </Button>
      </div>
    </section>
  );
}
