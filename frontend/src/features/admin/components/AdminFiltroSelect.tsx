"use client";

import { Filter } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface AdminFiltroOpcion {
  valor: string;
  etiqueta: string;
}

export interface AdminFiltroSelectProps {
  /** Label of the filter — it names the resource field it narrows. */
  etiqueta: string;
  /** Current value of the filter (empty string means "all"). */
  valor: string;
  /** Options of the filter; the "all" option is added by the component. */
  opciones: AdminFiltroOpcion[];
  onChange: (valor: string) => void;
  /** Placeholder of the "all" option. */
  todos?: string;
  className?: string;
}

/**
 * AdminFiltroSelect — one resource filter of the toolbar.
 *
 * The component is a THIN wrapper: it owns no state. The value comes from the
 * URL and every change is written back to the URL, so a filtered list can be
 * shared and reloaded without losing its context.
 */
export function AdminFiltroSelect({
  etiqueta,
  valor,
  opciones,
  onChange,
  todos = "Todos",
  className,
}: AdminFiltroSelectProps) {
  return (
    <div className={className}>
      <span className="mb-1.5 flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
        <Filter className="size-3" />
        {etiqueta}
      </span>
      <Select
        value={valor || "__todos__"}
        onValueChange={(next) => onChange(next === "__todos__" ? "" : next)}
      >
        <SelectTrigger
          className="h-9 w-full min-w-[10rem] rounded-xl bg-white text-xs font-bold"
          aria-label={etiqueta}
        >
          <SelectValue placeholder={todos} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__todos__">{todos}</SelectItem>
          {opciones.map((opcion) => (
            <SelectItem key={opcion.valor} value={opcion.valor}>
              {opcion.etiqueta}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
