"use client";

import { cn } from "@/lib/utils";
import type { InscripcionDetalleOut } from "../services/inscripcion.service";
import {
  estadoInscripcionMeta,
  InscripcionEstadoBadge,
} from "./InscripcionEstadoBadge";

interface EstadoInscripcionCardProps {
  inscripcion: InscripcionDetalleOut;
  className?: string;
}

/**
 * Administrative state of the inscription with its plain-language meaning.
 *
 * It never talks about the payment: the commercial state belongs to
 * `resumen_pago` and is rendered by `ResumenPagoCard`.
 */
export function EstadoInscripcionCard({
  inscripcion,
  className,
}: EstadoInscripcionCardProps) {
  const meta = estadoInscripcionMeta(inscripcion.estado);

  return (
    <section
      className={cn(
        "rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200/70",
        className,
      )}
    >
      <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-[#312e8e]">
        Estado de la inscripcion
      </h3>

      <div className="mt-3">
        <InscripcionEstadoBadge estado={inscripcion.estado} size="lg" />
      </div>

      <p className="mt-3 text-xs leading-relaxed text-slate-600">
        {meta.description}
      </p>

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
    </section>
  );
}
