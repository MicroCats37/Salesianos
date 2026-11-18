"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { FestBrandHeader } from "@/components/branding/FestBrandHeader";
import { PreinscribirCta } from "@/components/event/PreinscribirCta";

export function FestivalBanner() {
  const ref = useRef<HTMLElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const layerRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [imgIdx, setImgIdx] = useState(0);

  const bannerImages = [
    "/images/fulbito-varones.webp",
    "/images/voley-mixto.webp",
    "/images/basket-varones.webp",
  ];

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;

    const ctx = gsap.context(() => {
      gsap.from(el.querySelectorAll("[data-banner-stagger]"), {
        y: 60,
        opacity: 0,
        duration: 1.1,
        stagger: 0.12,
        ease: "power4.out",
      });

      const title = titleRef.current;
      if (title) {
        const chars = title.querySelectorAll("[data-char]");
        gsap.fromTo(
          chars,
          { y: 80, opacity: 0, rotateX: -60, filter: "blur(8px)" },
          {
            y: 0,
            opacity: 1,
            rotateX: 0,
            filter: "blur(0px)",
            duration: 1.2,
            stagger: 0.04,
            ease: "power4.out",
            delay: 0.3,
          },
        );
      }
    }, el);

    return () => ctx.revert();
  }, []);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return;

    const interval = setInterval(() => {
      const next = (imgIdx + 1) % bannerImages.length;
      const out = layerRefs.current[imgIdx];
      const into = layerRefs.current[next];
      if (!out || !into) {
        setImgIdx(next);
        return;
      }

      gsap.set(into, { opacity: 0, scale: 1.04, filter: "blur(10px)" });
      gsap.to(out, { opacity: 0, duration: 1.1, ease: "power2.inOut" });
      gsap.to(into, {
        opacity: 1,
        scale: 1,
        filter: "blur(0px)",
        duration: 1.1,
        ease: "power2.inOut",
        onStart: () => setImgIdx(next),
      });
    }, 5500);

    return () => clearInterval(interval);
  }, [imgIdx, bannerImages.length]);

  return (
    <section
      ref={ref}
      className="event-snap relative flex min-h-svh w-full items-center justify-center overflow-hidden"
    >
      {/* Background carousel */}
      <div className="absolute inset-0 -z-10">
        {bannerImages.map((src, i) => (
          <div
            key={src}
            ref={(el) => {
              layerRefs.current[i] = el;
            }}
            className="absolute inset-0"
            style={{
              opacity: i === 0 ? 1 : 0,
              transition: "opacity 1.1s ease-in-out",
            }}
          >
            <Image
              src={src}
              alt=""
              fill
              className="object-cover"
              priority={i === 0}
              sizes="100vw"
            />
          </div>
        ))}
      </div>

      {/* Dark overlay so text is readable, color kept minimal */}
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10"
        style={{
          background:
            "linear-gradient(180deg, rgba(7,8,28,0.62) 0%, rgba(26,24,87,0.55) 45%, rgba(12,12,31,0.70) 100%)",
        }}
      />

      <div className="relative z-10 mx-auto flex max-w-6xl flex-col items-center px-6 py-16 text-center">
        {/* Logo + brand mark (single compositional unit) */}
        <div
          data-banner-stagger
          className="relative mb-10 flex flex-col items-center gap-4"
        >
          <Link href="/" aria-label="Ir al inicio" className="relative grid place-items-center">
            <div
              className="relative h-32 w-32 overflow-hidden rounded-full border-[5px] border-white/80 shadow-2xl sm:h-40 sm:w-40"
              style={{
                background:
                  "linear-gradient(135deg, #1a1857 0%, #312e8e 100%)",
              }}
            >
              <img
                src="/logo-oficial-salesianos-2002.jpeg"
                alt="Logo oficial Salesianos 2002 - Bodas de Plata"
                className="h-full w-full object-cover"
              />
            </div>
          </Link>

        {/* Brand mark eyebrow (eyebrow only — main h1 below) */}
        <p
          data-banner-stagger
          className="text-[10px] font-black uppercase tracking-[0.5em] text-[#f4c64e] sm:text-xs"
        >
          Promocion 2002 · Bodas de Plata
        </p>
        </div>

        {/* Hero brand mark — single source of truth, matches login/registro/wizard */}
        <div data-banner-stagger className="mt-6">
          <FestBrandHeader showLogo={false} size="lg" wordmark="brand" />
        </div>

        {/* Sub */}
        <p
          data-banner-stagger
          className="mt-6 max-w-2xl text-base leading-7 text-white/85 sm:text-lg"
        >
          La reunion mas grande de la promocion 2002. Campeonato + fiesta en un
          solo lugar. 21 de noviembre, Lima.
        </p>

        {/* Date pill */}
        <div
          data-banner-stagger
          className="mt-8 flex flex-wrap items-center justify-center gap-3"
        >
          <span className="rounded-full border border-white/30 bg-white/10 px-5 py-2 text-xs font-black uppercase tracking-widest text-white backdrop-blur-sm">
            Campeonato 9:00 a.m.
          </span>
          <span className="rounded-full border border-[#f4c64e]/50 bg-[#f4c64e]/15 px-5 py-2 text-xs font-black uppercase tracking-widest text-[#f4c64e] backdrop-blur-sm">
            Fiesta 6:00 p.m. — 3:00 a.m.
          </span>
        </div>

        {/* CTA — auth-aware: hidden "Conoce el festival" stays as anchor; the
            Preinscribir pair is rendered by PreinscribirCta. */}
        <div
          data-banner-stagger
          className="mt-10 flex flex-col items-center gap-4"
        >
          <a
            href="/informacion"
            className="rounded-full bg-gradient-to-r from-[#1557b8] via-[#312e8e] to-[#1f2357] px-10 py-4 text-sm font-black uppercase tracking-widest text-white shadow-2xl shadow-[#312e8e]/30 transition-transform hover:scale-105"
          >
            Conoce el festival
          </a>
          <PreinscribirCta />
        </div>
      </div>
    </section>
  );
}
