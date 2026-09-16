"use client";

import { gsap } from "gsap";
import { Calendar, MapPin, ShieldCheck, Sparkles, Trophy } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";

const CYCLING_WORDS = ["cancha", "familia", "reencuentro", "promocion"];

export function Hero() {
  const heroRef = useRef<HTMLDivElement>(null);
  const keywordRef = useRef<HTMLSpanElement>(null);
  const isRunning = useRef(true);
  const [currentWord, setCurrentWord] = useState(CYCLING_WORDS[0]!);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!heroRef.current || !mounted) return;

    // Check reduced-motion BEFORE running any animations
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    // Entrance animations — always set explicit destination opacity
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".hero-title-line",
        { y: 80, opacity: 0 },
        { y: 0, opacity: 1, duration: 1, stagger: 0.15, ease: "power3.out" },
      );
      gsap.fromTo(
        ".hero-stagger",
        { y: 30, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          stagger: 0.1,
          delay: 0.6,
          ease: "power2.out",
        },
      );
      gsap.fromTo(
        ".hero-orb",
        { scale: 0, opacity: 0 },
        {
          scale: 1,
          opacity: 1,
          duration: 1.5,
          stagger: 0.2,
          ease: "elastic.out(1, 0.5)",
        },
      );
    }, heroRef);

    if (prefersReducedMotion) {
      ctx.revert();
      return;
    }

    let wordIdx = 0;

    async function animateKeywordOut() {
      if (!keywordRef.current) return;
      await new Promise<void>((resolve) => {
        gsap.to(keywordRef.current, {
          opacity: 0,
          duration: 0.2,
          ease: "power2.in",
          onComplete: resolve,
        });
      });
    }

    async function animateKeywordIn() {
      if (!keywordRef.current) return;
      gsap.fromTo(
        keywordRef.current,
        { opacity: 0 },
        { opacity: 1, duration: 0.35, ease: "power2.out" },
      );
      await new Promise((r) => setTimeout(r, 2200));
    }

    async function runCycle() {
      while (isRunning.current) {
        await animateKeywordIn();
        if (!isRunning.current) break;
        await animateKeywordOut();
        if (!isRunning.current) break;
        wordIdx = (wordIdx + 1) % CYCLING_WORDS.length;
        setCurrentWord(CYCLING_WORDS[wordIdx]!);
        if (!isRunning.current) break;
        await new Promise((r) => setTimeout(r, 50));
      }
    }

    isRunning.current = true;
    runCycle();

    return () => {
      isRunning.current = false;
      ctx.revert();
    };
  }, [mounted]);

  return (
    <section
      id="inicio"
      ref={heroRef}
      className="relative overflow-hidden text-white scroll-mt-20"
    >
      {/* Background gradient */}
      <div className="absolute inset-0 -z-10 bg-[linear-gradient(132deg,#211e70_0%,#312e8e_48%,#1557b8_100%)]" />
      {/* Orbs */}
      <div className="hero-orb absolute left-[8%] top-20 -z-10 size-64 rounded-full bg-[#6976ff]/25 blur-3xl" />
      <div className="hero-orb absolute right-[2%] top-24 -z-10 size-80 rounded-full bg-[#00bde7]/16 blur-3xl" />

      <div className="mx-auto grid max-w-[1280px] gap-6 px-4 pb-10 pt-6 sm:px-6 lg:grid-cols-[1fr_0.65fr] lg:gap-8 lg:px-8 lg:pb-16 lg:pt-8">
        {/* LEFT COLUMN */}
        <div className="flex flex-col text-white">
          {/* Text-only brand block — no image duplication */}
          <div className="hero-stagger">
            <span className="text-sm font-black uppercase tracking-[.2em] text-[#d8d8ff]">
              Promocion 2002
            </span>
            <strong className="mt-0.5 block text-2xl font-black text-white">
              Rumbo a Bodas de Plata
            </strong>
          </div>

          {/* Chip */}
          <div className="hero-stagger mt-5 inline-flex w-fit items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-bold text-white/90 backdrop-blur">
            <Sparkles className="size-4 text-[#f4c64e]" />
            <span>Deporte, familia y diversion</span>
          </div>

          {/* Headline with GSAP cycling word */}
          <h1 className="hero-title-line mt-4 max-w-2xl text-[2.5rem] font-black leading-[1.02] tracking-[-.045em] text-white sm:text-4xl lg:text-[3.25rem]">
            Tu promoción vuelve a la{" "}
            <span ref={keywordRef} className="inline-block text-gradient-gold">
              {currentWord}
            </span>
            .
          </h1>

          {/* Paragraph */}
          <p className="hero-stagger mt-4 max-w-xl text-base leading-7 text-[#e5e6ff] lg:text-lg lg:leading-8">
            Preinscribe la nomina de tu promocion para las Olimpiadas Deportivas
            Salesianas y preparense para el gran reencuentro rumbo a la
            Mayordomia 2027.
          </p>

          {/* Info cards grid */}
          <div className="hero-stagger mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
            <InfoCard
              icon={Calendar}
              label="Fecha oficial"
              value="Sabado 21 nov 2026"
            />
            <InfoCard
              icon={MapPin}
              label="Sede"
              value="Av. Asturias 588 - Ate"
            />
            <InfoCard
              icon={Trophy}
              label="Disciplinas"
              value="Fulbito - Voley - Basquet"
            />
            <InfoCard
              icon={ShieldCheck}
              label="Estado"
              value="Registro sujeto a validacion"
            />
          </div>

          {/* Notice box */}
          <div className="hero-stagger mt-5 rounded-2xl border border-[#f4c64e]/35 bg-[#f4c64e]/12 p-4 text-sm leading-6 text-[#fff7d6]">
            <strong className="block text-white">
              Bases aprobadas el 5 de septiembre de 2026
            </strong>
            La nomina se validara con carnet de exalumno o padron oficial. La
            suplantacion implica la descalificacion del equipo.
          </div>

          {/* CTA buttons */}
          <div className="hero-stagger mt-6 flex flex-wrap gap-3">
            <Button
              asChild
              size="lg"
              className="btn-brand-gradient btn-shine h-14 rounded-2xl px-8 text-base font-black"
            >
              <Link href="/register">Preinscribir equipo</Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="h-14 rounded-2xl border-white/30 bg-white/10 px-8 text-base font-black text-white backdrop-blur hover:bg-white/20 hover:text-white"
            >
              <Link href="/login">Ya tengo cuenta</Link>
            </Button>
          </div>

          {/* Social media links */}
          <div className="hero-stagger mt-6 flex items-center gap-4">
            <span className="text-sm font-bold text-white/60">Siguenos:</span>
            <div className="flex gap-3">
              <a
                href="https://www.facebook.com/share/1EgEPXVFU3/?mibextid=wwXIfr"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Facebook"
                className="flex size-9 items-center justify-center rounded-xl bg-white/10 text-white transition-colors hover:bg-white/20"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                </svg>
              </a>
              <a
                href="https://www.instagram.com/salesianos2002bodasdeplata?stkn=MWVwd3FxcXZ0ZzVhNg%3D%3D&utm_source=qr"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Instagram"
                className="flex size-9 items-center justify-center rounded-xl bg-white/10 text-white transition-colors hover:bg-white/20"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
                </svg>
              </a>
              <a
                href="https://www.tiktok.com/@salesianos.2002"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="TikTok"
                className="flex size-9 items-center justify-center rounded-xl bg-white/10 text-white transition-colors hover:bg-white/20"
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.77 1.52V6.84a4.83 4.83 0 01-1.01-.15z" />
                </svg>
              </a>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN — official image as main visual */}
        <div className="hidden lg:flex items-start pt-0">
          <div className="hero-stagger w-full overflow-hidden rounded-[1.5rem] border-2 border-white/25 bg-white/8 shadow-[0_32px_80px_rgba(7,10,52,.45)] backdrop-blur">
            {/* Official image — the ONE instance in Hero */}
            <div className="relative">
              <img
                src="/logo-oficial-salesianos-2002.jpeg"
                alt="Logotipo oficial Salesianos 2002 - Bodas de Plata"
                width={640}
                height={640}
                className="w-full object-contain"
                style={{ maxHeight: "480px" }}
              />
              {/* Overlay badge */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#0d0d2b]/90 to-transparent p-4 text-center">
                <p className="text-xs font-bold uppercase tracking-[.13em] text-[#bfc3ff]">
                  25 anos de hermandad
                </p>
                <p className="mt-0.5 text-lg font-black text-white">
                  2002 - 2027
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function InfoCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-white/16 bg-white/9 p-4 backdrop-blur">
      <div className="flex items-center gap-3">
        <span className="grid size-9 place-items-center rounded-xl bg-white/10 text-[#f4c64e]">
          <Icon className="size-5" />
        </span>
        <div>
          <span className="block text-xs font-bold uppercase tracking-[.13em] text-[#bfc3ff]">
            {label}
          </span>
          <strong className="mt-1 block text-sm text-white">{value}</strong>
        </div>
      </div>
    </div>
  );
}
