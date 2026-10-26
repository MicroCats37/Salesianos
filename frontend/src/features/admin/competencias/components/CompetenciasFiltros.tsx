"use client";

import { Eraser } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { AdminFiltrosSheet } from "@/features/admin/components";
import { useIsMobileState } from "@/hooks/use-mobile";

export interface CompetenciasFiltrosProps {
  /** The resource filters of the view. */
  controles: ReactNode;
  /** Whether a filter is narrowing the list. */
  hayFiltros: boolean;
  /** How many resource filters are active. */
  filtrosActivos: number;
  /** The "Limpiar filtros" action. */
  onLimpiarFiltros: () => void;
}

/**
 * CompetenciasFiltros — the resource filters of the views of the module.
 *
 * It reuses the chrome of the administration area (`AdminFiltrosSheet`, the
 * "Limpiar filtros" action) but it has NO free-text search and NO ordering:
 * the endpoints of the module declare neither `q` nor `ordering`, and the
 * client NEVER sends a parameter the backend does not accept.
 *
 * Below 768px the filters live inside a sheet, so they are not even in the
 * DOM until the administrator opens them.
 */
export function CompetenciasFiltros({
  controles,
  hayFiltros,
  filtrosActivos,
  onLimpiarFiltros,
}: CompetenciasFiltrosProps) {
  // `undefined` while the size of the viewport is unknown.
  const esMovil = useIsMobileState();

  return (
    <div className="card-elevated flex flex-col gap-4 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
          Filtros de la lista
        </p>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          {esMovil === true ? (
            <AdminFiltrosSheet
              activeCount={filtrosActivos}
              onClear={onLimpiarFiltros}
            >
              {controles}
            </AdminFiltrosSheet>
          ) : null}

          {hayFiltros ? (
            <Button
              type="button"
              variant="ghost"
              onClick={onLimpiarFiltros}
              className="btn-brand-gradient btn-shine h-9 gap-2 rounded-full px-4 text-xs font-black uppercase tracking-wider"
            >
              <Eraser className="size-3.5" />
              Limpiar filtros
            </Button>
          ) : null}
        </div>
      </div>

      {esMovil === false && controles ? (
        <div className="grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-2 lg:grid-cols-4">
          {controles}
        </div>
      ) : null}

      {/*
        The size of the viewport is unknown (server render): the space of the
        inline filters is reserved so the list does not jump when the branch
        is resolved.
      */}
      {esMovil === undefined && controles ? (
        <div
          aria-hidden="true"
          className="h-[73px] border-t border-slate-100"
        />
      ) : null}
    </div>
  );
}
