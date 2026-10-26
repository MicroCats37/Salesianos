"use client";

import { AlertCircle, Inbox, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/**
 * The four MANDATORY states of every administration table
 * (`sdd/administracion-operativa-fest/admin-surface` §8.3):
 * loading, error, empty and filtered-empty.
 *
 * The failure is NEVER a toast alone: the error stays visible in the page
 * with an explicit retry action.
 */

/** Stable keys of the skeleton rows. */
const CLAVES_ESQUELETON = [
  "fila-1",
  "fila-2",
  "fila-3",
  "fila-4",
  "fila-5",
  "fila-6",
  "fila-7",
  "fila-8",
];

export type AdminListaSkeletonVariant = "tabla" | "cards";

interface AdminListaSkeletonProps {
  filas?: number;
  variant?: AdminListaSkeletonVariant;
}

/** Skeleton of a table — mirrors the real number of rows. */
export function AdminListaSkeleton({
  filas = 6,
  variant = "cards",
}: AdminListaSkeletonProps) {
  const claves = CLAVES_ESQUELETON.slice(
    0,
    Math.min(Math.max(filas, 0), CLAVES_ESQUELETON.length),
  );
  const tablaDesdeXl = variant === "tabla";
  const clasesTabla = tablaDesdeXl ? "hidden xl:block" : "hidden md:block";
  const clasesCards = tablaDesdeXl ? "flex xl:hidden" : "flex md:hidden";

  return (
    <>
      <div className={cn("card-elevated overflow-hidden", clasesTabla)}>
        <div className="grid grid-cols-[minmax(0,1.5fr)_repeat(3,minmax(0,1fr))] gap-4 border-b border-slate-100 bg-slate-50/70 px-5 py-4">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-3 w-16" />
        </div>
        <div className="divide-y divide-slate-100">
          {claves.map((clave) => (
            <div
              key={clave}
              className="grid grid-cols-[minmax(0,1.5fr)_repeat(3,minmax(0,1fr))] items-center gap-4 px-5 py-4"
            >
              <Skeleton className="h-9 w-9 rounded-2xl" />
              <Skeleton className="h-3.5" />
              <Skeleton className="h-3.5" />
              <Skeleton className="h-3.5" />
            </div>
          ))}
        </div>
      </div>

      <div className={cn("flex flex-col gap-3", clasesCards)}>
        {claves.map((clave) => (
          <div key={clave} className="card-elevated p-4">
            <div className="flex items-center gap-4">
              <Skeleton className="h-9 w-9 rounded-2xl" />
              <Skeleton className="h-3.5 flex-1" />
              <Skeleton className="h-3.5 w-24" />
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

/** Inline error with a retry action. */
export function AdminListaError({
  mensaje,
  onReintentar,
}: {
  mensaje: string;
  onReintentar: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-3xl border border-rose-200 bg-rose-50/60 px-6 py-14 text-center">
      <div className="flex size-14 items-center justify-center rounded-2xl border border-rose-200 bg-white text-rose-600">
        <AlertCircle className="size-7" />
      </div>
      <div className="space-y-1">
        <h2 className="text-base font-black tracking-tight text-slate-900">
          No se pudo cargar la información
        </h2>
        <p className="text-sm leading-relaxed text-slate-600">{mensaje}</p>
      </div>
      <Button
        type="button"
        variant="ghost"
        onClick={onReintentar}
        className="btn-brand-gradient btn-shine h-10 gap-2 rounded-full px-5 text-xs font-black uppercase tracking-wider"
      >
        <RefreshCw className="size-3.5" />
        Reintentar
      </Button>
    </div>
  );
}

/** Empty state — no data at all, or no data for the current filters. */
export function AdminListaVacia({
  titulo,
  descripcion,
  accion,
  onAccion,
}: {
  titulo: string;
  descripcion: string;
  accion?: string;
  onAccion?: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-3xl border-2 border-dashed border-slate-200 bg-white/70 px-6 py-14 text-center">
      <div className="flex size-14 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-slate-400">
        <Inbox className="size-7" />
      </div>
      <div className="space-y-1">
        <h2 className="text-base font-black tracking-tight text-slate-900">
          {titulo}
        </h2>
        <p className="text-sm leading-relaxed text-slate-600">{descripcion}</p>
      </div>
      {accion && onAccion && (
        <Button
          type="button"
          variant="ghost"
          onClick={onAccion}
          className="btn-brand-gradient btn-shine h-10 gap-2 rounded-full px-5 text-xs font-black uppercase tracking-wider"
        >
          <RefreshCw className="size-3.5" />
          {accion}
        </Button>
      )}
    </div>
  );
}
