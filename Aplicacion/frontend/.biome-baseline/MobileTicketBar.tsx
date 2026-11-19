"use client";

import { ArrowUpRight } from "lucide-react";
import { useEffect, useState } from "react";
import { COPY } from "@/features/portada/copy";

/**
 * Barra fija de paquetes (solo móvil).
 *
 * Aparece al bajar por la portada y desaparece al volver arriba, para no
 * tapar el contenido. Con movimiento reducido queda siempre visible.
 */
export function MobileTicketBar() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduced) {
      setVisible(true);
      return;
    }

    const alDesplazar = () => setVisible(window.scrollY > 400);
    alDesplazar();
    window.addEventListener("scroll", alDesplazar, { passive: true });
    return () => window.removeEventListener("scroll", alDesplazar);
  }, []);

  return (
    <div
      className={`fixed inset-x-0 bottom-0 z-40 border-t border-slate-200 bg-white/95 px-4 pt-3 backdrop-blur transition-transform duration-300 lg:hidden ${
        visible ? "translate-y-0" : "translate-y-full"
      }`}
      style={{ paddingBottom: "calc(0.75rem + env(safe-area-inset-bottom))" }}
    >
      <div className="flex items-center justify-between gap-3">
        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-[#17214b]">
          {COPY.barraMovil.texto}
        </span>
        <a
          href="#paquetes"
          className="inline-flex h-10 items-center gap-1.5 rounded-full bg-[#312e8e] px-4 text-[10px] font-black uppercase tracking-widest text-white"
        >
          {COPY.barraMovil.cta}
          <ArrowUpRight className="size-3.5" aria-hidden="true" />
        </a>
      </div>
    </div>
  );
}
