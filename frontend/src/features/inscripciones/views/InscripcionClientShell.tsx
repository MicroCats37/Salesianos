"use client";

import { gsap } from "gsap";
import { useEffect, useRef } from "react";
import { InscripcionWizard } from "../components/InscripcionWizard";

// ── SubtleFormSparks (light theme) ───────────────────────────────────────────

function SubtleFormSparks() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cloudRefs = useRef<HTMLDivElement[]>([]);
  const sparkRefs = useRef<HTMLSpanElement[]>([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      cloudRefs.current.forEach((el) => {
        if (!el) return;
        gsap.fromTo(
          el,
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

      sparkRefs.current.forEach((el) => {
        if (!el) return;
        gsap.fromTo(
          el,
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
    }, container);

    return () => ctx.revert();
  }, []);

  const clouds = [
    {
      id: "gold",
      color: "rgba(244,197,74,0.55)",
      top: "10%",
      left: "8%",
      size: "55vh",
    },
    {
      id: "cyan",
      color: "rgba(34,211,238,0.45)",
      top: "55%",
      left: "65%",
      size: "50vh",
    },
    {
      id: "pink",
      color: "rgba(236,72,153,0.4)",
      top: "75%",
      left: "5%",
      size: "45vh",
    },
    {
      id: "indigo",
      color: "rgba(99,102,241,0.4)",
      top: "20%",
      left: "70%",
      size: "40vh",
    },
  ];

  const sparkColors = [
    "rgba(244,197,74,1)",
    "rgba(34,211,238,1)",
    "rgba(99,102,241,1)",
    "rgba(15,23,42,1)",
  ];

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 overflow-hidden z-[5]"
    >
      {clouds.map((c) => (
        <div
          key={c.id}
          ref={(el) => {
            if (el) cloudRefs.current[clouds.indexOf(c)] = el;
          }}
          className="absolute rounded-full"
          style={{
            top: c.top,
            left: c.left,
            width: c.size,
            height: c.size,
            background: `radial-gradient(circle, ${c.color}, transparent 70%)`,
            filter: "blur(80px)",
          }}
        />
      ))}

      {Array.from({ length: 18 }).map((_, i) => {
        const color = sparkColors[i % sparkColors.length];
        const size = i % 3 === 0 ? 5 : 3;
        return (
          <span
            key={`spark-${i}-${color}`}
            ref={(el) => {
              if (el) sparkRefs.current[i] = el;
            }}
            className="absolute rounded-full"
            style={{
              left: `${(i * 53 + 7) % 100}%`,
              bottom: `0%`,
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

// ── InscripcionClientShell ─────────────────────────────────────────────────────

export function InscripcionClientShell() {
  const shellRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const shell = shellRef.current;
    if (!shell) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

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
    }, shell);

    return () => ctx.revert();
  }, []);

  return (
    <div
      ref={shellRef}
      className="relative min-h-svh w-full overflow-y-auto px-4 py-6 sm:px-8"
      style={{
        background:
          "radial-gradient(circle at 20% 20%, #fff8e6 0%, transparent 55%)," +
          "radial-gradient(circle at 80% 30%, #e6f4ff 0%, transparent 55%)," +
          "radial-gradient(circle at 50% 100%, #f3e8ff 0%, transparent 55%)," +
          "linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)",
        color: "#0f172a",
      }}
    >
      <SubtleFormSparks />

      {/* Full-width centered wizard container */}
      <div className="rs-stagger relative z-10 mx-auto w-full max-w-6xl py-4">
        <div
          className="rounded-[1.75rem] p-5 sm:p-8"
          style={{
            background:
              "linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,252,0.92) 100%)",
            border: "1px solid rgba(15,23,42,0.08)",
            boxShadow:
              "0 10px 30px rgba(15,23,42,0.08), 0 2px 6px rgba(15,23,42,0.04)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
          }}
        >
          <InscripcionWizard />
        </div>
      </div>
    </div>
  );
}
