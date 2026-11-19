"use client";

import { MapPin } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { Countdown } from "@/features/portada/components/Countdown";
import { COPY } from "@/features/portada/fixtures/copy";
import { SEDE } from "@/features/portada/fixtures/festival";

/**
 * Los tres momentos destacados del festival + el pie con el lugar y la cuenta
 * regresiva.
 *
 * Va en su propia pantalla (y no dentro del hero) para que el hero mida
 * exactamente un viewport: con el scroll-snap, cada sección tiene que caber
 * en una pantalla o deja de ser una sección.
 *
 * Mide el espacio DISPONIBLE (viewport menos el navbar sticky), no el viewport
 * entero: si se mide contra el 100% de la pantalla, el navbar se encima del
 * contenido y el bloque de abajo queda bajo el pliegue.
 */
export function MomentosSection() {
  return (
    <section className="surface-page-gradient flex snap-start flex-col justify-center scroll-mt-[var(--portada-chrome-height)] py-16 sm:py-20 lg:portada-altura-disponible">
      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-4 sm:grid-cols-3">
          {COPY.hero.momentos.map((momento) => (
            <Link
              key={momento.numero}
              href={momento.href}
              className="group relative overflow-hidden rounded-2xl border border-primary/10 bg-surface-raised shadow-sm transition-transform hover:-translate-y-1"
            >
              <div className="relative aspect-[16/9] w-full">
                <Image
                  src={momento.imagen}
                  alt={momento.alt}
                  fill
                  loading="lazy"
                  sizes="(max-width: 640px) 100vw, 33vw"
                  className="object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div
                  aria-hidden="true"
                  className="absolute inset-0 bg-gradient-to-t from-brand-deep-navy/90 via-brand-deep-navy/20 to-transparent"
                />
              </div>
              <div className="absolute inset-x-0 bottom-0 p-5">
                <span className="text-[9px] font-black uppercase tracking-[0.25em] text-brand-cyan">
                  {momento.numero} / {momento.etiqueta}
                </span>
                <p className="mt-1 text-lg font-black uppercase leading-tight tracking-tight text-surface-inverse-foreground">
                  {momento.titular}
                </p>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-10 grid gap-6 border-t border-primary/10 pt-8 text-center lg:grid-cols-3 lg:text-left">
          <div className="flex items-center justify-center gap-3 lg:justify-start">
            <MapPin className="size-5 shrink-0 text-info" aria-hidden="true" />
            <div>
              <p className="text-xs font-black uppercase tracking-[0.15em] text-foreground">
                {SEDE.nombre}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {SEDE.bienvenida}
              </p>
            </div>
          </div>

          <p className="self-center text-center text-xs font-black uppercase tracking-[0.25em] text-info lg:text-center">
            {COPY.hero.pie.promesa}
          </p>

          <div className="[&_*]:text-foreground [&_span]:text-muted-foreground">
            <Countdown />
          </div>
        </div>
      </div>
    </section>
  );
}
