"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { RegisterForm } from "@/features/auth/components";
import { AuthShell } from "@/features/auth/components/AuthShell";
import { AuthGlassCard } from "@/features/auth/components/AuthGlassCard";

// ── SubtleFormSparks (mirror of login) ─────────────────────────────────────────

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
            opacity: gsap.utils.random(0.35, 0.65),
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
            opacity: gsap.utils.random(0.4, 0.95),
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
    { color: "rgba(244,197,74,0.85)", top: "10%", left: "8%", size: "55vh" },
    { color: "rgba(34,211,238,0.85)", top: "55%", left: "65%", size: "50vh" },
    { color: "rgba(236,72,153,0.85)", top: "75%", left: "5%", size: "45vh" },
    { color: "rgba(99,102,241,0.85)", top: "20%", left: "70%", size: "40vh" },
  ];

  const sparkColors = [
    "rgba(244,197,74,1)",
    "rgba(34,211,238,1)",
    "rgba(236,72,153,1)",
    "rgba(255,255,255,1)",
  ];

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 overflow-hidden z-[5]"
    >
      {clouds.map((c, i) => (
        <div
          key={i}
          ref={(el) => {
            if (el) cloudRefs.current[i] = el;
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
            key={i}
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

// ── RegisterClientShell ────────────────────────────────────────────────────────

export function RegisterClientShell() {
  return (
    <AuthShell
      variant="register"
      invertColumns
      form={
        <div className="register-form-shell relative">
          <SubtleFormSparks />
          <AuthGlassCard>
            <RegisterForm />
          </AuthGlassCard>
        </div>
      }
    />
  );
}
