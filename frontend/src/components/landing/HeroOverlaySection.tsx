"use client";

import { gsap } from "gsap";
import { Calendar, MapPin, ShieldCheck, Sparkles, Trophy } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { PreinscribirButton } from "./PreinscribirButton";

// Carrusel + overlay full-cover inspirado en el AuthVisualPanel del login.
const CAROUSEL_IMAGES = [
  { src: "/images/fulbito-varones.webp", alt: "Fulbito 7 vs 7" },
  { src: "/images/voley-mixto.webp", alt: "Voley Mixto" },
  { src: "/images/basket-varones.webp", alt: "Basket 3x3" },
];

const TEXT_GLOW: React.CSSProperties = {
  textShadow:
    "0 0 4px rgba(0,0,0,0.85), 0 0 10px rgba(0,0,0,0.7), 0 0 18px rgba(7,8,28,0.85), 0 2px 4px rgba(0,0,0,0.9), -1px -1px 0 rgba(0,0,0,0.6), 1px -1px 0 rgba(0,0,0,0.6), -1px 1px 0 rgba(0,0,0,0.6), 1px 1px 0 rgba(0,0,0,0.6)",
};

const TEXT_GLOW_GOLD: React.CSSProperties = {
  textShadow:
    "0 0 4px rgba(0,0,0,0.85), 0 0 14px rgba(244,197,74,0.7), 0 0 24px rgba(244,197,74,0.5), 0 2px 4px rgba(0,0,0,0.9), -1px -1px 0 rgba(0,0,0,0.6), 1px -1px 0 rgba(0,0,0,0.6), -1px 1px 0 rgba(0,0,0,0.6), 1px 1px 0 rgba(0,0,0,0.6)",
};

function PartySparks() {
  const containerRef = useRef<HTMLDivElement>(null);
  const sparkRefs = useRef<HTMLSpanElement[]>([]);
  const smokeRefs = useRef<HTMLDivElement[]>([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      sparkRefs.current.forEach((el) => {
        if (!el) return;
        gsap.fromTo(
          el,
          {
            x: gsap.utils.random(-50, 50),
            y: 30,
            opacity: 0,
            scale: gsap.utils.random(0.4, 1),
          },
          {
            x: `+=${gsap.utils.random(-180, 180)}`,
            y: `-=${gsap.utils.random(180, 380)}`,
            opacity: gsap.utils.random(0.35, 0.95),
            scale: gsap.utils.random(0.6, 1.4),
            duration: gsap.utils.random(3, 6),
            ease: "sine.out",
            repeat: -1,
            delay: gsap.utils.random(0, 4),
          },
        );
      });
      smokeRefs.current.forEach((el) => {
        if (!el) return;
        gsap.fromTo(
          el,
          { opacity: 0, scale: 0.85, filter: "blur(40px)" },
          {
            opacity: gsap.utils.random(0.18, 0.35),
            scale: gsap.utils.random(1.05, 1.25),
            filter: "blur(60px)",
            duration: gsap.utils.random(6, 10),
            ease: "sine.inOut",
            repeat: -1,
            yoyo: true,
            delay: gsap.utils.random(0, 4),
          },
        );
      });
    }, container);

    return () => ctx.revert();
  }, []);

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 overflow-hidden z-[11]"
    >
      <div
        ref={(el) => {
          if (el) smokeRefs.current[0] = el;
        }}
        className="absolute -left-24 top-1/4 h-[55vh] w-[55vh] rounded-full"
        style={{
          background:
            "radial-gradient(circle, rgba(0,123,255,0.7), transparent 70%)",
        }}
      />
      <div
        ref={(el) => {
          if (el) smokeRefs.current[1] = el;
        }}
        className="absolute -right-24 bottom-10 h-[55vh] w-[55vh] rounded-full"
        style={{
          background:
            "radial-gradient(circle, rgba(244,197,74,0.55), transparent 70%)",
        }}
      />
      <div
        ref={(el) => {
          if (el) smokeRefs.current[2] = el;
        }}
        className="absolute left-1/3 top-1/3 h-[40vh] w-[40vh] rounded-full"
        style={{
          background:
            "radial-gradient(circle, rgba(0,183,212,0.45), transparent 70%)",
        }}
      />
      {Array.from({ length: 22 }).map((_, i) => {
        const isYellow = i % 3 === 0;
        const isBlue = i % 3 === 1;
        const color = isYellow
          ? "rgba(244,197,74,0.95)"
          : isBlue
            ? "rgba(0,183,212,0.95)"
            : "rgba(0,123,255,0.95)";
        const size = i % 4 === 0 ? 6 : 4;
        return (
          <span
            key={i}
            ref={(el) => {
              if (el) sparkRefs.current[i] = el;
            }}
            className="absolute rounded-full"
            style={{
              left: `${(i * 53) % 100}%`,
              bottom: `${(i * 23) % 40}%`,
              width: size,
              height: size,
              background: color,
              boxShadow: `0 0 ${size * 3}px ${color}`,
            }}
          />
        );
      })}
    </div>
  );
}

const INFO_CARDS = [
  { icon: Calendar, label: "Fecha oficial", value: "Sábado 21 nov 2026" },
  { icon: MapPin, label: "Sede", value: "Av. Asturias 588 — Ate" },
  { icon: Trophy, label: "Disciplinas", value: "Fulbito · Vóley · Básquet" },
  { icon: ShieldCheck, label: "Estado", value: "Registro sujeto a validación" },
];

export function HeroOverlaySection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const layersRef = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".hero-stagger",
        { y: 40, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.9,
          stagger: 0.1,
          ease: "power3.out",
        },
      );
    }, el);
    return () => ctx.revert();
  }, []);

  useEffect(() => {
    const id = setInterval(() => {
      setCurrentImageIndex((i) => (i + 1) % CAROUSEL_IMAGES.length);
    }, 5500);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const outEl = layersRef.current[currentImageIndex];
    if (!outEl) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;
    gsap.fromTo(
      outEl,
      { opacity: 0, scale: 1.04, filter: "blur(10px)" },
      {
        opacity: 1,
        scale: 1,
        filter: "blur(0px)",
        duration: 1.2,
        ease: "power2.out",
      },
    );
  }, [currentImageIndex]);

  return (
    <section
      ref={sectionRef}
      id="inicio"
      className="relative flex min-h-screen w-full items-center overflow-hidden text-white"
    >
      {/* Background carousel full-cover */}
      <div className="absolute inset-0 z-0">
        {CAROUSEL_IMAGES.map((img, i) => (
          <div
            key={img.src}
            ref={(el) => {
              layersRef.current[i] = el;
            }}
            className="absolute inset-0 transition-opacity duration-1000"
            style={{ opacity: i === currentImageIndex ? 1 : 0 }}
          >
            <Image
              src={img.src}
              alt={img.alt}
              fill
              priority={i === 0}
              className="object-cover"
              sizes="100vw"
            />
          </div>
        ))}
        <div className="absolute inset-0 bg-gradient-to-br from-[#0b0c2c]/85 via-[#1a1857]/75 to-[#312e8e]/80" />
      </div>

      <PartySparks />

      <div className="relative z-10 mx-auto grid w-full max-w-[1280px] gap-6 px-4 py-12 sm:px-6 lg:grid-cols-[1fr_0.65fr] lg:gap-8 lg:px-8 lg:py-16">
        {/* LEFT — texto */}
        <div className="flex flex-col text-white">
          <div className="hero-stagger">
            <span className="text-sm font-black uppercase tracking-[.2em] text-[#d8d8ff]">
              Promoción 2002
            </span>
            <strong className="mt-0.5 block text-2xl font-black text-white">
              Rumbo a Bodas de Plata
            </strong>
          </div>

          <div className="hero-stagger mt-5 inline-flex w-fit items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-bold text-white/90 backdrop-blur">
            <Sparkles className="size-4 text-[#f4c64e]" />
            <span>Deporte, familia y diversión</span>
          </div>

          <h1
            className="hero-stagger mt-4 max-w-2xl text-[2.25rem] font-black leading-[1.05] tracking-[-.045em] text-white sm:text-4xl lg:text-[3.25rem]"
            style={TEXT_GLOW}
          >
            Tu promoción vuelve a la{" "}
            <span style={TEXT_GLOW_GOLD} className="text-[#f4c64e]">
              cancha
            </span>
            .
          </h1>

          <p
            className="hero-stagger mt-4 max-w-xl text-base leading-7 text-[#e5e6ff] lg:text-lg lg:leading-8"
            style={TEXT_GLOW}
          >
            Preinscribe la nómina de tu promoción para las Olimpiadas Deportivas
            Salesianas y prepárense para el gran reencuentro rumbo a la
            Mayordomía 2027.
          </p>

          <div className="hero-stagger mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-2">
            {INFO_CARDS.map((card) => (
              <div
                key={card.label}
                className="rounded-2xl border border-white/15 bg-white/8 p-4 backdrop-blur-md"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f4c64e]/15">
                    <card.icon className="size-5 text-[#f4c64e]" />
                  </div>
                  <div>
                    <p className="text-[11px] font-black uppercase tracking-wider text-[#f4c64e]">
                      {card.label}
                    </p>
                    <p className="mt-0.5 text-sm font-bold text-white">
                      {card.value}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="hero-stagger mt-5 rounded-2xl border border-[#f4c64e]/35 bg-[#f4c64e]/12 p-4 text-sm leading-6 text-[#fff7d6]">
            <strong className="block text-white">
              Bases aprobadas el 5 de septiembre de 2026
            </strong>
            La nómina se validará con carnet de exalumno o padrón oficial. La
            suplantación implica la descalificación del equipo.
          </div>

          <div className="hero-stagger mt-6 flex flex-wrap gap-3">
            <PreinscribirButton
              size="lg"
              className="btn-brand-gradient btn-shine h-14 rounded-2xl px-8 text-base font-black"
            />
            <Button
              asChild
              size="lg"
              variant="outline"
              className="h-14 rounded-2xl border-white/40 bg-white/8 px-8 text-base font-bold text-white hover:bg-white/15"
            >
              <Link href="/">Información del Evento</Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="ghost"
              className="h-14 rounded-2xl px-8 text-base font-bold text-white/80 hover:bg-white/10 hover:text-white"
            >
              <Link href="/login">Ya tengo cuenta</Link>
            </Button>
          </div>
        </div>

        {/* RIGHT — overlay "carousel card" (estilo login visual panel) */}
        <div className="relative hidden lg:flex lg:items-center lg:justify-center">
          <div className="absolute -inset-2 rounded-[2rem] bg-gradient-to-br from-[#f4c64e]/35 via-transparent to-[#0b0c2c]/45 blur-2xl" />
          <div className="relative w-full max-w-md overflow-hidden rounded-[1.75rem] border border-white/15 bg-[#0b0c2c]/40 p-3 shadow-2xl backdrop-blur-xl">
            {/* Logo centered badge */}
            <div className="pointer-events-none absolute left-1/2 top-1/2 z-20 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center">
              <div className="rounded-full bg-white p-2 shadow-[0_0_30px_rgba(244,197,74,0.55)] ring-4 ring-[#f4c64e]/55">
                <Image
                  src="/images/logo.jpeg"
                  alt="Logo oficial Salesianos FEST"
                  width={120}
                  height={120}
                  className="size-28 rounded-full object-cover sm:size-32"
                  priority
                />
              </div>
              <div className="mt-4 rounded-full border border-[#f4c64e]/40 bg-[#0b0c2c]/70 px-4 py-1.5 backdrop-blur">
                <span className="text-[11px] font-black uppercase tracking-[0.3em] text-[#f4c64e]">
                  Salesianos FEST 2026
                </span>
              </div>
            </div>

            {/* Background image */}
            <div className="relative aspect-[4/5] overflow-hidden rounded-2xl">
              {CAROUSEL_IMAGES.map((img, i) => (
                <Image
                  key={img.src}
                  src={img.src}
                  alt={img.alt}
                  fill
                  className="object-cover transition-opacity duration-1000"
                  style={{ opacity: i === currentImageIndex ? 1 : 0 }}
                  sizes="(min-width: 1024px) 35vw, 100vw"
                />
              ))}
              <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/35 to-black/15" />
            </div>

            {/* Bottom caption */}
            <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 p-6">
              <div className="flex items-center gap-2 text-[11px] font-black uppercase tracking-[.18em] text-[#f4c64e]">
                <Sparkles className="size-3.5" />
                Bodas de Plata
              </div>
              <p
                className="mt-1 text-xl font-black leading-tight text-white"
                style={TEXT_GLOW}
              >
                Rumbo a la Mayordomía 2027
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
