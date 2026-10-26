"use client";

import { CalendarRange } from "lucide-react";
import { Input } from "@/components/ui/input";

export interface AdminFiltroRangoFechasProps {
  /** Label of the filter. */
  etiqueta: string;
  /** Initial date (ISO `YYYY-MM-DD`). */
  desde: string;
  /** Final date (ISO `YYYY-MM-DD`). */
  hasta: string;
  onChange: (desde: string, hasta: string) => void;
}

/**
 * AdminFiltroRangoFechas — the `desde` / `hasta` filter.
 *
 * The backend expects an ISO date (`YYYY-MM-DD`) and rejects anything else
 * with 422 `INVALID_REQUEST`, so the control only emits that format.
 */
export function AdminFiltroRangoFechas({
  etiqueta,
  desde,
  hasta,
  onChange,
}: AdminFiltroRangoFechasProps) {
  return (
    <div>
      <span className="mb-1.5 flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
        <CalendarRange className="size-3" />
        {etiqueta}
      </span>
      {/*
        Below `sm` the two native date inputs are STACKED: side by side they
        do not fit in a 375px phone and the page would scroll horizontally.
      */}
      <div className="grid grid-cols-1 items-center gap-2 sm:grid-cols-[1fr_auto_1fr]">
        <Input
          type="date"
          value={desde}
          onChange={(evento) => onChange(evento.target.value, hasta)}
          aria-label={`${etiqueta} desde`}
          className="h-9 rounded-xl bg-white text-xs font-medium"
        />
        <span className="hidden text-xs text-slate-400 sm:inline">a</span>
        <Input
          type="date"
          value={hasta}
          onChange={(evento) => onChange(desde, evento.target.value)}
          aria-label={`${etiqueta} hasta`}
          className="h-9 rounded-xl bg-white text-xs font-medium"
        />
      </div>
    </div>
  );
}
