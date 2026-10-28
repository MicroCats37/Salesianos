"use client";

import { CalendarDays, GraduationCap, Package } from "lucide-react";
import { FestBrandHeader } from "@/components/branding/FestBrandHeader";
import type { InscripcionDetalleOut } from "../services/inscripcion.service";

interface InscripcionHeroProps {
  inscripcion: InscripcionDetalleOut;
}

/**
 * Identity header of the inscription detail.
 *
 * It answers "where am I" at a glance: which event, which package, which
 * inscription id, when it was created and which promotion it uses.
 *
 * It deliberately shows NO counters and NO state: the administrative state and
 * the progress live in `EstadoProgresoCard`, the money in `ResumenPagoCard`.
 * Every fact has exactly one owner on this page.
 */
export function InscripcionHero({ inscripcion }: InscripcionHeroProps) {
  return (
    <section className="relative overflow-hidden border-b border-slate-200/60 bg-gradient-to-br from-[#f6f4ee] via-white to-[#eef1f8]">
      <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-amber-300/40 blur-3xl" />
      <div className="pointer-events-none absolute -left-24 bottom-0 h-72 w-72 rounded-full bg-cyan-300/40 blur-3xl" />

      <div className="relative mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-10 lg:py-10">
        <div className="flex flex-col gap-5">
          <FestBrandHeader
            variant="onLight"
            size="sm"
            className="flex-row items-center gap-3"
          />

          <div className="space-y-2">
            <p className="text-[10px] font-black uppercase tracking-[0.35em] text-[#312e8e]">
              Inscripcion #{inscripcion.id.slice(0, 8)}
            </p>
            <h1 className="text-2xl font-black tracking-tight text-[#17214b] sm:text-3xl lg:text-4xl">
              {inscripcion.evento_nombre}
            </h1>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-[#17214b]/80">
              <span className="inline-flex items-center gap-1.5">
                <CalendarDays className="size-4" />
                Creada el{" "}
                {new Date(inscripcion.created_at).toLocaleDateString("es-PE", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
              {inscripcion.promocion_nombre && (
                <span className="inline-flex items-center gap-1.5">
                  <GraduationCap className="size-4" />
                  {inscripcion.promocion_nombre}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Package block — the contracted commercial detail of the inscription */}
        <div className="rounded-3xl border border-slate-200/70 bg-white/85 p-5 shadow-sm backdrop-blur">
          <div className="flex items-start gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#312e8e] to-[#25236f] text-white shadow-md">
              <Package className="size-5" />
            </span>
            <div className="min-w-0">
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#312e8e]">
                Paquete contratado
              </p>
              <p className="text-lg font-black tracking-tight text-[#17214b] sm:text-xl">
                {inscripcion.paquete_nombre}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
