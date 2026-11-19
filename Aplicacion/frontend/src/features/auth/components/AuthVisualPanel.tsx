"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { cn } from "@/lib/utils";
import {
  LOGIN_CYCLING_WORDS,
  REGISTER_CYCLING_WORDS,
  type CyclingEntry,
  useCyclingText,
} from "@/features/auth/hooks/useCyclingText";

// =============================================================================
// DEFAULTS — reproduce the login visual panel
// =============================================================================

const DEFAULT_FEATURES = [
  "Fulbito 7 vs 7",
  "Voley Mixto",
  "Basquet 3x3",
  "Premiacion Ekiden",
];

const DEFAULT_EVENT_BADGE = {
  date: "21 NOV",
  place: "Av. Asturias 588 — Ate",
};

// =============================================================================
// CAROUSEL IMAGES — using existing public assets
// =============================================================================

const CAROUSEL_IMAGES = [
  { src: "/images/fulbito-varones.webp", alt: "Fulbito 7 vs 7" },
  { src: "/images/voley-mixto.webp", alt: "Voley Mixto" },
  { src: "/images/basket-varones.webp", alt: "Basket 3x3" },
];

// Multi-direction text shadow so letters stay readable over any part of the image
const TEXT_GLOW: React.CSSProperties = {
  textShadow:
    "0 0 4px rgba(0,0,0,0.85), 0 0 10px rgba(0,0,0,0.7), 0 0 18px rgba(7,8,28,0.85), 0 2px 4px rgba(0,0,0,0.9), -1px -1px 0 rgba(0,0,0,0.6), 1px -1px 0 rgba(0,0,0,0.6), -1px 1px 0 rgba(0,0,0,0.6), 1px 1px 0 rgba(0,0,0,0.6)",
};

const TEXT_GLOW_GOLD: React.CSSProperties = {
  textShadow:
    "0 0 4px rgba(0,0,0,0.85), 0 0 14px rgba(244,197,74,0.7), 0 0 24px rgba(244,197,74,0.5), 0 2px 4px rgba(0,0,0,0.9), -1px -1px 0 rgba(0,0,0,0.6), 1px -1px 0 rgba(0,0,0,0.6), -1px 1px 0 rgba(0,0,0,0.6), 1px 1px 0 rgba(0,0,0,0.6)",
};

// =============================================================================
// PARTY SPARKS — animated confetti particles + smoke clouds
// =============================================================================

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
            yoyo: false,
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

  const sparks = Array.from({ length: 22 });

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 overflow-hidden z-[11]"
    >
      {/* Smoke clouds */}
      <div
        ref={(el) => {
          if (el) smokeRefs.current[0] = el;
        }}
        className="absolute -left-24 top-1/4 h-[55vh] w-[55vh] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(0,123,255,0.7), transparent 70%)",
        }}
      />
      <div
        ref={(el) => {
          if (el) smokeRefs.current[1] = el;
        }}
        className="absolute -right-24 bottom-10 h-[55vh] w-[55vh] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(244,197,74,0.55), transparent 70%)",
        }}
      />
      <div
        ref={(el) => {
          if (el) smokeRefs.current[2] = el;
        }}
        className="absolute left-1/3 top-1/3 h-[40vh] w-[40vh] rounded-full"
        style={{
          background: "radial-gradient(circle, rgba(0,183,212,0.45), transparent 70%)",
        }}
      />

      {/* Sparks */}
      {sparks.map((_, i) => {
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

// =============================================================================
// VISUAL PANEL — full-cover carousel with overlay
// =============================================================================

function VisualPanelInner({
  title,
  subtitle,
  features,
  eventBadge,
  disableSparks,
  cyclingWords,
}: {
  title: string;
  subtitle: string;
  features: string[];
  eventBadge: { date: string; place: string };
  disableSparks?: boolean;
  cyclingWords: CyclingEntry[];
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const keywordRef = useRef<HTMLSpanElement>(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const carouselIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const { currentEntry, mounted } = useCyclingText(cyclingWords);

  const prevIndex = useRef(0);
  const layersRef = useRef<(HTMLDivElement | null)[]>([]);

  const goToImage = (index: number) => {
    if (index === currentImageIndex) return;
    const outIdx = currentImageIndex;
    const inIdx = index;
    prevIndex.current = outIdx;

    const outEl = layersRef.current[outIdx];
    const inEl = layersRef.current[inIdx];
    if (!outEl || !inEl) {
      setCurrentImageIndex(index);
      return;
    }

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    if (prefersReducedMotion) {
      setCurrentImageIndex(index);
      return;
    }

    const FADE = 1.6;

    gsap.set(inEl, { opacity: 0, scale: 1.04, filter: "blur(14px)" });

    gsap.to(outEl, {
      opacity: 0,
      duration: FADE,
      ease: "power1.inOut",
    });

    gsap.to(inEl, {
      opacity: 1,
      scale: 1,
      filter: "blur(0px)",
      duration: FADE,
      ease: "power1.inOut",
      delay: 0.35,
      onStart: () => setCurrentImageIndex(inIdx),
    });
  };

  const nextImage = () => {
    const next = (currentImageIndex + 1) % CAROUSEL_IMAGES.length;
    goToImage(next);
  };

  const startAutoplay = () => {
    stopAutoplay();
    carouselIntervalRef.current = setInterval(nextImage, 5000);
  };

  const stopAutoplay = () => {
    if (carouselIntervalRef.current) {
      clearInterval(carouselIntervalRef.current);
      carouselIntervalRef.current = null;
    }
  };

  // GSAP entrance + cycling
  useEffect(() => {
    if (!panelRef.current || !mounted) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".vp-stagger",
        { y: 40, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.9,
          stagger: 0.12,
          ease: "power3.out",
        },
      );
    }, panelRef);

    if (prefersReducedMotion) {
      ctx.revert();
    }

    return () => {
      ctx.revert();
    };
  }, [mounted]);

  // Smooth keyword fade on word change
  useEffect(() => {
    if (!keywordRef.current) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) {
      gsap.set(keywordRef.current, { y: 0, opacity: 1 });
      return;
    }

    gsap.fromTo(
      keywordRef.current,
      { y: 14, opacity: 0, filter: "blur(6px)" },
      {
        y: 0,
        opacity: 1,
        filter: "blur(0px)",
        duration: 0.7,
        ease: "power1.inOut",
      },
    );
  }, [currentEntry]);

  // Carousel autoplay
  useEffect(() => {
    startAutoplay();
    return () => stopAutoplay();
  }, [currentImageIndex]);

  return (
    <div ref={panelRef} className="vp-panel">
      {/* ---- FULL-COVER CAROUSEL ---- */}
      <div className="absolute inset-0">
        {CAROUSEL_IMAGES.map((img, idx) => (
          <div
            key={img.src}
            ref={(el) => {
              layersRef.current[idx] = el;
            }}
            className="absolute inset-0 will-change-[opacity,transform,filter]"
            style={{
              opacity: idx === currentImageIndex ? 1 : 0,
              zIndex: idx === currentImageIndex ? 10 : 0,
            }}
          >
            <Image
              src={img.src}
              alt={img.alt}
              fill
              className="object-cover"
              priority={idx === 0}
              sizes="(max-width: 1024px) 0vw, 50vw"
            />
          </div>
        ))}

        {/* Fallback gradient if no image loads */}
        <div className="absolute inset-0 bg-gradient-br-primary z-[5]" />
      </div>

      {/* ---- OVERLAY LAYERS ---- */}
      {/* Strong dark base — keeps text readable across the whole image */}
      <div className="absolute inset-0 z-[6]" style={{ background: "rgba(7, 8, 28, 0.68)" }} />

      {/* Blue/purple tint */}
      <div
        className="absolute inset-0 z-[7]"
        style={{
          background:
            "linear-gradient(135deg, rgba(33,30,112,0.45) 0%, rgba(21,87,184,0.30) 50%, rgba(10,10,30,0.55) 100%)",
        }}
      />

      {/* Vignette edges */}
      <div className="absolute inset-0 z-[8] vp-vignette" />

      {/* Subtle grid */}
      <div
        className="absolute inset-0 z-[9] opacity-[0.04] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.5) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />

      {/* Top-to-bottom AND bottom-to-top dark gradient for legibility everywhere */}
      <div
        className="absolute inset-0 z-[10]"
        style={{
          background:
            "linear-gradient(to bottom, rgba(7,8,28,0.85) 0%, rgba(7,8,28,0.35) 30%, rgba(7,8,28,0.55) 70%, rgba(7,8,28,0.92) 100%)",
        }}
      />

      {/* ---- PARTY SPARKS / SMOKE ---- */}
      {!disableSparks && <PartySparks />}

      {/* ---- CONTENT ---- */}
      <div className="relative z-20 flex min-h-svh flex-col justify-center p-10 xl:p-16 space-y-8">
        {/* Eyebrow badge */}
        <div className="vp-stagger">
          <span
            className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/10 px-4 py-1.5 text-xs font-bold uppercase tracking-[.15em] text-white backdrop-blur-sm"
            style={TEXT_GLOW}
          >
            <span className="badge-dot animate-pulse" />
            Promocion 2002 — Bodas de Plata
          </span>
        </div>

        {/* Headline with cycling word */}
        <div className="vp-stagger space-y-2">
          <h2
            className="text-[2.6rem] font-black leading-[1.05] tracking-[-.04em] text-white xl:text-[3.2rem]"
            style={TEXT_GLOW}
          >
            Tu promocion vuelve a {currentEntry.article}{" "}
            <span
              ref={keywordRef}
              className="inline-block text-gold-light"
              style={TEXT_GLOW_GOLD}
            >
              {currentEntry.word}
            </span>
          </h2>
          <p
            className="max-w-sm text-base leading-7 text-white"
            style={TEXT_GLOW}
          >
            {subtitle}
          </p>
        </div>

        {/* Feature pills */}
        <div className="vp-stagger flex flex-wrap gap-3">
          {features.map((feat) => (
            <span key={feat} className="feature-pill" style={TEXT_GLOW}>
              {feat}
            </span>
          ))}
        </div>

        {/* Event info badge */}
        <div className="vp-stagger">
          <div className="inline-flex items-center gap-3 rounded-2xl border border-white/20 bg-white/10 px-5 py-3 backdrop-blur-sm shadow-xl">
            <div className="flex flex-col items-center justify-center rounded-xl bg-gold-dim px-3 py-1">
              <span
                className="text-[10px] font-bold uppercase tracking-wider text-gold"
                style={TEXT_GLOW}
              >
                {eventBadge.date.split(" ")[1]}
              </span>
              <span className="text-xl font-black text-white leading-none" style={TEXT_GLOW}>
                {eventBadge.date.split(" ")[0]}
              </span>
            </div>
            <div className="flex flex-col">
              <p
                className="text-xs font-black uppercase tracking-[.1em] text-white"
                style={TEXT_GLOW}
              >
                Evento principal
              </p>
              <p className="text-sm font-bold text-white" style={TEXT_GLOW}>
                {eventBadge.place}
              </p>
            </div>
          </div>
        </div>

        {/* Carousel indicators */}
        <div className="vp-stagger flex items-center gap-2 pt-2">
          {CAROUSEL_IMAGES.map((_, idx) => (
            <button
              key={idx}
              onClick={() => goToImage(idx)}
              className={cn(
                "carousel-dot",
                idx === currentImageIndex
                  ? "carousel-dot-active"
                  : "carousel-dot-inactive",
              )}
              aria-label={`Ir a imagen ${idx + 1}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// AUTH VISUAL PANEL — public component
// =============================================================================

export interface AuthVisualPanelProps {
  variant?: "login" | "register";
  title?: string;
  subtitle?: string;
  features?: string[];
  eventBadge?: { date: string; place: string };
  /** When true, PartySparks animation is disabled (e.g., when form is mounted to avoid distraction). */
  disableSparks?: boolean;
}

export function AuthVisualPanel({
  variant = "login",
  title: _title,
  subtitle,
  features = DEFAULT_FEATURES,
  eventBadge = DEFAULT_EVENT_BADGE,
  disableSparks = false,
}: AuthVisualPanelProps) {
  const copy = COPY_BY_VARIANT[variant];
  const cyclingWords =
    variant === "register" ? REGISTER_CYCLING_WORDS : LOGIN_CYCLING_WORDS;
  return (
    <VisualPanelInner
      title={_title ?? copy.title}
      subtitle={subtitle ?? copy.subtitle}
      features={features}
      eventBadge={eventBadge}
      disableSparks={disableSparks}
      cyclingWords={cyclingWords}
    />
  );
}

const COPY_BY_VARIANT = {
  login: {
    title: "Tu promocion vuelve a",
    subtitle:
      "Mas de 25 anos de hermandad, deporte y convivencia en las Olimpiadas Deportivas Salesianas.",
  },
  register: {
    title: "Confirma tu",
    subtitle:
      "Registrate para crear tu inscripcion, registrar a tus equipos y completar el pago.",
  },
} as const;
