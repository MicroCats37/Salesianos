"use client";

import { CheckCircle2, Package, TriangleAlert, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ResumenEquiposOut } from "../services/inscripcion.service";

interface ResumenEquiposBadgeProps {
  resumen: ResumenEquiposOut;
  className?: string;
}

/**
 * Aggregate badge showing total / complete / incomplete equipo counts.
 * Rendered from presenter-derived data — no business logic here.
 */
export function ResumenEquiposBadge({
  resumen,
  className,
}: ResumenEquiposBadgeProps) {
  const { total, completos, incompletos } = resumen;
  const allComplete = incompletos === 0 && total > 0;
  const progreso = total > 0 ? Math.round((completos / total) * 100) : 0;

  return (
    <section
      className={cn(
        "rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200/70",
        className,
      )}
    >
      <div className="flex items-center gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-[#312e8e]/10 text-[#312e8e]">
          <Package className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-[#312e8e]">
            Equipos inscritos
          </h3>
          <p className="text-sm font-bold leading-snug text-slate-900">
            {completos} de {total} con roster completo
          </p>
        </div>
        {allComplete ? (
          <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-bold text-emerald-700">
            <CheckCircle2 className="size-3.5" />
            Listos
          </span>
        ) : (
          <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[11px] font-bold text-amber-700">
            <TriangleAlert className="size-3.5" />
            {incompletos} pendientes
          </span>
        )}
      </div>

      <div
        className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-200/80"
        role="progressbar"
        aria-valuenow={completos}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label="Equipos con roster completo"
      >
        <div
          className={cn(
            "h-full rounded-full transition-all duration-500",
            allComplete
              ? "bg-gradient-to-r from-emerald-400 to-emerald-600"
              : "bg-gradient-to-r from-[#312e8e] to-[#6976ff]",
          )}
          style={{ width: `${progreso}%` }}
        />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
          <Users className="size-3 text-slate-500" />
          {total} equipos
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
          <CheckCircle2 className="size-3" />
          {completos} completos
        </span>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
            incompletos > 0
              ? "bg-amber-100 text-amber-700"
              : "bg-slate-50 text-slate-500",
          )}
        >
          <TriangleAlert className="size-3" />
          {incompletos} incompletos
        </span>
      </div>
    </section>
  );
}
