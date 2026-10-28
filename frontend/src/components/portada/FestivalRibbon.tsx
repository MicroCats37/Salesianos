"use client";

import { useEffect, useState } from "react";
import { COPY } from "@/features/portada/copy";
import { cn } from "@/lib/utils";

/**
 * Cinta institucional en marquee.
 *
 * El movimiento es CSS puro (más barato que GSAP) y con movimiento reducido
 * la cinta queda estática: nunca desaparece, porque es información.
 */
export function FestivalRibbon({ className }: { className?: string }) {
  const [estatico, setEstatico] = useState(false);

  useEffect(() => {
    const consulta = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sincronizar = () => setEstatico(consulta.matches);
    sincronizar();
    consulta.addEventListener("change", sincronizar);
    return () => consulta.removeEventListener("change", sincronizar);
  }, []);

  return (
    <div
      className={cn(
        "relative snap-none overflow-hidden border-y border-white/10 bg-[#312e8e] py-3",
        className,
      )}
    >
      <div
        className={cn(
          "flex w-max items-center gap-6 whitespace-nowrap",
          !estatico && "animate-[marquee_22s_linear_infinite]",
        )}
        style={
          estatico
            ? undefined
            : { animationName: "portada-marquee", animationDuration: "22s" }
        }
      >
        {[0, 1].map((copia) => (
          <div
            key={copia}
            aria-hidden={copia === 1 ? "true" : undefined}
            className="flex items-center gap-6"
          >
            {COPY.ribbon.map((palabra) => (
              <span key={palabra} className="flex items-center gap-6">
                <span className="text-xs font-black uppercase tracking-[0.25em] text-white/90 sm:text-sm">
                  {palabra}
                </span>
                <span className="text-[#f4c64e]" aria-hidden="true">
                  ✦
                </span>
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
