"use client";

import { ArrowUpRight, CalendarPlus, Play } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { ENLACES, FESTIVAL } from "@/features/portada/fixtures/festival";
import { COPY } from "@/features/portada/fixtures/copy";

/**
 * Sección "06 / TRANSMISIÓN EN VIVO".
 *
 * El enlace oficial todavía no existe: la sección anuncia el canal y ofrece
 * guardar la fecha mientras tanto.
 */
export function LiveSection() {
  const [abierto, setAbierto] = useState(false);

  return (
    <PortadaSection
      id="en-vivo"
      eyebrow={COPY.enVivo.eyebrow}
      titulo={[...COPY.enVivo.titulo]}
      destacado={COPY.enVivo.destacado}
      copy={COPY.enVivo.copy}
    >
      <div className="mt-12 grid gap-10 lg:grid-cols-2 lg:items-center lg:gap-14">
        <div className="relative overflow-hidden rounded-2xl border border-primary/10 shadow-xl shadow-primary/10">
          <div className="relative aspect-[16/10] w-full">
            <Image
              src="/images/portada/futbol.png"
              alt="Imagen deportiva del programa del festival"
              fill
              loading="lazy"
              sizes="(max-width: 1024px) 100vw, 50vw"
              className="object-cover"
            />
          </div>
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-gradient-to-t from-brand-deep-navy/85 via-brand-deep-navy/25 to-transparent"
          />
          <span className="absolute top-4 left-4 inline-flex items-center gap-2 rounded-full bg-brand-deep-night/45 px-3 py-1.5 text-[10px] font-black uppercase tracking-[0.2em] text-surface-inverse-foreground backdrop-blur-sm">
            <span
              className="size-1.5 rounded-full bg-accent"
              aria-hidden="true"
            />
            {COPY.enVivo.estado}
          </span>
          <button
            type="button"
            onClick={() => setAbierto(true)}
            aria-label="Ver información de la transmisión"
            className="absolute inset-0 m-auto grid size-16 place-items-center rounded-full bg-surface-raised/90 text-primary shadow-xl transition-transform hover:scale-105"
          >
            <Play className="size-7 fill-current" aria-hidden="true" />
          </button>
          <div className="absolute inset-x-0 bottom-0 p-5">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-cyan">
              {FESTIVAL.nombre}
            </p>
            <p className="mt-1 text-sm font-bold uppercase tracking-wide text-surface-inverse-foreground">
              EL FESTIVAL TAMBIÉN SE VIVE A DISTANCIA.
            </p>
          </div>
        </div>

        <div>
          <p className="text-sm leading-relaxed text-muted-foreground sm:text-base">
            {COPY.enVivo.nota}
          </p>
          <button
            type="button"
            onClick={() => setAbierto(true)}
            className="mt-8 inline-flex h-12 items-center justify-center gap-2 rounded-full border border-primary/25 px-5 text-xs font-black uppercase tracking-wider text-primary transition-colors hover:bg-primary/5"
          >
            {COPY.enVivo.cta}
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </button>
        </div>
      </div>

      <Dialog open={abierto} onOpenChange={setAbierto}>
        <DialogContent className="max-w-md text-center">
          <DialogTitle className="text-2xl font-black uppercase leading-tight tracking-tight text-foreground">
            LA FAMILIA,
            <br />
            <span className="text-info">SIEMPRE CERCA.</span>
          </DialogTitle>
          <p className="mt-2 text-[10px] font-black uppercase tracking-[0.25em] text-info">
            {COPY.enVivo.estado}
          </p>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            21 DE NOVIEMBRE DE 2026 · LIMA, PERÚ. La transmisión en vivo aún no
            está disponible: publicaremos el enlace oficial y los horarios para
            seguir el campeonato, las entrevistas y los momentos del festival.
          </p>
          <div className="mt-6 flex flex-col gap-3">
            <a
              href={ENLACES.calendario}
              download
              className="btn-brand-gradient btn-shine inline-flex h-12 w-full items-center justify-center gap-2 rounded-full px-6 text-xs font-black uppercase tracking-wider"
            >
              <CalendarPlus className="size-4" aria-hidden="true" />
              GUARDAR LA FECHA
            </a>
            <a
              href={ENLACES.facebook}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-full border border-primary/25 px-5 text-xs font-black uppercase tracking-wider text-primary transition-colors hover:bg-primary/5"
            >
              VER NOVEDADES
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </a>
          </div>
        </DialogContent>
      </Dialog>
    </PortadaSection>
  );
}
