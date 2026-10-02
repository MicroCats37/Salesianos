"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";

interface LightRaysProps {
  palette?: string[];
  count?: number;
}

export function LightRays({
  palette = ["#22d3ee", "#6366f1", "#ec4899", "#f4c64e", "#0ea5e9"],
  count = 6,
}: LightRaysProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rayRefs = useRef<HTMLDivElement[]>([]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const reduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduced) return;

    const ctx = gsap.context(() => {
      rayRefs.current.forEach((el) => {
        if (!el) return;
        gsap.fromTo(
          el,
          { opacity: 0.25, scaleY: 0.9 },
          {
            opacity: gsap.utils.random(0.55, 0.95),
            scaleY: gsap.utils.random(1.0, 1.3),
            duration: gsap.utils.random(3, 6),
            ease: "sine.inOut",
            repeat: -1,
            yoyo: true,
            delay: gsap.utils.random(0, 3),
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
      className="pointer-events-none absolute inset-0 overflow-hidden"
    >
      {[
        { top: "-10%", left: "10%", rotate: 18, length: "70vh", width: "120px", color: palette[0] },
        { top: "5%", left: "55%", rotate: -12, length: "60vh", width: "90px", color: palette[1] },
        { top: "55%", left: "20%", rotate: 24, length: "65vh", width: "110px", color: palette[2] },
        { top: "65%", left: "60%", rotate: -18, length: "70vh", width: "100px", color: palette[3] },
        { top: "25%", left: "5%", rotate: 14, length: "55vh", width: "80px", color: palette[4] },
        { top: "40%", left: "75%", rotate: -22, length: "60vh", width: "95px", color: palette[2] },
      ].slice(0, count).map((r, i) => (
        <div
          key={i}
          ref={(el) => {
            if (el) rayRefs.current[i] = el;
          }}
          className="absolute origin-top"
          style={{
            top: r.top,
            left: r.left,
            width: r.width,
            height: r.length,
            transform: `rotate(${r.rotate}deg)`,
            background: `linear-gradient(180deg, ${r.color} 0%, ${r.color}80 35%, ${r.color}20 70%, transparent 100%)`,
            filter: "blur(40px)",
            mixBlendMode: "screen",
            borderRadius: "999px",
            opacity: 0,
          }}
        />
      ))}

      <div
        aria-hidden="true"
        className="absolute -top-40 left-1/2 -z-10 h-[60vh] w-[60vh] -translate-x-1/2 rounded-full"
        style={{
          background:
            "radial-gradient(circle, rgba(99,102,241,0.45) 0%, rgba(34,211,238,0.18) 35%, transparent 70%)",
          filter: "blur(60px)",
          mixBlendMode: "screen",
        }}
      />
    </div>
  );
}
