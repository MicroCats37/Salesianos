"use client";

import { MapPin } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { Countdown } from "@/components/portada/Countdown";
import { SEDE } from "@/features/portada/config/festival";
import { COPY } from "@/features/portada/copy";

/**
 * Los tres momentos destacados del festival + el pie con el lugar y la cuenta
 * regresiva.
 *
 * Va en su propia pantalla (y no dentro del hero) para que el hero mida
 * exactamente un viewport: con el scroll-snap, cada sección tiene que caber
 * en una pantalla o deja de ser una sección.
 */
export function MomentosSection() {
  return (
    <section className="surface-page-gradient flex min-h-svh snap-start flex-col justify-center py-16 sm:py-20">
      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-4 sm:grid-cols-3">
          {COPY.hero.momentos.map((momento) => (
            <Link
              key={momento.numero}
              href={momento.href}
              className="group relative overflow-hidden rounded-2xl border border-[#312e8e]/10 bg-white shadow-sm transition-transform hover:-translate-y-1"
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
                  className="absolute inset-0 bg-gradient-to-t from-[#17214b]/90 via-[#17214b]/20 to-transparent"
                />
              </div>
              <div className="absolute inset-x-0 bottom-0 p-5">
                <span className="text-[9px] font-black uppercase tracking-[0.25em] text-[#22d3ee]">
                  {momento.numero} / {momento.etiqueta}
                </span>
                <p className="mt-1 text-lg font-black uppercase leading-tight tracking-tight text-white">
                  {momento.titular}
                </p>
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-10 grid gap-6 border-t border-[#312e8e]/10 pt-8 text-center lg:grid-cols-3 lg:text-left">
          <div className="flex items-center justify-center gap-3 lg:justify-start">
            <MapPin
              className="size-5 shrink-0 text-[#1557b8]"
              aria-hidden="true"
            />
            <div>
              <p className="text-xs font-black uppercase tracking-[0.15em] text-[#17214b]">
                {SEDE.nombre}
              </p>
              <p className="mt-1 text-xs text-[#626195]">{SEDE.bienvenida}</p>
            </div>
          </div>

          <p className="self-center text-center text-xs font-black uppercase tracking-[0.25em] text-[#1557b8] lg:text-center">
            {COPY.hero.pie.promesa}
          </p>

          <div className="[&_*]:text-[#17214b] [&_span]:text-[#626195]">
            <Countdown />
          </div>
        </div>
      </div>
    </section>
  );
}
