"use client";

import { ArrowLeft, PackageOpen } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EquiposEmptyStateProps {
  onVolver: () => void;
}

/**
 * Empty state of the teams section.
 *
 * Teams are created together with the inscription (wizard), so an inscription
 * without teams needs a decision, not a form: either go back to the panel or
 * contact the organizing committee.
 */
export function EquiposEmptyState({ onVolver }: EquiposEmptyStateProps) {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-dashed border-amber-300 bg-gradient-to-br from-amber-50 via-white to-rose-50 p-8 text-center shadow-sm sm:p-10">
      <div className="pointer-events-none absolute -right-12 -top-12 size-40 rounded-full bg-amber-200/40 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-16 -left-16 size-40 rounded-full bg-rose-200/40 blur-3xl" />

      <div className="relative mx-auto max-w-md space-y-4">
        <span className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-amber-600 text-white shadow-lg">
          <PackageOpen className="size-6" />
        </span>
        <div className="space-y-1.5">
          <h3 className="text-xl font-black tracking-tight text-slate-900">
            Esta inscripcion aun no tiene equipos
          </h3>
          <p className="text-sm leading-relaxed text-slate-600">
            Los equipos se registran al crear la inscripcion. Si tu delegacion
            debia tener equipos, contacta al Comite Organizador para
            regularizarlos.
          </p>
        </div>
        <Button
          type="button"
          onClick={onVolver}
          className="btn-brand-gradient btn-shine h-12 w-full rounded-full px-6 text-sm font-black uppercase tracking-widest shadow-lg sm:w-auto"
        >
          <ArrowLeft className="size-4" />
          Volver al panel
        </Button>
      </div>
    </div>
  );
}
