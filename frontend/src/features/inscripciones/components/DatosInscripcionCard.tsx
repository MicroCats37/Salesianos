"use client";

import { UserRound } from "lucide-react";
import { cn } from "@/lib/utils";
import type { InscripcionDetalleOut } from "../services/inscripcion.service";

interface DatosInscripcionCardProps {
  inscripcion: InscripcionDetalleOut;
  className?: string;
}

/**
 * People responsible for the inscription.
 *
 * It only lists the delegated person and the responsable: the package, the
 * promotion and the creation date already live in `InscripcionHero`, so
 * repeating them here would be noise.
 */
export function DatosInscripcionCard({
  inscripcion,
  className,
}: DatosInscripcionCardProps) {
  const datos = [
    {
      icon: UserRound,
      label: "Delegado",
      value: inscripcion.delegado_nombre ?? "Sin asignar",
    },
    {
      icon: UserRound,
      label: "Responsable",
      value: inscripcion.responsable_nombre || "—",
    },
  ];

  return (
    <section
      aria-labelledby="datos-inscripcion-titulo"
      className={cn(
        "rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200/70",
        className,
      )}
    >
      <h3
        id="datos-inscripcion-titulo"
        className="text-[10px] font-black uppercase tracking-[0.3em] text-[#312e8e]"
      >
        Responsables
      </h3>

      <dl className="mt-3 space-y-3">
        {datos.map((dato) => {
          const Icon = dato.icon;
          return (
            <div key={dato.label} className="flex items-start gap-2.5">
              <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-[#312e8e]/10 text-[#312e8e]">
                <Icon className="size-3.5" />
              </span>
              <div className="min-w-0 flex-1">
                <dt className="text-[10px] font-black uppercase tracking-[0.15em] text-slate-500">
                  {dato.label}
                </dt>
                <dd className="truncate text-xs font-bold text-slate-800">
                  {dato.value}
                </dd>
              </div>
            </div>
          );
        })}
      </dl>
    </section>
  );
}
