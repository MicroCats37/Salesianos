"use client";

import { gsap } from "gsap";
import type { ReactNode } from "react";
import { useEffect, useRef } from "react";

/**
 * The ambient light of the registration form.
 *
 * It is COPIED from the previous frontend
 * (`frontend/src/features/inscripciones/views/InscripcionClientShell.tsx`) and
 * adapted: the four clouds and the eighteen sparks use the TOKENS of the
 * institution instead of literal colours, and the whole movement is off
 * when the visitor asked for reduced motion.
 */
function BrilloDeFormulario() {
  const contenedorRef = useRef<HTMLDivElement>(null);
  const nubeRefs = useRef<HTMLDivElement[]>([]);
  const chispaRefs = useRef<HTMLSpanElement[]>([]);

  useEffect(() => {
    const contenedor = contenedorRef.current;
    if (!contenedor) return;

    const prefiereMenos = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefiereMenos) return;

    const ctx = gsap.context(() => {
      nubeRefs.current.forEach((nube) => {
        if (!nube) return;
        gsap.fromTo(
          nube,
          {
            xPercent: gsap.utils.random(-30, 30),
            yPercent: gsap.utils.random(-20, 20),
            scale: 0.85,
            opacity: 0,
          },
          {
            xPercent: gsap.utils.random(-30, 30),
            yPercent: gsap.utils.random(-20, 20),
            scale: gsap.utils.random(1.1, 1.4),
            opacity: gsap.utils.random(0.18, 0.32),
            duration: gsap.utils.random(6, 11),
            ease: "sine.inOut",
            repeat: -1,
            yoyo: true,
            delay: gsap.utils.random(0, 4),
          },
        );
      });

      chispaRefs.current.forEach((chispa) => {
        if (!chispa) return;
        gsap.fromTo(
          chispa,
          {
            y: 24,
            opacity: 0,
            scale: gsap.utils.random(0.3, 0.7),
          },
          {
            y: -260,
            opacity: gsap.utils.random(0.25, 0.6),
            scale: gsap.utils.random(0.6, 1.2),
            duration: gsap.utils.random(4, 7),
            ease: "sine.out",
            repeat: -1,
            delay: gsap.utils.random(0, 5),
          },
        );
      });
    }, contenedor);

    return () => ctx.revert();
  }, []);

  const nubes = [
    {
      id: "gold",
      color: "var(--accent)",
      top: "10%",
      left: "8%",
      size: "55vh",
    },
    {
      id: "cyan",
      color: "var(--brand-cyan)",
      top: "55%",
      left: "65%",
      size: "50vh",
    },
    {
      id: "purple",
      color: "var(--secondary)",
      top: "75%",
      left: "5%",
      size: "45vh",
    },
    {
      id: "indigo",
      color: "var(--primary)",
      top: "20%",
      left: "70%",
      size: "40vh",
    },
  ];

  const coloresChispa = [
    "var(--accent)",
    "var(--brand-cyan)",
    "var(--primary)",
    "var(--foreground)",
  ];

  return (
    <div
      ref={contenedorRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 z-(--z-toast) overflow-hidden"
    >
      {nubes.map((nube, indice) => (
        <div
          key={nube.id}
          ref={(elemento) => {
            if (elemento) nubeRefs.current[indice] = elemento;
          }}
          className="absolute rounded-full"
          style={{
            top: nube.top,
            left: nube.left,
            width: nube.size,
            height: nube.size,
            background: `radial-gradient(circle, color-mix(in srgb, ${nube.color} 55%, transparent), transparent 70%)`,
            filter: "blur(80px)",
          }}
        />
      ))}

      {Array.from({ length: 18 }).map((_, indice) => {
        const color = coloresChispa[indice % coloresChispa.length];
        const size = indice % 3 === 0 ? 5 : 3;

        return (
          <span
            key={`chispa-${indice}`}
            ref={(elemento) => {
              if (elemento) chispaRefs.current[indice] = elemento;
            }}
            className="absolute rounded-full"
            style={{
              left: `${(indice * 53 + 7) % 100}%`,
              bottom: "0%",
              width: size,
              height: size,
              background: color,
              boxShadow: `0 0 ${size * 4}px ${color}`,
            }}
          />
        );
      })}
    </div>
  );
}

export interface InscripcionClientShellProps {
  children: ReactNode;
}

/**
 * InscripcionClientShell - the surface of the registration form.
 *
 * The page is a GLASS CARD over an ambient light: the form of the festival
 * is the one moment of the product that feels like an event and not like a
 * back office, and the light is what says it.
 */
export function InscripcionClientShell({
  children,
}: InscripcionClientShellProps) {
  const contenedorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const contenedor = contenedorRef.current;
    if (!contenedor) return;

    const prefiereMenos = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefiereMenos) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".rs-stagger",
        { y: 30, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.7,
          stagger: 0.1,
          ease: "power3.out",
        },
      );
    }, contenedor);

    return () => ctx.revert();
  }, []);

  return (
    <div
      ref={contenedorRef}
      className="relative min-h-svh w-full overflow-y-auto px-4 py-6 sm:px-8"
      style={{
        background:
          "radial-gradient(circle at 20% 20%, color-mix(in srgb, var(--accent) 22%, transparent) 0%, transparent 55%)," +
          "radial-gradient(circle at 80% 30%, color-mix(in srgb, var(--info) 18%, transparent) 0%, transparent 55%)," +
          "radial-gradient(circle at 50% 100%, color-mix(in srgb, var(--secondary) 16%, transparent) 0%, transparent 55%)," +
          "linear-gradient(180deg, var(--surface) 0%, color-mix(in srgb, var(--primary) 8%, var(--surface)) 100%)",
        color: "var(--foreground)",
      }}
    >
      <BrilloDeFormulario />

      <div className="rs-stagger relative z-10 mx-auto w-full max-w-6xl py-4">
        <div className="rounded-[var(--radius-xl)] border border-border bg-card/95 p-5 shadow-[var(--elevation-lg)] backdrop-blur-xl sm:p-8">
          {children}
        </div>
      </div>
    </div>
  );
}
