"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useEffect, useRef } from "react";
import { PaqueteComercialCard } from "@/components/paquetes/PaqueteComercialCard";
import { PreventaBanner } from "@/components/paquetes/PreventaBanner";
import type { Paquete } from "@/features/landing/paquetes.service";
import { PreinscribirCTA } from "./PreinscribirCTA";

gsap.registerPlugin(ScrollTrigger);

interface PaquetesCardsProps {
  paquetes: Paquete[];
}

interface PaqueteSectionProps {
  id: string;
  paquetes: Paquete[];
  variant: "PACK" | "DISCIPLINA";
}

function PaqueteSection({ id, paquetes, variant }: PaqueteSectionProps) {
  const sectionRef = useRef<HTMLElement>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: re-init the reveal when the packages arrive — the section mounts empty.
  useEffect(() => {
    const container = sectionRef.current;
    if (!container) return;

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".paquete-reveal",
        { y: 50, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          stagger: 0.12,
          ease: "power3.out",
          scrollTrigger: {
            trigger: container,
            start: "top 75%",
            once: true,
          },
        },
      );
    }, container);
    return () => ctx.revert();
  }, [paquetes]);

  if (paquetes.length === 0) return null;

  return (
    <section
      id={id}
      ref={sectionRef}
      className="relative scroll-mt-20 bg-[#eef4fb]"
    >
      {/* The banner is a full-bleed backdrop: it must never depend on the
          scroll reveal, otherwise it can stay invisible when the trigger
          does not fire. */}
      <PreventaBanner
        titulo="PREVENTA POR"
        palabraDestacada={variant === "PACK" ? "PACKS" : "DISCIPLINA"}
        variant={variant === "PACK" ? "PACKS" : "DISCIPLINA"}
      />

      <div className="relative z-30 mx-auto -mt-12 max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 items-stretch gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {paquetes.map((paquete) => (
            <div key={paquete.id} className="paquete-reveal h-full">
              <PaqueteComercialCard
                paquete={paquete}
                variant={variant}
                footer={<PreinscribirCTA />}
              />
            </div>
          ))}
        </div>
      </div>

      <div className="h-16" aria-hidden="true" />
    </section>
  );
}

export function PaquetesCards({ paquetes }: PaquetesCardsProps) {
  const packs = paquetes.filter((paquete) => paquete.tipo === "PACK");
  const disciplinas = paquetes.filter(
    (paquete) => paquete.tipo === "DISCIPLINA",
  );

  return (
    <section id="paquetes" className="bg-white">
      <PaqueteSection id="paquetes-packs" paquetes={packs} variant="PACK" />
      <PaqueteSection
        id="paquetes-disciplinas"
        paquetes={disciplinas}
        variant="DISCIPLINA"
      />

      <div className="bg-white px-4 pb-16 text-center text-sm text-[#626195] sm:pb-20">
        ¿Tienes dudas sobre el paquete o necesitas una cotización para múltiples
        equipos?{" "}
        <a
          href="#reglamento"
          className="font-bold text-[#312e8e] hover:underline"
        >
          Consulta las condiciones de preinscripción
        </a>
        .
      </div>
    </section>
  );
}
