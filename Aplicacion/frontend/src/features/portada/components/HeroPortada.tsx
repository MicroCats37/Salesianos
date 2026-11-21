"use client";

import { gsap } from "gsap";
import { ArrowUpRight } from "lucide-react";
import Image from "next/image";
import { useEffect, useRef } from "react";
import { COPY } from "@/features/portada/fixtures/copy";

/**
 * Portada oficial del festival.
 *
 * El cartel es la portada: la imagen ya lleva el wordmark, la fecha y el
 * reclamo de la campaña, así que el hero NO la repite en HTML. Lo que sí vive
 * en el código es el mensaje y las dos acciones.
 */
const PORTADA = {
  escritorio: {
    src: "/images/section/Portada_escritorio_1920x840.webp",
    width: 1920,
    height: 840,
    alt: "Cartel oficial de Salesianos Fest 2026: volvemos a la cancha. 21 de noviembre de 2026 en la Asociación Okinawense del Perú.",
  },
  movil: {
    src: "/images/section/Portada_movil_1080x1350.webp",
    width: 1080,
    height: 1350,
    alt: "Cartel oficial de Salesianos Fest 2026: volvemos a la cancha. 21 de noviembre de 2026 en la Asociación Okinawense del Perú.",
  },
};

/**
 * Portada del festival.
 *
 * El cartel oficial es el HERO: se muestra a su proporción natural —nunca
 * recortado— y el mensaje y las acciones van debajo, sobre la superficie de
 * la página. El titular sigue siendo el `h1` de la web, aunque la imagen ya
 * lo cuente con su propia tipografía.
 */
export function HeroPortada() {
  const rootRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduced) return;

    const ctx = gsap.context(() => {
      gsap.from(root.querySelectorAll("[data-hero-stagger]"), {
        y: 60,
        opacity: 0,
        duration: 1.1,
        stagger: 0.12,
        ease: "power4.out",
      });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={rootRef}
      className="relative flex snap-start flex-col overflow-hidden scroll-mt-[var(--portada-chrome-height)]"
    >
      <h1 className="sr-only">
        {`${COPY.hero.tituloLineas.join(" ")} Salesianos FEST 2026`}
      </h1>

      <div>
        <div className="lg:hidden">
          <Image
            src={PORTADA.movil.src}
            alt={PORTADA.movil.alt}
            width={PORTADA.movil.width}
            height={PORTADA.movil.height}
            priority
            sizes="100vw"
            className="h-auto w-full"
          />
        </div>
        <div className="hidden lg:block">
          <Image
            src={PORTADA.escritorio.src}
            alt={PORTADA.escritorio.alt}
            width={PORTADA.escritorio.width}
            height={PORTADA.escritorio.height}
            priority
            sizes="100vw"
            className="h-auto w-full"
          />
        </div>
      </div>

      <div className="relative z-10 mx-auto w-full max-w-7xl bg-surface px-4 py-9 text-center sm:px-6 sm:py-11 lg:px-8">
        <p data-hero-stagger className="text-eyebrow-brand text-primary">
          {COPY.hero.topline}
        </p>
        <p
          data-hero-stagger
          className="mt-2 text-eyebrow-brand text-muted-foreground"
        >
          {COPY.hero.edicion}
        </p>

        <h2
          data-hero-stagger
          className="mt-4 text-3xl font-black uppercase leading-[1.02] tracking-[-0.03em] text-foreground sm:text-5xl lg:text-6xl"
        >
          {COPY.hero.tituloLineas.map((linea, index) => (
            <span key={linea}>
              {index > 0 && <br />}
              {index === COPY.hero.tituloLineas.length - 1 ? (
                <em className="not-italic text-info">{linea}</em>
              ) : (
                linea
              )}
            </span>
          ))}
        </h2>

        <p
          data-hero-stagger
          className="mt-5 text-base leading-relaxed text-muted-foreground sm:text-lg"
        >
          {COPY.hero.descripcion.map((linea) => (
            <span key={linea} className="block">
              {linea}
            </span>
          ))}
        </p>

        <div
          data-hero-stagger
          className="mt-6 flex flex-wrap items-center justify-center gap-3"
        >
          <span className="rounded-full border border-primary/20 bg-surface-raised px-5 py-2 text-xs font-black uppercase tracking-widest text-primary">
            Campeonato 9:00 a. m.
          </span>
          <span className="rounded-full border border-accent/50 bg-accent/15 px-5 py-2 text-xs font-black uppercase tracking-widest text-accent-muted">
            Fiesta 6:00 p. m. — 3:00 a. m.
          </span>
        </div>

        <div
          data-hero-stagger
          className="mt-7 flex flex-col items-center gap-3 sm:flex-row sm:justify-center"
        >
          <a
            href={COPY.hero.ctaPrimario.href}
            className="btn-shine inline-flex h-12 items-center justify-center gap-2 rounded-full bg-accent px-8 text-xs font-black uppercase tracking-widest text-accent-foreground shadow-glow-brand transition-colors hover:bg-accent-muted"
          >
            {COPY.hero.ctaPrimario.label}
            <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
          <a
            href={COPY.hero.ctaSecundario.href}
            className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-primary/25 px-6 text-xs font-black uppercase tracking-widest text-primary transition-colors hover:bg-primary/5"
          >
            {COPY.hero.ctaSecundario.label}
          </a>
        </div>
      </div>
    </section>
  );
}
