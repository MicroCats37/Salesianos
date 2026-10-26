"use client";

import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import type { AdminKpi } from "../utils/admin.resumen.utils";
import { toneClasses } from "../utils/admin.tone";

export interface AdminKpiCardProps {
  kpi: AdminKpi;
  icon: LucideIcon;
  href?: string;
  className?: string;
}

export function AdminKpiCard({
  kpi,
  icon: Icon,
  href,
  className,
}: AdminKpiCardProps) {
  const destino = href ?? kpi.ruta;
  const tones = toneClasses(kpi.tone);

  const contenido = (
    <>
      <div
        aria-hidden="true"
        className={cn(
          "pointer-events-none absolute -right-12 -top-12 size-40 rounded-full bg-gradient-to-br to-transparent opacity-80",
          tones.soft,
        )}
      />

      <div className="relative flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
            {kpi.label}
          </p>
          <p
            className={cn(
              "mt-2 break-words text-2xl font-black tracking-tight sm:text-3xl",
              tones.value,
            )}
          >
            {kpi.value}
          </p>
        </div>

        <span
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl",
            tones.icon,
          )}
        >
          <Icon className="size-5" />
        </span>
      </div>

      <p className="relative mt-3 text-xs font-medium leading-relaxed text-slate-500">
        {kpi.hint}
      </p>
    </>
  );

  const clases = cn(
    "card-elevated relative block w-full overflow-hidden p-5 sm:p-6",
    destino &&
      "card-elevated-hover focus-visible:ring-2 focus-visible:ring-[#312e8e]/40 focus-visible:ring-offset-2 focus-visible:outline-none",
    className,
  );

  if (destino) {
    return (
      <Link href={destino} className={clases}>
        {contenido}
      </Link>
    );
  }

  return <article className={clases}>{contenido}</article>;
}
