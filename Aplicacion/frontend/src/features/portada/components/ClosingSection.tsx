"use client";

import { ArrowUpRight, Share2 } from "lucide-react";
import { notify } from "@/errors";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { COPY } from "@/features/portada/fixtures/copy";
import { ENLACES, FESTIVAL } from "@/features/portada/fixtures/festival";

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
      notify.success("Enlace del festival copiado.");
    } catch {
      notify.error("No se pudo copiar el enlace.");
    }
  }

  return (
    <PortadaSection fondo="marca">
      <div className="flex flex-col items-center text-center">
        <p className="text-eyebrow-brand text-brand-cyan">
          {COPY.cierre.fecha}
        </p>
        <h2 className="mt-4 max-w-4xl text-3xl font-black uppercase leading-[1.05] tracking-tight text-brand-on-gradient sm:text-5xl lg:text-6xl">
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
            className="btn-shine inline-flex h-12 items-center justify-center gap-2 rounded-full bg-accent px-8 text-xs font-black uppercase tracking-widest text-accent-foreground shadow-glow-brand transition-colors hover:bg-accent-muted"
          >
            {COPY.cierre.cta}
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
          <button
            type="button"
            onClick={compartir}
            className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-brand-on-gradient-border px-6 text-xs font-black uppercase tracking-widest text-brand-on-gradient transition-colors hover:bg-brand-on-gradient-soft"
          >
            <Share2 className="size-4" aria-hidden="true" />
            {COPY.cierre.compartir}
          </button>
        </div>
      </div>
    </PortadaSection>
  );
}
