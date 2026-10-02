"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";

interface NeonSmokeProps {
  density?: "low" | "medium" | "high";
}

interface GlowConfig {
  color: string;
  size: number;
  top: string;
  left: string;
  duration: number;
  delay: number;
  blur: number;
}

export function NeonSmoke({ density = "medium" }: NeonSmokeProps) {
  const cloudRefs = useRef<HTMLDivElement[]>([]);
  const sparkRefs = useRef<HTMLSpanElement[]>([]);

  useEffect(() => {
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
            yPercent: gsap.utils.random(-15, 15),
            scale: 0.7,
            opacity: 0,
          },
          {
            xPercent: gsap.utils.random(-30, 30),
            yPercent: gsap.utils.random(-15, 15),
            scale: gsap.utils.random(1.0, 1.5),
            opacity: gsap.utils.random(0.75, 1),
            duration: gsap.utils.random(6, 12),
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
          { y: 30, opacity: 0, scale: gsap.utils.random(0.3, 0.7) },
          {
            y: -360,
            opacity: gsap.utils.random(0.5, 1),
            scale: gsap.utils.random(0.7, 1.4),
            duration: gsap.utils.random(3, 6),
            ease: "sine.out",
            repeat: -1,
            delay: gsap.utils.random(0, 5),
          },
        );
      });
    });

    return () => ctx.revert();
  }, []);

  const glows: GlowConfig[] =
    density === "high"
      ? [
          {
            color: "#ec4899",
            size: 720,
            top: "-5%",
            left: "-10%",
            duration: 9,
            delay: 0,
            blur: 180,
          },
          {
            color: "#6366f1",
            size: 760,
            top: "30%",
            left: "55%",
            duration: 11,
            delay: 1,
            blur: 200,
          },
          {
            color: "#22d3ee",
            size: 640,
            top: "65%",
            left: "-5%",
            duration: 10,
            delay: 2,
            blur: 190,
          },
          {
            color: "#a855f7",
            size: 580,
            top: "80%",
            left: "60%",
            duration: 12,
            delay: 3,
            blur: 190,
          },
        ]
      : density === "low"
        ? [
            {
              color: "#ec4899",
              size: 520,
              top: "10%",
              left: "-5%",
              duration: 9,
              delay: 0,
              blur: 160,
            },
            {
              color: "#22d3ee",
              size: 520,
              top: "65%",
              left: "55%",
              duration: 11,
              delay: 2,
              blur: 170,
            },
          ]
        : [
            {
              color: "#ec4899",
              size: 620,
              top: "5%",
              left: "-5%",
              duration: 9,
              delay: 0,
              blur: 160,
            },
            {
              color: "#6366f1",
              size: 680,
              top: "45%",
              left: "50%",
              duration: 11,
              delay: 1,
              blur: 180,
            },
            {
              color: "#22d3ee",
              size: 580,
              top: "72%",
              left: "8%",
              duration: 10,
              delay: 2,
              blur: 170,
            },
          ];

  const sparks = Array.from({ length: density === "high" ? 32 : 18 }).map(
    (_, i) => {
      const palette = [
        "#ec4899",
        "#22d3ee",
        "#a855f7",
        "#f4c64e",
        "#ffffff",
      ];
      return {
        color: palette[i % palette.length],
        left: `${(i * 53 + 11) % 100}%`,
        size: i % 3 === 0 ? 5 : 3,
      };
    },
  );

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 overflow-hidden"
    >
      {/* Neon glows — stacked box-shadows for real neon look */}
      {glows.map((g, i) => (
        <div
          key={i}
          ref={(el) => {
            if (el) cloudRefs.current[i] = el;
          }}
          className="absolute rounded-full"
          style={{
            top: g.top,
            left: g.left,
            width: g.size,
            height: g.size,
            background: g.color,
            filter: `blur(${g.blur}px)`,
            boxShadow: `
              0 0 ${g.blur / 2}px ${g.color},
              0 0 ${g.blur}px ${g.color},
              0 0 ${g.blur * 1.5}px ${g.color}
            `,
            mixBlendMode: "screen",
            opacity: 0,
          }}
        />
      ))}

      {/* Rising neon sparks */}
      {sparks.map((s, i) => (
        <span
          key={i}
          ref={(el) => {
            if (el) sparkRefs.current[i] = el;
          }}
          className="absolute rounded-full"
          style={{
            left: s.left,
            bottom: "0%",
            width: s.size,
            height: s.size,
            background: s.color,
            boxShadow: `
              0 0 ${s.size * 3}px ${s.color},
              0 0 ${s.size * 6}px ${s.color}
            `,
          }}
        />
      ))}
    </div>
  );
}
