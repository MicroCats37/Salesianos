"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Flag, Trophy } from "lucide-react";
import { useEffect, useRef } from "react";

gsap.registerPlugin(ScrollTrigger);

const DISCIPLINES = [
  {
    code: "fulbito_var",
    num: "01",
    title: "Fulbito varones",
    cupos: "Máximo 12 jugadores",
    cats: "Junior · Senior · Máster · Súper Máster",
  },
  {
    code: "fulbito_dam",
    num: "02",
    title: "Fulbito mujeres",
    cupos: "Máximo 12 jugadoras",
    cats: "Junior · Máster",
  },
  {
    code: "voley_mix",
    num: "03",
    title: "Vóley mixto",
    cupos: "Máximo 12 jugadores",
    cats: "En cancha: mínimo 2 y máximo 3 varones.",
  },
  {
    code: "basket_var",
    num: "04",
    title: "Básquet varones",
    cupos: "Máximo 10 jugadores",
    cats: "Junior · Senior · Máster",
  },
];

const CATEGORY_ROWS = [
  {
    discipline: "Fulbito varones",
    categories:
      "Junior 2012–2025 · Senior 1998–2011 · Máster 1987–1997 · Súper Máster 1970–1986",
  },
  {
    discipline: "Fulbito mujeres",
    categories: "Junior 2001–2024 · Máster 1975–2000",
  },
  {
    discipline: "Básquet varones",
    categories: "Junior 2012–2025 · Senior 1998–2011 · Máster 1970–1997",
  },
  {
    discipline: "Vóley mixto",
    categories:
      "Junior 2012–2025 · Senior 1998–2011 · Máster 1975–1986. La base deja 1987–1997 pendiente de precisión.",
  },
];

export function Disciplines() {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!sectionRef.current) return;

    // Check reduced motion preference early — skip all GSAP if set
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      // Header animation
      gsap.fromTo(
        ".discipline-header",
        { y: 40, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          ease: "power3.out",
          scrollTrigger: {
            trigger: ".discipline-header",
            start: "top 85%",
            once: true,
          },
        },
      );

      // Cards stagger animation
      gsap.fromTo(
        ".discipline-card",
        { y: 80, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.7,
          stagger: 0.15,
          ease: "power3.out",
          scrollTrigger: {
            trigger: ".discipline-cards",
            start: "top 80%",
            once: true,
          },
        },
      );

      // Table rows stagger animation
      gsap.fromTo(
        ".discipline-row",
        { x: -30, opacity: 0 },
        {
          x: 0,
          opacity: 1,
          duration: 0.5,
          stagger: 0.1,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".discipline-table",
            start: "top 85%",
            once: true,
          },
        },
      );
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  return (
    <section
      id="disciplinas"
      ref={sectionRef}
      className="relative overflow-hidden bg-[#17214b] py-24 scroll-mt-20 sm:py-28"
    >
      {/* Decorative background elements */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute -top-40 -right-40 size-80 rounded-full bg-[#312e8e]/40 blur-3xl" />
        <div className="absolute top-1/2 -left-40 size-96 rounded-full bg-[#00bde7]/20 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="discipline-header mx-auto max-w-3xl text-center">
          <p className="text-sm font-black uppercase tracking-[0.25em] text-[#f4c64e]">
            Cobertura Deportiva
          </p>
          <h2 className="mt-4 text-4xl font-black tracking-tight text-white sm:text-5xl">
            Tres disciplinas. Una sola comunidad.
          </h2>
          <p className="mt-5 text-lg leading-8 text-white/70">
            Los cupos son metas operativas del plan maestro y quedarán sujetos a
            las bases, aforo, fixture y validación final del Comité.
          </p>
        </div>

        {/* Cards Grid */}
        <div className="discipline-cards mt-16 grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {DISCIPLINES.map((d) => (
            <article
              key={d.code}
              className="discipline-card group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm transition-all duration-300 hover:border-[#f4c64e]/40 hover:bg-white/10"
            >
              {/* Number badge */}
              <div className="absolute -top-2 -right-2 size-16 rounded-full bg-[#312e8e]/60 flex items-center justify-center">
                <span className="text-2xl font-black text-[#f4c64e]">
                  {d.num}
                </span>
              </div>

              {/* Icon */}
              <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-[#f4c64e]/10">
                <Trophy className="size-6 text-[#f4c64e]" />
              </div>

              {/* Content */}
              <h3 className="text-xl font-black text-white">{d.title}</h3>
              <p className="mt-2 font-bold text-[#f4c64e]">{d.cupos}</p>
              <p className="mt-3 text-sm leading-relaxed text-white/60">
                {d.cats}
              </p>

              {/* Bottom accent line */}
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-[#f4c64e]/60 to-[#f4c64e]/0 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
            </article>
          ))}
        </div>

        {/* Category Table */}
        <div className="discipline-table mt-16 overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
          <div className="grid grid-cols-[1fr_3fr] divide-x divide-white/10">
            <div className="bg-[#312e8e]/30 px-6 py-4">
              <span className="text-xs font-black uppercase tracking-widest text-[#f4c64e]">
                Disciplina
              </span>
            </div>
            <div className="bg-[#312e8e]/30 px-6 py-4">
              <span className="text-xs font-black uppercase tracking-widest text-[#f4c64e]">
                Categorías y años
              </span>
            </div>
          </div>
          {CATEGORY_ROWS.map((row, i) => (
            <div
              key={row.discipline}
              className="discipline-row grid grid-cols-[1fr_3fr] divide-x divide-white/10 border-t border-white/10"
            >
              <div className="px-6 py-4">
                <div className="flex items-center gap-2">
                  <Flag className="size-4 text-[#f4c64e]" />
                  <span className="font-bold text-white">{row.discipline}</span>
                </div>
              </div>
              <div className="px-6 py-4">
                <p className="text-sm leading-relaxed text-white/70">
                  {row.categories}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
