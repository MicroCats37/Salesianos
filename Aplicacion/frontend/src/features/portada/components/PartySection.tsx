"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowRight } from "lucide-react";
import Image from "next/image";
import { useEffect, useRef } from "react";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { COPY } from "@/features/portada/fixtures/copy";
import { SECCIONES } from "@/features/portada/fixtures/festival";

gsap.registerPlugin(ScrollTrigger);

/**
 * Sección "04 / LA GRAN FIESTA".
 *
 * Fondo a pantalla completa con overlay de marca, titular, horario de la
 * noche, lineup, beneficios y las dos llamadas a la acción. El parallax
 * mueve la foto más lento que el texto.
 */
export function PartySection() {
  const rootRef = useRef<HTMLDivElement>(null);
  const fondoRef = useRef<HTMLDivElement>(null);
  const contenidoRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    const fondo = fondoRef.current;
    const contenido = contenidoRef.current;
    if (!root || !fondo || !contenido) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        fondo,
        { y: -14 },
        {
          y: 14,
          ease: "none",
          scrollTrigger: {
            trigger: root,
            start: "top bottom",
            end: "bottom top",
            scrub: 1,
          },
        },
      );
      gsap.fromTo(
        contenido,
        { y: 0 },
        {
          y: -40,
          ease: "none",
          scrollTrigger: {
            trigger: root,
            start: "top bottom",
            end: "bottom top",
            scrub: 1,
          },
        },
      );
    }, root);
    return () => ctx.revert();
  }, []);

  const destacado = COPY.fiesta.titulo.find((linea) =>
    linea.endsWith(COPY.fiesta.destacado),
  );

  return (
    <PortadaSection
      id="fiesta"
      fondo="inverso"
      eyebrow={COPY.fiesta.eyebrow}
      titulo={[...COPY.fiesta.titulo]}
      destacado={destacado}
      copy={[...COPY.fiesta.copy]}
      className="relative isolate overflow-hidden"
    >
      <div ref={rootRef} className="mt-16">
        <div
          className="absolute inset-0 -z-10 overflow-hidden"
          aria-hidden="true"
        >
          <div
            ref={fondoRef}
            className="absolute inset-x-0 -top-[12%] h-[124%]"
          >
            <Image
              src="/images/portada/salon.png"
              alt="Salón de eventos de la Asociación Okinawense del Perú, sede de la fiesta"
              fill
              loading="lazy"
              sizes="100vw"
              className="object-cover"
            />
          </div>
          <div className="absolute inset-0 bg-[linear-gradient(180deg,color-mix(in_srgb,var(--brand-deep-navy)_94%,transparent)_0%,color-mix(in_srgb,var(--brand-deep-navy)_78%,transparent)_45%,color-mix(in_srgb,var(--brand-deep-navy)_95%,transparent)_100%)]" />
        </div>

        <div
          ref={contenidoRef}
          className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-start lg:gap-16"
        >
          <div className="lg:order-2">
            <div className="flex items-center gap-5 lg:justify-end">
              <p className="sr-only">
                {`${COPY.fiesta.inicio.hora} (${COPY.fiesta.inicio.dia}) — ${COPY.fiesta.fin.hora} (${COPY.fiesta.fin.dia})`}
              </p>
              <div className="text-right">
                <b className="block text-4xl font-black leading-none text-surface-inverse-foreground sm:text-5xl">
                  {COPY.fiesta.inicio.hora}
                </b>
                <span className="mt-2 block text-[10px] font-black uppercase tracking-[0.3em] text-brand-cyan">
                  {COPY.fiesta.inicio.dia}
                </span>
              </div>
              <span
                className="h-px w-8 bg-surface-inverse-foreground/40"
                aria-hidden="true"
              />
              <div>
                <b className="block text-4xl font-black leading-none text-surface-inverse-foreground sm:text-5xl">
                  {COPY.fiesta.fin.hora}
                </b>
                <span className="mt-2 block text-[10px] font-black uppercase tracking-[0.3em] text-brand-cyan">
                  {COPY.fiesta.fin.dia}
                </span>
              </div>
            </div>
          </div>

          <div className="lg:order-1">
            <p className="flex flex-wrap items-center gap-3 text-lg font-black uppercase tracking-[0.15em] text-surface-inverse-foreground sm:text-xl">
              {COPY.fiesta.lineup.map((artista, indice) => (
                <span key={artista} className="flex items-center gap-3">
                  {indice > 0 && (
                    <span className="text-accent" aria-hidden="true">
                      ＋
                    </span>
                  )}
                  {artista}
                </span>
              ))}
            </p>

            <ul className="mt-8 flex flex-wrap gap-3">
              {COPY.fiesta.features.map((feature) => (
                <li
                  key={feature}
                  className="rounded-full border border-surface-inverse-foreground/20 bg-surface-inverse-foreground/10 px-4 py-2 text-[11px] font-black uppercase tracking-wider text-surface-inverse-foreground/90"
                >
                  {feature}
                </li>
              ))}
            </ul>

            <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <a
                href={`#${SECCIONES.paquetes}`}
                className="btn-shine inline-flex h-12 items-center justify-center gap-2 rounded-full bg-accent px-6 text-sm font-black uppercase tracking-widest text-accent-foreground shadow-glow-brand transition-colors hover:bg-accent-muted"
              >
                {COPY.fiesta.ctaPrimario.label}
                <ArrowRight className="size-4" aria-hidden="true" />
              </a>
              <a
                href={`#${COPY.paseFiesta.id}`}
                className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-surface-inverse-foreground/35 px-5 text-xs font-black uppercase tracking-wider text-surface-inverse-foreground transition-colors hover:bg-surface-inverse-foreground/10"
              >
                {COPY.fiesta.ctaSecundario.label}
              </a>
            </div>

            <p className="mt-6 text-xs leading-relaxed text-surface-inverse-foreground/60">
              {COPY.fiesta.nota}
            </p>
          </div>
        </div>
      </div>
    </PortadaSection>
  );
}
