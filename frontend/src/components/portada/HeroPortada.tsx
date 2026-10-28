"use client";

import { gsap } from "gsap";
import { ArrowUpRight } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { FestBrandHeader } from "@/components/branding/FestBrandHeader";
import { COPY } from "@/features/portada/copy";

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
      className="relative flex min-h-svh snap-start flex-col justify-center overflow-hidden"
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
            "linear-gradient(180deg, rgba(7,8,28,0.72) 0%, rgba(26,24,87,0.62) 45%, rgba(12,12,31,0.80) 100%)",
        }}
      />

      <div className="relative z-10 mx-auto w-full max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center text-center">
          <p
            data-hero-stagger
            className="text-[10px] font-black uppercase tracking-[0.35em] text-[#f4c64e] sm:text-xs"
          >
            {COPY.hero.topline}
          </p>
          <p
            data-hero-stagger
            className="mt-2 text-[10px] font-black uppercase tracking-[0.25em] text-white/60"
          >
            {COPY.hero.edicion}
          </p>

          <div
            data-hero-stagger
            className="relative mt-8 grid size-24 place-items-center overflow-hidden rounded-full border-4 border-white/80 shadow-2xl sm:size-32"
            style={{
              background: "linear-gradient(135deg, #1a1857 0%, #312e8e 100%)",
            }}
          >
            <Image
              src="/logo-oficial-salesianos-2002.jpeg"
              alt="Logo oficial Salesianos 2002 - Bodas de Plata"
              fill
              sizes="128px"
              className="object-cover"
            />
          </div>

          <div data-hero-stagger className="mt-6">
            <FestBrandHeader showLogo={false} size="lg" wordmark="brand" />
          </div>

          <p
            data-hero-stagger
            className="mt-5 text-[10px] font-black uppercase tracking-[0.3em] text-[#22d3ee]"
          >
            {COPY.hero.eyebrow}
          </p>

          <h1
            data-hero-stagger
            className="mt-4 max-w-5xl text-4xl font-black uppercase leading-[1.02] tracking-[-0.03em] text-white sm:text-6xl lg:text-7xl"
          >
            {COPY.hero.tituloLineas.map((linea, index) => (
              <span key={linea}>
                {index > 0 && <br />}
                {index === COPY.hero.tituloLineas.length - 1 ? (
                  <em className="not-italic text-[#f4c64e]">{linea}</em>
                ) : (
                  linea
                )}
              </span>
            ))}
          </h1>

          <p
            data-hero-stagger
            className="mt-6 max-w-2xl text-base leading-relaxed text-white/85 sm:text-lg"
          >
            {COPY.hero.descripcion.map((linea) => (
              <span key={linea} className="block">
                {linea}
              </span>
            ))}
          </p>

          <p
            data-hero-stagger
            className="mt-3 text-sm leading-relaxed text-white/60"
          >
            {COPY.hero.comunidad.map((linea) => (
              <span key={linea} className="block">
                {linea}
              </span>
            ))}
          </p>

          <div
            data-hero-stagger
            className="mt-8 flex flex-wrap items-center justify-center gap-3"
          >
            <span className="rounded-full border border-white/30 bg-white/10 px-5 py-2 text-xs font-black uppercase tracking-widest text-white backdrop-blur-sm">
              Campeonato 9:00 a. m.
            </span>
            <span className="rounded-full border border-[#f4c64e]/50 bg-[#f4c64e]/15 px-5 py-2 text-xs font-black uppercase tracking-widest text-[#f4c64e] backdrop-blur-sm">
              Fiesta 6:00 p. m. — 3:00 a. m.
            </span>
          </div>

          <div
            data-hero-stagger
            className="mt-10 flex flex-col items-center gap-4 sm:flex-row"
          >
            <a
              href={COPY.hero.ctaPrimario.href}
              className="inline-flex h-12 items-center justify-center gap-2 rounded-full bg-gradient-to-r from-[#1557b8] via-[#312e8e] to-[#1f2357] px-8 text-xs font-black uppercase tracking-widest text-white shadow-2xl shadow-[#312e8e]/30 transition-transform hover:scale-105"
            >
              {COPY.hero.ctaPrimario.label}
              <ArrowUpRight className="size-4" aria-hidden="true" />
            </a>
            <a
              href={COPY.hero.ctaSecundario.href}
              className="inline-flex h-12 items-center justify-center gap-2 rounded-full border border-white/30 px-6 text-xs font-black uppercase tracking-widest text-white transition-colors hover:bg-white/10"
            >
              {COPY.hero.ctaSecundario.label}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
