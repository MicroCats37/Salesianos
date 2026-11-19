"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Image from "next/image";
import { useEffect, useRef } from "react";
import { PortadaSection } from "@/components/portada/PortadaSection";
import { COPY } from "@/features/portada/copy";

gsap.registerPlugin(ScrollTrigger);

/**
 * Sección "03 / EN FAMILIA".
 *
 * Panel de dos columnas: la zona campestre con la cita sobre el overlay y
 * el detalle de lo que la familia puede hacer entre partido y partido.
 */
export function FamilySection() {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.from("[data-familia-visual]", {
        x: -32,
        opacity: 0,
        duration: 0.9,
        ease: "power3.out",
        immediateRender: false,
        scrollTrigger: {
          trigger: root,
          start: "top 78%",
          once: true,
        },
      });
      gsap.from("[data-familia-item]", {
        y: 24,
        opacity: 0,
        duration: 0.6,
        stagger: 0.1,
        ease: "power3.out",
        immediateRender: false,
        scrollTrigger: {
          trigger: root,
          start: "top 78%",
          once: true,
        },
      });
    }, root);
    return () => ctx.revert();
  }, []);

  const destacado = COPY.familia.titulo.find((linea) =>
    linea.endsWith(COPY.familia.destacado),
  );

  return (
    <PortadaSection
      id="familia"
      eyebrow={COPY.familia.eyebrow}
      titulo={[...COPY.familia.titulo]}
      destacado={destacado}
      copy={COPY.familia.copy}
    >
      <div
        ref={rootRef}
        className="mt-12 grid gap-8 lg:grid-cols-2 lg:items-center lg:gap-12"
      >
        <div
          data-familia-visual
          className="relative overflow-hidden rounded-2xl border border-[#312e8e]/10 shadow-xl shadow-[#312e8e]/10"
        >
          <div className="relative aspect-[4/3] w-full">
            <Image
              src={COPY.familia.imagen}
              alt={COPY.familia.alt}
              fill
              loading="lazy"
              sizes="(max-width: 1024px) 100vw, 50vw"
              className="object-cover"
            />
          </div>
          <div
            className="absolute inset-0 bg-gradient-to-t from-[#17214b]/90 via-[#17214b]/30 to-transparent"
            aria-hidden="true"
          />
          <p className="absolute inset-x-0 bottom-0 p-5 text-sm font-black uppercase leading-snug tracking-wider text-white sm:p-6 sm:text-base">
            {COPY.familia.cita}
          </p>
        </div>

        <div>
          <ol className="space-y-4">
            {COPY.familia.items.map((item, indice) => (
              <li
                key={item}
                data-familia-item
                className="flex items-start gap-4 border-b border-[#312e8e]/10 pb-4 last:border-b-0 last:pb-0"
              >
                <span className="text-xs font-black tracking-[0.2em] text-[#22d3ee]">
                  {String(indice + 1).padStart(2, "0")}
                </span>
                <p className="text-sm leading-relaxed text-[#17214b] sm:text-base">
                  {item}
                </p>
              </li>
            ))}
          </ol>
          <p className="mt-6 text-xs leading-relaxed text-[#626195]">
            {COPY.familia.nota}
          </p>
        </div>
      </div>
    </PortadaSection>
  );
}
