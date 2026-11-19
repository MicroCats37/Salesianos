"use client";

import { ArrowUpRight, CalendarPlus, MapPin } from "lucide-react";
import Image from "next/image";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { ENLACES, SEDE } from "@/features/portada/fixtures/festival";
import { COPY } from "@/features/portada/fixtures/copy";

/**
 * Sección "07 / NUESTRO PUNTO DE ENCUENTRO".
 *
 * En escritorio se muestra el mapa incrustado; en móvil se sustituye por
 * una imagen estática (el iframe de Google pesa alrededor de un megabyte) y
 * un botón que abre la ubicación.
 */
export function VenueSection() {
  return (
    <PortadaSection
      id="lugar"
      eyebrow={COPY.lugar.eyebrow}
      titulo={[...COPY.lugar.titulo]}
      destacado={COPY.lugar.destacado}
    >
      <div className="mt-12 grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:gap-12">
        <div className="relative overflow-hidden rounded-2xl border border-primary/10 shadow-xl shadow-primary/10">
          <div className="hidden aspect-[16/10] w-full lg:block">
            <iframe
              title="Ubicación de la Asociación Okinawense del Perú"
              src={SEDE.mapaEmbedUrl}
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              className="size-full border-0"
            />
          </div>
          <div className="relative aspect-[4/3] w-full lg:hidden">
            <Image
              src="/images/portada/campestre.png"
              alt="Zona campestre de la Asociación Okinawense del Perú"
              fill
              loading="lazy"
              sizes="100vw"
              className="object-cover"
            />
            <div
              aria-hidden="true"
              className="absolute inset-0 bg-gradient-to-t from-brand-deep-navy/85 via-brand-deep-navy/25 to-transparent"
            />
            <div className="absolute inset-x-0 bottom-0 p-5">
              <p className="text-sm font-black uppercase tracking-tight text-surface-inverse-foreground">
                {SEDE.nombre}
              </p>
              <p className="mt-1 text-xs text-surface-inverse-foreground/75">
                {SEDE.direccion}
              </p>
            </div>
          </div>
        </div>

        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-surface-raised/70 px-4 py-2 text-[10px] font-black uppercase tracking-[0.2em] text-primary">
            <MapPin className="size-3.5" aria-hidden="true" />
            {SEDE.direccion}
          </span>

          <h3 className="mt-6 text-2xl font-black uppercase leading-[1.08] tracking-tight text-foreground sm:text-3xl">
            {SEDE.nombre}
          </h3>

          <div className="mt-6 grid grid-cols-3 gap-3">
            {COPY.lugar.horarios.map((horario) => (
              <div
                key={horario.etiqueta}
                className="card-elevated rounded-2xl p-4 text-center"
              >
                <p className="text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                  {horario.etiqueta}
                </p>
                <p className="mt-2 text-sm font-black text-foreground sm:text-base">
                  {horario.valor}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <a
              href={SEDE.mapaUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-brand-gradient btn-shine inline-flex h-12 items-center justify-center gap-2 rounded-full px-6 text-xs font-black uppercase tracking-wider"
            >
              {COPY.lugar.cta}
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </a>
            <a
              href={ENLACES.calendario}
              download
              className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-primary/25 px-5 text-xs font-black uppercase tracking-wider text-primary transition-colors hover:bg-primary/5"
            >
              <CalendarPlus className="size-4" aria-hidden="true" />
              {COPY.lugar.accionCalendario}
            </a>
          </div>
        </div>
      </div>

      <div className="mt-10 grid gap-4 sm:grid-cols-3">
        {COPY.lugar.comodidades.map((comodidad) => (
          <div key={comodidad.numero} className="card-elevated rounded-2xl p-5">
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-info">
              {comodidad.numero}
            </span>
            <h3 className="mt-2 text-base font-black uppercase tracking-tight text-foreground">
              {comodidad.titulo}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {comodidad.descripcion}
            </p>
          </div>
        ))}
      </div>
    </PortadaSection>
  );
}
