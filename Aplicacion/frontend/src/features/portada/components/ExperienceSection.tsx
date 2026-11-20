"use client";

import { ArrowUpRight, CalendarPlus } from "lucide-react";
import Image from "next/image";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { COPY } from "@/features/portada/fixtures/copy";
import { ENLACES, SECCIONES } from "@/features/portada/fixtures/festival";

/**
 * Sección "01 / LA EXPERIENCIA".
 *
 * Tres tarjetas que resumen el día (campeonato, familia y fiesta) y un pie
 * con la promesa institucional más la descarga del calendario.
 */
export function ExperienceSection() {
  return (
    <PortadaSection
      id={SECCIONES.experiencia}
      eyebrow={COPY.experiencia.eyebrow}
      titulo={[...COPY.experiencia.titulo]}
      destacado={COPY.experiencia.destacado}
      copy={[...COPY.experiencia.copy]}
    >
      <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-[1.15fr_1fr_1fr]">
        {COPY.experiencia.tarjetas.map((tarjeta) => (
          <a
            key={tarjeta.numero}
            href={tarjeta.href}
            data-portada-stagger
            className="card-elevated card-elevated-hover group flex flex-col overflow-hidden rounded-2xl"
          >
            <div className="relative aspect-[4/3] overflow-hidden sm:aspect-[16/10] lg:aspect-[4/3]">
              <Image
                src={tarjeta.imagen}
                alt={tarjeta.alt}
                fill
                loading="lazy"
                sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
                className="object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div
                aria-hidden="true"
                className="absolute inset-0 bg-gradient-to-t from-brand-deep-navy/45 via-transparent to-transparent"
              />
              <span className="absolute top-4 left-4 grid size-9 place-items-center rounded-full border border-surface-inverse-foreground/50 bg-surface-inverse/30 text-[11px] font-black text-surface-inverse-foreground backdrop-blur-sm">
                {tarjeta.numero}
              </span>
            </div>
            <div className="flex flex-1 flex-col p-5 sm:p-6">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-info">
                {tarjeta.miniLabel}
              </p>
              <h3 className="mt-3 text-xl font-black uppercase leading-[1.05] tracking-tight text-foreground sm:text-2xl">
                {tarjeta.titulo.map((linea, index) => (
                  <span key={linea}>
                    {index > 0 && <br />}
                    {linea}
                  </span>
                ))}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                {tarjeta.descripcion}
              </p>
              <span
                aria-hidden="true"
                className="mt-5 grid size-10 place-items-center rounded-full border border-primary/25 text-primary transition-transform duration-300 group-hover:rotate-45 group-hover:bg-accent group-hover:text-accent-foreground"
              >
                <ArrowUpRight className="size-5" />
              </span>
            </div>
          </a>
        ))}
      </div>

      <div
        data-portada-stagger
        className="mt-10 flex flex-col gap-4 border-t border-primary/15 pt-6 sm:flex-row sm:items-center sm:justify-between"
      >
        <p className="text-xs font-black uppercase tracking-[0.2em] text-foreground sm:text-sm">
          {COPY.experiencia.pie.frase}
        </p>
        <a
          href={ENLACES.calendario}
          download
          className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-primary/25 px-5 text-xs font-black uppercase tracking-wider text-primary transition-colors hover:bg-primary/5"
        >
          <CalendarPlus className="size-4" aria-hidden="true" />
          {COPY.experiencia.pie.accion}
        </a>
      </div>
    </PortadaSection>
  );
}
