"use client";

import { gsap } from "gsap";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { NeonSmoke } from "@/components/event/NeonSmoke";

const CYCLING_WORDS = [
  { word: "cancha", article: "la" },
  { word: "familia", article: "la" },
  { word: "reencuentro", article: "el" },
  { word: "promocion", article: "la" },
];

function useRotating() {
  const [idx, setIdx] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduced) return;

    const t = setInterval(() => {
      if (!ref.current) return;
      gsap.to(ref.current, {
        opacity: 0,
        y: -16,
        duration: 0.4,
        ease: "power2.in",
        onComplete: () => setIdx((i) => (i + 1) % CYCLING_WORDS.length),
      });
    }, 2400);

    return () => clearInterval(t);
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: animate the new rotating word when idx changes.
  useEffect(() => {
    if (!ref.current) return;
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduced) {
      gsap.set(ref.current, { opacity: 1, y: 0 });
      return;
    }
    gsap.fromTo(
      ref.current,
      { opacity: 0, y: 16 },
      { opacity: 1, y: 0, duration: 0.55, ease: "power3.out" },
    );
  }, [idx]);

  return { ref, entry: CYCLING_WORDS[idx] };
}

interface EventHeroProps {
  images: string[];
}

export function EventHero({ images }: EventHeroProps) {
  const heroRef = useRef<HTMLDivElement>(null);
  const [imgIdx, setImgIdx] = useState(0);
  const { ref: wordRef, entry } = useRotating();

  useEffect(() => {
    if (!heroRef.current) return;
    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduced) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".event-hero-stagger",
        { y: 30, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.9,
          stagger: 0.1,
          ease: "power3.out",
          delay: 0.2,
        },
      );

      const interval = setInterval(() => {
        setImgIdx((v) => (v + 1) % images.length);
      }, 5000);

      return () => clearInterval(interval);
    }, heroRef);

    return () => ctx.revert();
  }, [images.length]);

  return (
    <section
      ref={heroRef}
      className="relative min-h-svh w-full overflow-hidden"
    >
      {/* Image carousel */}
      <div className="absolute inset-0">
        {images.map((src, i) => (
          <div
            key={src}
            className="absolute inset-0"
            style={{
              opacity: i === imgIdx ? 1 : 0,
              transition: "opacity 1.2s ease-in-out",
            }}
          >
            <Image
              src={src}
              alt=""
              fill
              className="object-cover"
              priority={i === 0}
              sizes="100vw"
            />
          </div>
        ))}
      </div>

      {/* Dark overlay gradient */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(135deg, rgba(7,8,28,0.72) 0%, rgba(33,30,112,0.55) 50%, rgba(21,87,184,0.55) 100%)",
        }}
      />

      {/* Neon smoke */}
      <NeonSmoke density="low" />

      {/* Foreground content */}
      <div className="relative z-10 flex min-h-svh flex-col items-center justify-center px-6 py-16 text-center">
        {/* FESTIVAL BANNER — nombre + logo ARRIBA de todo */}
        <div className="event-hero-stagger mb-10 flex flex-col items-center gap-4">
          <div className="relative size-28 sm:size-32">
            <div
              aria-hidden="true"
              className="absolute -inset-3 rounded-full"
              style={{
                background:
                  "conic-gradient(from 0deg, #f4c64e, #ec4899, #6366f1, #22d3ee, #f4c64e)",
                filter: "blur(20px)",
                opacity: 0.32,
                animation: "spin 8s linear infinite",
              }}
            />
            <div
              className="relative h-full w-full overflow-hidden rounded-full border-4 border-white/70 shadow-2xl"
              style={{
                background: "linear-gradient(135deg, #1a1857 0%, #312e8e 100%)",
              }}
            >
              <Image
                src="/logo-oficial-salesianos-2002.jpeg"
                alt="Logo oficial Salesianos 2002 - Bodas de Plata"
                width={128}
                height={128}
                className="h-full w-full object-cover"
                priority
              />
            </div>
          </div>

          <div
            className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-6 py-2 backdrop-blur-md"
            style={{ fontFamily: "'Brush Script MT', 'Comic Sans MS', cursive" }}
          >
            <span
              className="inline-block animate-[goldPulse_2.6s_ease-in-out_infinite] text-2xl sm:text-3xl"
              style={{ color: "var(--brand-cyan-soft)" }}
            >
              Salesianos
            </span>{" "}
            <span className="inline-block animate-[cyanPulse_2.6s_ease-in-out_infinite] text-2xl sm:text-3xl text-brand-cyan">
              FEST
            </span>{" "}
            <span className="text-2xl font-bold text-white sm:text-3xl">
              2026
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.45em] text-[#f4c64e] sm:text-xs">
              · Bodas de Plata ·
            </span>
          </div>
        </div>

        <h1
          className="event-hero-stagger max-w-5xl text-4xl font-black leading-[1.05] tracking-[-0.025em] text-white sm:text-6xl lg:text-7xl"
          style={{ textShadow: "0 0 30px rgba(0,0,0,0.5)" }}
        >
          Tu promocion vuelve a {entry.article}{" "}
          <span
            ref={wordRef}
            className="inline-block"
            style={{
              background:
                "linear-gradient(135deg, #f4c64e 0%, #ec4899 50%, #6366f1 100%)",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
              textShadow: "0 0 30px rgba(236,72,153,0.4)",
            }}
          >
            {entry.word}
          </span>
          .
        </h1>

        <p className="event-hero-stagger mt-6 max-w-2xl text-base leading-7 text-white/85 sm:text-lg">
          Mas de 25 anos de hermandad, deporte y convivencia. Conoce el festival
          que reune a toda la promocion en un solo lugar.
        </p>

        <div className="event-hero-stagger mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="#por-que"
            className="rounded-full bg-gradient-to-r from-[#1557b8] to-[#312e8e] px-8 py-3 text-sm font-black uppercase tracking-wider text-white shadow-2xl shadow-[#1557b8]/40 transition-all hover:scale-105"
          >
            Conoce el festival
          </Link>
          <Link
            href="/"
            className="rounded-full border border-white/30 bg-white/10 px-8 py-3 text-sm font-black uppercase tracking-wider text-white backdrop-blur-sm transition-all hover:bg-white/20"
          >
            Volver al inicio
          </Link>
        </div>

        {/* Carousel indicators */}
        <div className="event-hero-stagger mt-12 flex items-center gap-2">
          {images.map((src, i) => (
            <button
              key={src}
              type="button"
              onClick={() => setImgIdx(i)}
              aria-label={`Ir a imagen ${i + 1}`}
              className="h-2 rounded-full transition-all duration-500"
              style={{
                width: i === imgIdx ? "2.5rem" : "0.5rem",
                background:
                  i === imgIdx
                    ? "linear-gradient(90deg, #f4c64e, #ec4899)"
                    : "rgba(255,255,255,0.35)",
              }}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
