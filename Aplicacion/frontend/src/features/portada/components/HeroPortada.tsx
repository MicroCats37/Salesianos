"use client";

import { gsap } from "gsap";
import { ArrowUpRight } from "lucide-react";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { FestBrandHeader } from "@/components/brand/FestBrandHeader";
import { COPY } from "@/features/portada/fixtures/copy";

/** Fondo del hero: las fotos de la referencia, en crossfade. */
const FONDO = [
  {
    src: "/images/portada/familia.png",
    alt: "Familias compartiendo al aire libre, con juegos y un castillo inflable",
  },
  {
    src: "/images/portada/futbol.png",
    alt: "Preparación de un balón de fútbol sobre el césped",
  },
  {
    src: "/images/portada/voley.png",
    alt: "Vóley en el material de presentación del festival",
  },
  {
    src: "/images/portada/basquet.png",
    alt: "Cancha y balón de básquet",
  },
];

/**
 * Portada del festival.
 *
 * Conserva el lenguaje visual de la portada anterior (hero a pantalla
 * completa con carrusel en crossfade, overlay oscuro, escudo circular y
 * wordmark) y adopta el contenido de la referencia: topline, fecha, copy y
 * los tres momentos destacados.
 *
 * VERTICAL: el hero mide el espacio REALMENTE disponible (el viewport menos el
 * navbar sticky), no el viewport entero, y su lockup de marca —escudo y
 * wordmark— se escala con la altura de la pantalla. Sin esto, en un monitor
 * bajo el titular ("UN FESTIVAL. TODA LA FAMILIA.") queda por debajo del
 * pliegue: la sección se repartía el 100% del viewport POR ENCIMA del chrome
 * que ya estaba ocupando 75 px. Es un `min-height`: si el contenido no cabe,
 * la sección crece y nunca recorta.
 */
export function HeroPortada() {
  const rootRef = useRef<HTMLElement>(null);
  const capasRef = useRef<(HTMLDivElement | null)[]>([]);
  const [indice, setIndice] = useState(0);

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

  useEffect(() => {
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduced) return;

    const intervalo = setInterval(() => {
      const siguiente = (indice + 1) % FONDO.length;
      const saliente = capasRef.current[indice];
      const entrante = capasRef.current[siguiente];
      if (!saliente || !entrante) {
        setIndice(siguiente);
        return;
      }

      gsap.set(entrante, { opacity: 0, scale: 1.04, filter: "blur(10px)" });
      gsap.to(saliente, { opacity: 0, duration: 1.1, ease: "power2.inOut" });
      gsap.to(entrante, {
        opacity: 1,
        scale: 1,
        filter: "blur(0px)",
        duration: 1.1,
        ease: "power2.inOut",
        onStart: () => setIndice(siguiente),
      });
    }, 5500);

    return () => clearInterval(intervalo);
  }, [indice]);

  return (
    <section
      ref={rootRef}
      className="relative flex snap-start flex-col justify-center overflow-hidden scroll-mt-[var(--portada-chrome-height)] lg:portada-altura-disponible"
    >
      <div className="absolute inset-0 -z-10">
        {FONDO.map((fondo, i) => (
          <div
            key={fondo.src}
            ref={(elemento) => {
              capasRef.current[i] = elemento;
            }}
            className="absolute inset-0"
            style={{
              opacity: i === 0 ? 1 : 0,
              transition: "opacity 1.1s ease-in-out",
            }}
          >
            <Image
              src={fondo.src}
              alt={fondo.alt}
              fill
              priority={i === 0}
              sizes="100vw"
              className="object-cover"
            />
          </div>
        ))}
      </div>

      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10"
        style={{
          background:
            "linear-gradient(180deg, color-mix(in srgb, var(--brand-deep-night) 72%, transparent) 0%, color-mix(in srgb, var(--brand-deep-blue) 62%, transparent) 45%, color-mix(in srgb, var(--brand-deep-night) 80%, transparent) 100%)",
        }}
      />

      <div className="relative z-10 mx-auto w-full max-w-7xl px-4 py-[clamp(1.5rem,5svh,4rem)] sm:px-6 lg:px-8">
        <div className="flex flex-col items-center text-center">
          <p
            data-hero-stagger
            className="text-[10px] font-black uppercase tracking-[0.35em] text-accent sm:text-xs"
          >
            {COPY.hero.topline}
          </p>
          <p
            data-hero-stagger
            className="mt-2 text-[10px] font-black uppercase tracking-[0.25em] text-surface-inverse-foreground/60"
          >
            {COPY.hero.edicion}
          </p>

          <div
            data-hero-stagger
            className="relative mt-6 grid size-[clamp(4.5rem,13svh,8rem)] place-items-center overflow-hidden rounded-full border-4 border-surface-inverse-foreground/80 shadow-2xl"
            style={{
              background:
                "linear-gradient(135deg, var(--brand-deep-blue) 0%, var(--primary) 100%)",
            }}
          >
            <Image
              src="/logo-oficial-salesianos-2002.jpeg"
              alt="Logo oficial Salesianos 2002 - Bodas de Plata"
              fill
              sizes="(min-width: 1024px) 128px, 104px"
              className="object-cover"
            />
          </div>

          {/*
            El wordmark es el bloque más alto del lockup. A 192 px fijos
            empujaba el titular fuera de la pantalla en cualquier monitor de
            poca altura, así que aquí se acota con la altura disponible.
          */}
          <div data-hero-stagger className="mt-5">
            <FestBrandHeader
              showLogo={false}
              size="lg"
              wordmark="brand"
              wordmarkHeight="clamp(4rem,16svh,12rem)"
            />
          </div>

          <p
            data-hero-stagger
            className="mt-4 text-[10px] font-black uppercase tracking-[0.3em] text-brand-cyan"
          >
            {COPY.hero.eyebrow}
          </p>

          {/*
            El titular se encoge con la altura SOLO cuando la pantalla es baja:
            en un monitor alto conserva los 72 px de siempre.
          */}
          <h1
            data-hero-stagger
            className="mt-3 max-w-5xl text-4xl font-black uppercase leading-[1.02] tracking-[-0.03em] text-surface-inverse-foreground sm:text-6xl lg:text-[clamp(3rem,8svh,4.5rem)]"
          >
            {COPY.hero.tituloLineas.map((linea, index) => (
              <span key={linea}>
                {index > 0 && <br />}
                {index === COPY.hero.tituloLineas.length - 1 ? (
                  <em className="not-italic text-accent">{linea}</em>
                ) : (
                  linea
                )}
              </span>
            ))}
          </h1>

          <p
            data-hero-stagger
            className="mt-6 max-w-2xl text-base leading-relaxed text-surface-inverse-foreground/85 sm:text-lg"
          >
            {COPY.hero.descripcion.map((linea) => (
              <span key={linea} className="block">
                {linea}
              </span>
            ))}
          </p>

          <p
            data-hero-stagger
            className="mt-3 text-sm leading-relaxed text-surface-inverse-foreground/60"
          >
            {COPY.hero.comunidad.map((linea) => (
              <span key={linea} className="block">
                {linea}
              </span>
            ))}
          </p>

          <div
            data-hero-stagger
            className="mt-6 flex flex-wrap items-center justify-center gap-3"
          >
            <span className="rounded-full border border-surface-inverse-foreground/30 bg-surface-inverse-foreground/10 px-5 py-2 text-xs font-black uppercase tracking-widest text-surface-inverse-foreground backdrop-blur-sm">
              Campeonato 9:00 a. m.
            </span>
            <span className="rounded-full border border-accent/50 bg-accent/15 px-5 py-2 text-xs font-black uppercase tracking-widest text-accent backdrop-blur-sm">
              Fiesta 6:00 p. m. — 3:00 a. m.
            </span>
          </div>

          <div
            data-hero-stagger
            className="mt-8 flex flex-col items-center gap-4 sm:flex-row"
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
              className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-brand-on-gradient-border px-6 text-xs font-black uppercase tracking-widest text-brand-on-gradient transition-colors hover:bg-brand-on-gradient-soft"
            >
              {COPY.hero.ctaSecundario.label}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
