"use client";

import { ArrowUpRight, Share2 } from "lucide-react";
import { toast } from "sonner";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { ENLACES, FESTIVAL } from "@/features/portada/fixtures/festival";
import { COPY } from "@/features/portada/fixtures/copy";

/**
 * Cierre de la portada: la llamada final a la acción.
 */
export function ClosingSection() {
  async function compartir() {
    const url = typeof window === "undefined" ? "" : window.location.href;
    const datos = {
      title: FESTIVAL.nombre,
      text: `${FESTIVAL.frase} — ${FESTIVAL.fechaEvento} en ${"Ate, Lima"}.`,
      url,
    };

    if (
      typeof navigator !== "undefined" &&
      typeof navigator.share === "function"
    ) {
      try {
        await navigator.share(datos);
        return;
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") return;
      }
    }

    try {
      await navigator.clipboard.writeText(url);
      toast.success("Enlace del festival copiado.");
    } catch {
      toast.error("No se pudo copiar el enlace.");
    }
  }

  return (
    <PortadaSection fondo="marca">
      <div className="flex flex-col items-center text-center">
        <p className="text-[10px] font-black uppercase tracking-[0.35em] text-brand-cyan">
          {COPY.cierre.fecha}
        </p>
        <h2 className="mt-4 max-w-4xl text-3xl font-black uppercase leading-[1.05] tracking-tight text-primary-foreground sm:text-5xl lg:text-6xl">
          {COPY.cierre.titulo.map((linea, index) => (
            <span key={linea}>
              {index > 0 && <br />}
              {index === COPY.cierre.titulo.length - 1 ? (
                <em className="not-italic text-accent">{linea}</em>
              ) : (
                linea
              )}
            </span>
          ))}
        </h2>

        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
          <a
            href={ENLACES.registro}
            className="inline-flex h-12 items-center justify-center gap-2 rounded-full bg-gradient-to-r from-info via-primary to-brand-deep-navy px-8 text-xs font-black uppercase tracking-widest text-primary-foreground shadow-2xl shadow-brand-deep-night/30 transition-transform hover:scale-105"
          >
            {COPY.cierre.cta}
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
          <button
            type="button"
            onClick={compartir}
            className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-primary-foreground/30 px-6 text-xs font-black uppercase tracking-widest text-primary-foreground transition-colors hover:bg-primary-foreground/10"
          >
            <Share2 className="size-4" aria-hidden="true" />
            {COPY.cierre.compartir}
          </button>
        </div>
      </div>
    </PortadaSection>
  );
}
