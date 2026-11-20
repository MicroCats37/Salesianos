"use client";

import { gsap } from "gsap";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import {
  type CyclingEntry,
  LOGIN_CYCLING_WORDS,
  REGISTER_CYCLING_WORDS,
  useCyclingText,
} from "@/features/auth/hooks/useCyclingText";
import { cn } from "@/lib/utils";

// =============================================================================
// DEFAULTS — reproduce the login visual panel
// =============================================================================

const DEFAULT_FEATURES = [
  "Fulbito 7 vs 7",
  "Voley Mixto",
  "Basquet 3x3",
  "Premiacion Ekiden",
];

/**
 * The date and the place of the edition, as the brand panel publishes them.
 *
 * It is exported so the collapsed header of the access —the one that replaces
 * the panel below 1024— states the SAME fact and not a second version of it.
 */
export const EVENTO_FEST = {
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

// Multi-direction text shadow so letters stay readable over any part of the image.
//
// The panel is an INVERSE surface: a dark photographic base under light ink.
// Every colour below comes from a ROLE of the token system, never from a
// literal: the panel is dark in BOTH themes and the roles resolve in both.
const TEXT_GLOW: React.CSSProperties = {
  textShadow:
    "0 0 4px color-mix(in srgb, var(--brand-deep-night) 85%, transparent), 0 0 10px color-mix(in srgb, var(--brand-deep-night) 70%, transparent), 0 0 18px color-mix(in srgb, var(--brand-deep-night) 85%, transparent), 0 2px 4px color-mix(in srgb, var(--brand-deep-night) 90%, transparent), -1px -1px 0 color-mix(in srgb, var(--brand-deep-night) 60%, transparent), 1px -1px 0 color-mix(in srgb, var(--brand-deep-night) 60%, transparent), -1px 1px 0 color-mix(in srgb, var(--brand-deep-night) 60%, transparent), 1px 1px 0 color-mix(in srgb, var(--brand-deep-night) 60%, transparent)",
};

const TEXT_GLOW_GOLD: React.CSSProperties = {
  textShadow:
    "0 0 4px color-mix(in srgb, var(--brand-deep-night) 85%, transparent), 0 0 14px color-mix(in srgb, var(--accent) 70%, transparent), 0 0 24px color-mix(in srgb, var(--accent) 50%, transparent), 0 2px 4px color-mix(in srgb, var(--brand-deep-night) 90%, transparent), -1px -1px 0 color-mix(in srgb, var(--brand-deep-night) 60%, transparent), 1px -1px 0 color-mix(in srgb, var(--brand-deep-night) 60%, transparent), -1px 1px 0 color-mix(in srgb, var(--brand-deep-night) 60%, transparent), 1px 1px 0 color-mix(in srgb, var(--brand-deep-night) 60%, transparent)",
};

/** The ink of the inverse surface: light in both themes. */
const INK = "var(--surface-inverse-foreground)";

/** The smoke of the panel: blue, gold and cyan, as roles. */
const HUMO_AZUL = "color-mix(in srgb, var(--info) 70%, transparent)";
const HUMO_ORO = "color-mix(in srgb, var(--accent) 55%, transparent)";
const HUMO_CIAN = "color-mix(in srgb, var(--brand-cyan) 45%, transparent)";

/** The sparks of the panel: the same three roles, at full strength. */
const CHISPA_ORO = "color-mix(in srgb, var(--accent) 95%, transparent)";
const CHISPA_CIAN = "color-mix(in srgb, var(--brand-cyan) 95%, transparent)";
const CHISPA_AZUL = "color-mix(in srgb, var(--info) 95%, transparent)";

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
          background: `radial-gradient(circle, ${HUMO_AZUL}, transparent 70%)`,
        }}
      />
      <div
        ref={(el) => {
          if (el) smokeRefs.current[1] = el;
        }}
        className="absolute -right-24 bottom-10 h-[55vh] w-[55vh] rounded-full"
        style={{
          background: `radial-gradient(circle, ${HUMO_ORO}, transparent 70%)`,
        }}
      />
      <div
        ref={(el) => {
          if (el) smokeRefs.current[2] = el;
        }}
        className="absolute left-1/3 top-1/3 h-[40vh] w-[40vh] rounded-full"
        style={{
          background: `radial-gradient(circle, ${HUMO_CIAN}, transparent 70%)`,
        }}
      />

      {/* Sparks */}
      {sparks.map((_, i) => {
        const isYellow = i % 3 === 0;
        const isBlue = i % 3 === 1;
        const color = isYellow
          ? CHISPA_ORO
          : isBlue
            ? CHISPA_CIAN
            : CHISPA_AZUL;
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
  const carouselIntervalRef = useRef<ReturnType<typeof setInterval> | null>(
    null,
  );
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
        <div className="absolute inset-0 bg-brand-gradient-deep z-[5]" />
      </div>

      {/* ---- OVERLAY LAYERS ---- */}
      {/* Strong dark base — keeps text readable across the whole image */}
      <div
        className="absolute inset-0 z-[6]"
        style={{
          background:
            "color-mix(in srgb, var(--brand-deep-night) 68%, transparent)",
        }}
      />

      {/* Blue/purple tint */}
      <div
        className="absolute inset-0 z-[7]"
        style={{
          background:
            "linear-gradient(135deg, color-mix(in srgb, var(--brand-deep-blue) 45%, transparent) 0%, color-mix(in srgb, var(--info) 30%, transparent) 50%, color-mix(in srgb, var(--brand-deep-night) 55%, transparent) 100%)",
        }}
      />

      {/* Vignette edges */}
      <div
        className="absolute inset-0 z-[8]"
        style={{
          background:
            "radial-gradient(ellipse at center, transparent 45%, color-mix(in srgb, var(--brand-deep-night) 55%, transparent) 100%)",
        }}
      />

      {/* Subtle grid */}
      <div
        className="absolute inset-0 z-[9] opacity-[0.04] pointer-events-none"
        style={{
          backgroundImage: `linear-gradient(color-mix(in srgb, ${INK} 50%, transparent) 1px, transparent 1px), linear-gradient(90deg, color-mix(in srgb, ${INK} 50%, transparent) 1px, transparent 1px)`,
          backgroundSize: "48px 48px",
        }}
      />

      {/* Top-to-bottom AND bottom-to-top dark gradient for legibility everywhere */}
      <div
        className="absolute inset-0 z-[10]"
        style={{
          background:
            "linear-gradient(to bottom, color-mix(in srgb, var(--brand-deep-night) 85%, transparent) 0%, color-mix(in srgb, var(--brand-deep-night) 35%, transparent) 30%, color-mix(in srgb, var(--brand-deep-night) 55%, transparent) 70%, color-mix(in srgb, var(--brand-deep-night) 92%, transparent) 100%)",
        }}
      />

      {/* ---- PARTY SPARKS / SMOKE ---- */}
      {!disableSparks && <PartySparks />}

      {/* ---- CONTENT ---- */}
      <div className="relative z-20 flex min-h-svh flex-col justify-center p-10 xl:p-16 space-y-8">
        {/* Eyebrow badge */}
        <div className="vp-stagger">
          <span
            className="inline-flex items-center gap-2 rounded-full border border-surface-inverse-foreground/25 bg-surface-inverse-foreground/10 px-4 py-1.5 text-eyebrow-brand text-surface-inverse-foreground backdrop-blur-sm"
            style={TEXT_GLOW}
          >
            <span
              className="size-2 shrink-0 animate-pulse rounded-full bg-accent"
              aria-hidden="true"
            />
            Promocion 2002 — Bodas de Plata
          </span>
        </div>

        {/* Headline with cycling word */}
        <div className="vp-stagger space-y-2">
          <h2
            className="text-[2.6rem] font-bold leading-[1.05] text-surface-inverse-foreground xl:text-[3.2rem]"
            style={TEXT_GLOW}
          >
            Tu promocion vuelve a {currentEntry.article}{" "}
            <span
              ref={keywordRef}
              className="inline-block text-accent"
              style={TEXT_GLOW_GOLD}
            >
              {currentEntry.word}
            </span>
          </h2>
          <p
            className="max-w-sm text-base leading-7 text-surface-inverse-foreground"
            style={TEXT_GLOW}
          >
            {subtitle}
          </p>
        </div>

        {/* Feature pills */}
        <div className="vp-stagger flex flex-wrap gap-3">
          {features.map((feat) => (
            <span
              key={feat}
              className="inline-flex items-center rounded-full border border-surface-inverse-foreground/25 bg-surface-inverse-foreground/10 px-4 py-2 text-xs font-semibold text-surface-inverse-foreground backdrop-blur-sm"
              style={TEXT_GLOW}
            >
              {feat}
            </span>
          ))}
        </div>

        {/* Event info badge */}
        <div className="vp-stagger">
          <div className="inline-flex items-center gap-3 rounded-2xl border border-surface-inverse-foreground/20 bg-surface-inverse-foreground/10 px-5 py-3 backdrop-blur-sm shadow-xl">
            <div className="flex flex-col items-center justify-center rounded-xl bg-accent/20 px-3 py-1">
              <span
                className="text-eyebrow-brand text-accent"
                style={TEXT_GLOW}
              >
                {eventBadge.date.split(" ")[1]}
              </span>
              <span
                className="text-xl font-bold text-surface-inverse-foreground leading-none"
                style={TEXT_GLOW}
              >
                {eventBadge.date.split(" ")[0]}
              </span>
            </div>
            <div className="flex flex-col">
              <p
                className="text-eyebrow-brand text-surface-inverse-foreground"
                style={TEXT_GLOW}
              >
                Evento principal
              </p>
              <p
                className="text-sm font-bold text-surface-inverse-foreground"
                style={TEXT_GLOW}
              >
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
              type="button"
              onClick={() => goToImage(idx)}
              className={cn(
                "size-2.5 rounded-full transition-colors",
                idx === currentImageIndex
                  ? "bg-accent"
                  : "bg-surface-inverse-foreground/40 hover:bg-surface-inverse-foreground/70",
              )}
              aria-label={`Ir a imagen ${idx + 1}`}
              aria-current={idx === currentImageIndex ? "true" : undefined}
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
  eventBadge = EVENTO_FEST,
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
