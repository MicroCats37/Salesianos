"use client";

import {
  Calendar,
  Check,
  Lock,
  MapPin,
  Music,
  Shield,
  Sparkles,
  Trophy,
  Users,
} from "lucide-react";
import Image from "next/image";
import { useEffect, useRef } from "react";
import { LightRays } from "@/components/event/LightRays";
import { NeonSmoke } from "@/components/event/NeonSmoke";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

interface BulletItem {
  icon: keyof typeof ICON_MAP;
  title: string;
  description?: string;
}

const ICON_MAP = {
  deporte: { Component: Trophy, bg: "#10b981" },
  familia: { Component: Users, bg: "#f59e0b" },
  musica: { Component: Music, bg: "#ec4899" },
  fiesta: { Component: Sparkles, bg: "#a855f7" },
  trofeo: { Component: Trophy, bg: "#3b82f6" },
  cancha: { Component: Trophy, bg: "#0ea5e9" },
  escenario: { Component: Music, bg: "#ef4444" },
  escudo: { Component: Shield, bg: "#22d3ee" },
  bano: { Component: Lock, bg: "#22d3ee" },
  parking: { Component: Calendar, bg: "#3b82f6" },
  puerta: { Component: Check, bg: "#ec4899" },
  carrusel: { Component: MapPin, bg: "#a855f7" },
  comida: { Component: Sparkles, bg: "#f59e0b" },
  palco: { Component: Trophy, bg: "#6366f1" },
};

interface EventBlockProps {
  id?: string;
  eyebrow: string;
  headline: React.ReactNode;
  pill: string;
  paragraph: string;
  bullets: BulletItem[];
  images: { src: string; alt: string }[];
  ribbon: string;
  flipped?: boolean;
  chips?: string[];
  festivalBadge?: boolean;
}

export function EventBlock({
  id,
  eyebrow,
  headline,
  pill,
  paragraph,
  bullets,
  images,
  ribbon,
  flipped,
  chips,
  festivalBadge,
}: EventBlockProps) {
  const blockRef = useRef<HTMLDivElement>(null);
  const leftRef = useRef<HTMLDivElement>(null);
  const rightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = blockRef.current;
    if (!el) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;

    const ctx = gsap.context(() => {
      // Text reveal on enter
      gsap.from(el.querySelectorAll("[data-stagger]"), {
        y: 50,
        opacity: 0,
        duration: 1,
        stagger: 0.08,
        ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 78%", once: true },
      });

      // Collage reveal
      gsap.from(el.querySelectorAll("[data-collage]"), {
        y: 80,
        opacity: 0,
        scale: 0.85,
        duration: 1.3,
        stagger: 0.15,
        ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 72%", once: true },
      });

      // Parallax for eyebrow, headline and ribbon while scrolling
      gsap.to(el.querySelectorAll("[data-parallax='up']"), {
        y: -50,
        ease: "none",
        scrollTrigger: {
          trigger: el,
          start: "top bottom",
          end: "bottom top",
          scrub: 1,
        },
      });

      gsap.to(el.querySelectorAll("[data-parallax='down']"), {
        y: 50,
        ease: "none",
        scrollTrigger: {
          trigger: el,
          start: "top bottom",
          end: "bottom top",
          scrub: 1,
        },
      });

      // Floating collage items
      gsap.to(el.querySelectorAll("[data-float]"), {
        y: -20,
        duration: 3,
        ease: "sine.inOut",
        repeat: -1,
        yoyo: true,
        stagger: 0.4,
      });
    }, el);

    return () => ctx.revert();
  }, []);

  return (
    <section
      id={id}
      ref={blockRef}
      className="event-snap relative flex min-h-svh w-full items-center overflow-hidden py-16 sm:py-20 lg:py-24"
      style={{
        background:
          "linear-gradient(180deg, #ffffff 0%, #f4f6fb 50%, #eef1f8 100%)",
      }}
    >
      <NeonSmoke density="low" />
      <LightRays count={6} />

      {festivalBadge && (
        <div
          data-stagger
          data-parallax="up"
          className="relative z-10 mx-auto mb-10 flex max-w-7xl items-center justify-center gap-4 px-4 sm:px-6 lg:px-8"
        >
          <div className="flex w-full flex-col items-center gap-4 rounded-3xl border border-white/40 bg-white/80 px-6 py-5 shadow-2xl backdrop-blur-md sm:flex-row sm:gap-6 sm:py-6">
            <div
              className="relative size-20 shrink-0 animate-[badgePulse_3s_ease-in-out_infinite]"
              aria-hidden="true"
            >
              <div
                className="absolute inset-0 rounded-full"
                style={{
                  background:
                    "linear-gradient(135deg, #f4c64e 0%, #ec4899 50%, #6366f1 100%)",
                  filter: "blur(10px)",
                  opacity: 0.6,
                }}
              />
              <div
                className="relative h-full w-full overflow-hidden rounded-full border-4 border-white/70 shadow-2xl"
                style={{
                  background:
                    "linear-gradient(135deg, #1a1857 0%, #312e8e 100%)",
                }}
              >
                <Image
                  src="/logo-oficial-salesianos-2002.jpeg"
                  alt="Logo oficial Salesianos 2002 - Bodas de Plata"
                  width={80}
                  height={80}
                  className="h-full w-full object-cover"
                  priority
                />
              </div>
            </div>
            <div className="text-center sm:text-left">
              <p className="text-xs font-black uppercase tracking-[0.3em] text-[#1557b8]">
                Salesianos FEST
              </p>
              <p
                className="text-3xl font-black tracking-tight text-[#1f2357] sm:text-4xl"
                style={{
                  fontFamily: "'Brush Script MT', 'Comic Sans MS', cursive",
                  background:
                    "linear-gradient(135deg, #f4c64e 0%, #ec4899 50%, #6366f1 100%)",
                  WebkitBackgroundClip: "text",
                  backgroundClip: "text",
                  color: "transparent",
                }}
              >
                Lima 2026
              </p>
              <p className="mt-1 text-[10px] font-black uppercase tracking-[0.35em] text-[#6366f1]">
                · Bodas de Plata ·
              </p>
            </div>
            <span
              className="mx-auto inline-block rounded-full bg-[#1557b8] px-5 py-2 text-xs font-black uppercase tracking-wider text-white shadow-lg sm:ml-auto sm:mx-0"
            >
              Promocion 2002
            </span>
          </div>
        </div>
      )}

      <div
        className={`relative z-10 mx-auto grid max-w-7xl items-center gap-12 px-4 sm:px-6 lg:grid-cols-[1.05fr_1fr] lg:gap-16 lg:px-8 ${
          flipped ? "lg:[&>*:first-child]:order-last" : ""
        }`}
      >
        {/* LEFT */}
        <div ref={leftRef} className="space-y-6">
          <p
            data-stagger
            className="text-xs sm:text-sm font-black uppercase tracking-[0.35em] text-[#1557b8]"
          >
            {eyebrow}
            <span className="ml-3 inline-block h-px w-12 align-middle bg-[#22d3ee]" />
          </p>

          <h2
            data-stagger
            className="font-black leading-[1.05] tracking-[-0.025em] text-[#1f2357]"
            style={{ fontSize: "clamp(1.85rem, 4vw, 2.85rem)" }}
          >
            {headline}
          </h2>

          <div
            data-stagger
            className="inline-block max-w-full rounded-lg bg-[#1557b8] px-5 py-3 text-sm font-black uppercase tracking-wider text-white shadow-lg"
          >
            {pill}
          </div>

          <p
            data-stagger
            className="max-w-xl text-base leading-7 text-[#17214b]/85 sm:text-lg"
          >
            {paragraph}
          </p>

          <ul className="space-y-4">
            {bullets.map((b, i) => {
              const IconCfg = ICON_MAP[b.icon];
              return (
                <li
                  key={i}
                  data-stagger
                  className="flex items-start gap-4"
                >
                  <span
                    className="grid size-12 shrink-0 place-items-center rounded-full shadow-md transition-transform hover:scale-110"
                    style={{ backgroundColor: IconCfg.bg }}
                  >
                    <IconCfg.Component className="size-5 text-white" aria-hidden="true" />
                  </span>
                  <div>
                    <p className="text-base font-black text-[#1f2357] sm:text-lg">
                      {b.title}
                    </p>
                    {b.description && (
                      <p className="mt-1 text-sm text-[#17214b]/70">
                        {b.description}
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>

          {chips && chips.length > 0 && (
            <div data-stagger className="flex flex-wrap gap-2 pt-2">
              {chips.map((c) => (
                <span
                  key={c}
                  className="rounded-full border border-[#1557b8]/30 bg-white/70 px-4 py-1.5 text-xs font-black uppercase tracking-wider text-[#1557b8] shadow-sm"
                >
                  {c}
                </span>
              ))}
            </div>
          )}

          <div
            data-stagger
            className="relative mt-8 overflow-hidden rounded-2xl bg-gradient-to-r from-[#1557b8] via-[#312e8e] to-[#1f2357] px-6 py-5 shadow-2xl shadow-[#1557b8]/30"
          >
            <p
              className="relative text-lg font-black uppercase tracking-wider text-white sm:text-xl"
              style={{
                fontFamily: "'Brush Script MT', 'Comic Sans MS', cursive",
                letterSpacing: "0.04em",
              }}
            >
              {ribbon}
            </p>
            <span
              aria-hidden="true"
              className="absolute bottom-1 left-6 right-6 h-0.5 rounded-full"
              style={{
                background:
                  "linear-gradient(90deg, transparent, rgba(255,255,255,0.7), transparent)",
              }}
            />
          </div>
        </div>

        {/* RIGHT — COLLAGE estilo mockup (1 dominante + 2 recortes diagonales) */}
        <div ref={rightRef} className="relative h-[460px] sm:h-[560px] lg:h-[640px]">
          <div
            aria-hidden="true"
            className="absolute -inset-10 -z-10 opacity-90"
            style={{
              background:
                "radial-gradient(ellipse at 60% 40%, rgba(99,102,241,0.45) 0%, rgba(34,211,238,0.25) 35%, rgba(236,72,153,0.18) 65%, transparent 80%)",
              filter: "blur(60px)",
            }}
          />

          {/* Dominant image (right side, ~70% width) */}
          {images[0] && (
            <div
              data-collage
              data-parallax="up"
              className="absolute right-0 top-0 h-full w-[72%] overflow-hidden rounded-[2rem] border border-white/40 shadow-2xl"
              style={{
                clipPath:
                  "polygon(10% 0, 100% 4%, 100% 100%, 6% 96%, 0 12%)",
              }}
            >
              <Image
                src={images[0].src}
                alt={images[0].alt}
                fill
                className="object-cover"
                sizes="(max-width: 1024px) 100vw, 55vw"
              />
              <div
                aria-hidden="true"
                className="absolute inset-0"
                style={{
                  background:
                    "linear-gradient(180deg, transparent 55%, rgba(31,35,87,0.6) 100%)",
                }}
              />
            </div>
          )}

          {/* Bottom-left diagonal accent (~50%) */}
          {images[1] && (
            <div
              data-collage
              data-parallax="down"
              data-float
              className="absolute bottom-0 left-0 h-[55%] w-[52%] overflow-hidden rounded-[1.5rem] border border-white/40 shadow-2xl"
              style={{
                clipPath:
                  "polygon(12% 0, 100% 8%, 96% 100%, 0 92%, 0 18%)",
              }}
            >
              <Image
                src={images[1].src}
                alt={images[1].alt}
                fill
                className="object-cover"
                sizes="(max-width: 1024px) 55vw, 32vw"
              />
              <div
                aria-hidden="true"
                className="absolute inset-0"
                style={{
                  background:
                    "linear-gradient(180deg, transparent 50%, rgba(31,35,87,0.55) 100%)",
                }}
              />
            </div>
          )}

          {/* Top-right diagonal accent strip (~28%) */}
          {images[2] && (
            <div
              data-collage
              data-parallax="up"
              data-float
              className="absolute right-0 top-[6%] h-[32%] w-[28%] overflow-hidden rounded-xl border border-white/40 shadow-2xl"
              style={{
                clipPath:
                  "polygon(0 18%, 100% 0, 100% 100%, 0 82%)",
              }}
            >
              <Image
                src={images[2].src}
                alt={images[2].alt}
                fill
                className="object-cover"
                sizes="(max-width: 1024px) 35vw, 22vw"
              />
              <div
                aria-hidden="true"
                className="absolute inset-0"
                style={{
                  background:
                    "linear-gradient(180deg, transparent 50%, rgba(31,35,87,0.55) 100%)",
                }}
              />
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
