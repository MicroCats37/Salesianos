"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { PreinscribirCta } from "@/components/event/PreinscribirCta";

export function EventFooter() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;

    const ctx = gsap.context(() => {
      gsap.from(el.querySelectorAll("[data-footer-stagger]"), {
        y: 40,
        opacity: 0,
        duration: 1,
        stagger: 0.1,
        ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 80%", once: true },
      });
    }, el);

    return () => ctx.revert();
  }, []);

  return (
    <footer
      ref={ref}
      className="event-snap relative overflow-hidden py-20 sm:py-28"
      style={{
        background:
          "linear-gradient(180deg, #0c0c1f 0%, #1a1857 50%, #312e8e 100%)",
      }}
    >
      {/* Halo */}
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10 opacity-90"
        style={{
          background:
            "radial-gradient(ellipse at 50% 30%, rgba(236,72,153,0.35) 0%, rgba(99,102,241,0.25) 35%, rgba(34,211,238,0.18) 65%, transparent 80%)",
          filter: "blur(80px)",
        }}
      />

      <div className="relative z-10 mx-auto max-w-4xl px-6 text-center">
        <div
          data-footer-stagger
          className="mx-auto mb-8 flex items-center justify-center gap-4"
        >
          <Link
            href="/"
            aria-label="Ir al inicio"
            className="relative size-20 animate-[badgePulse_3s_ease-in-out_infinite]"
          >
            <div
              className="absolute -inset-2 rounded-full"
              style={{
                background:
                  "conic-gradient(from 0deg, #f4c64e, #ec4899, #6366f1, #22d3ee, #f4c64e)",
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
              <img
                src="/logo-oficial-salesianos-2002.jpeg"
                alt="Logo oficial Salesianos 2002"
                className="h-full w-full object-cover"
              />
            </div>
          </Link>
        </div>

        <p
          data-footer-stagger
          className="text-xs font-black uppercase tracking-[0.4em] text-[#f4c64e]"
        >
          Salesianos FEST · Bodas de Plata
        </p>

        <h2
          data-footer-stagger
          className="mt-4 font-black tracking-tight text-white"
          style={{
            fontFamily: "'Brush Script MT', 'Comic Sans MS', cursive",
            fontSize: "clamp(2.25rem, 5vw, 3.75rem)",
            background:
              "linear-gradient(135deg, #f4c64e 0%, #ec4899 50%, #6366f1 100%)",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            color: "transparent",
            textShadow: "0 0 30px rgba(236,72,153,0.4)",
          }}
        >
          Listos para volver a la cancha?
        </h2>

        <p
          data-footer-stagger
          className="mx-auto mt-5 max-w-xl text-base leading-7 text-white/85 sm:text-lg"
        >
          Preinscribe la nomina de tu promocion y asegurate un lugar en el
          campeonato + fiesta mas grande de la promocion 2002.
        </p>

        <div
          data-footer-stagger
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <PreinscribirCta />
        </div>

        {/* Social media */}
        <div
          data-footer-stagger
          className="mt-12 flex items-center justify-center gap-3"
        >
          <span className="text-xs font-black uppercase tracking-[0.3em] text-white/65">
            Siguenos:
          </span>
          <a
            href="https://www.facebook.com/share/1EgEPXVFU3/?mibextid=wwXIfr"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Facebook"
            className="grid size-11 place-items-center rounded-2xl border border-white/20 bg-white/10 text-white transition-all hover:scale-110 hover:bg-[#1877f2]"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
            </svg>
          </a>
          <a
            href="https://www.instagram.com/salesianos2002bodasdeplata?stkn=MWVwd3FxcXZ0ZzVhNg%3D%3D&utm_source=qr"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Instagram"
            className="grid size-11 place-items-center rounded-2xl border border-white/20 text-white transition-all hover:scale-110"
            style={{
              background:
                "linear-gradient(135deg, #ec4899 0%, #a855f7 50%, #6366f1 100%)",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
            </svg>
          </a>
          <a
            href="https://www.tiktok.com/@salesianos.2002"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="TikTok"
            className="grid size-11 place-items-center rounded-2xl border border-white/20 bg-white/10 text-white transition-all hover:scale-110 hover:bg-black"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.27 6.27 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.77 1.52V6.84a4.83 4.83 0 01-1-.15z" />
            </svg>
          </a>
        </div>

        <p
          data-footer-stagger
          className="mt-10 text-[10px] font-black uppercase tracking-[0.3em] text-white/55"
        >
          Salesianos FEST — Asociacion Okinawense del Peru
        </p>
      </div>
    </footer>
  );
}
