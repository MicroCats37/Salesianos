"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useEffect, useRef } from "react";

import type { Paquete } from "@/features/landing/paquetes.service";
import { PreinscribirCTA } from "./PreinscribirCTA";

gsap.registerPlugin(ScrollTrigger);

interface PaquetesCardsProps {
  paquetes: Paquete[];
}

function ModoBadge({ modo }: { modo: string }) {
  const isElegible = modo === "ELEGIBLE";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-black uppercase tracking-wider ${
        isElegible
          ? "bg-[#f4c64e] text-[#17214b]"
          : "bg-[#312e8e]/10 text-[#312e8e]"
      }`}
    >
      {modo === "FIJO"
        ? "FIJO"
        : modo === "ELEGIBLE"
          ? "ELEGIBLE"
          : modo}
    </span>
  );
}

export function PaquetesCards({ paquetes }: PaquetesCardsProps) {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!sectionRef.current) return;

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
            trigger: sectionRef.current,
            start: "top 75%",
            once: true,
          },
        },
      );
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  return (
    <section
      id="paquetes"
      ref={sectionRef}
      className="bg-white py-20 scroll-mt-20 sm:py-24"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="paquete-reveal mx-auto max-w-3xl text-center">
          <p className="text-sm font-black uppercase tracking-[0.2em] text-[#312e8e]/70">
            Inversión
          </p>
          <h2 className="mt-4 text-4xl font-black tracking-tight text-[#17214b] sm:text-5xl">
            Paquetes de preinscripción
          </h2>
          <p className="mt-5 text-lg leading-8 text-[#626195]">
            El paquete referencial para la inscripción de un equipo en las
            Olimpiadas Deportivas Salesianas. Incluye todas las disciplinas,
            categorías y soporte del Comité.
          </p>
        </div>

        <div className="paquete-reveal mt-12 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-2 lg:items-start xl:grid-cols-4 2xl:grid-cols-4">
          {paquetes.map((pkg) => (
            <article
              key={pkg.id}
              className="paquete-reveal relative flex flex-col rounded-3xl bg-white p-8 shadow-xl ring-1 ring-[#312e8e]/10"
            >
              {/* Gold ribbon with package name */}
              <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#f4c64e] px-4 py-1.5 text-xs font-black text-[#17214b] shadow-lg">
                  <svg
                    className="size-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2.5}
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
                    />
                  </svg>
                  {pkg.nombre}
                </span>
              </div>

              <div className="mb-6 mt-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-bold uppercase tracking-wider text-[#626195]">
                    {pkg.nombre}
                  </p>
                  <ModoBadge modo={pkg.modo_disciplinas} />
                </div>
                <p className="mt-2 text-4xl font-black text-[#17214b]">
                  {pkg.precio_promocional !== null &&
                  pkg.precio_promocional > 0
                    ? `S/ ${pkg.precio_promocional.toLocaleString("es-PE")}`
                    : `S/ ${pkg.precio_regular.toLocaleString("es-PE")}`}
                </p>
                {pkg.precio_promocional !== null &&
                  pkg.precio_promocional > 0 && (
                    <p className="mt-1 text-sm text-[#626195] line-through">
                      S/ {pkg.precio_regular.toLocaleString("es-PE")} regular
                    </p>
                  )}
                <p className="mt-1 text-sm text-[#626195]">por equipo</p>
              </div>

              {pkg.descripcion && (
                <p className="mb-6 text-sm leading-7 text-[#626195]">
                  {pkg.descripcion}
                </p>
              )}

              <ul className="mb-8 flex flex-col gap-3">
                <li className="flex items-start gap-3 text-sm">
                  <svg
                    className="mt-0.5 size-4 shrink-0 text-[#312e8e]"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2.5}
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span className="text-[#17214b]">
                    Hasta{" "}
                    <strong>
                      {pkg.cantidad_maxima_participantes} jugadores
                    </strong>{" "}
                    por equipo
                  </span>
                </li>

                {pkg.modo_disciplinas === "ELEGIBLE" &&
                  pkg.cantidad_disciplinas_requeridas !== null && (
                    <li className="flex items-start gap-3 text-sm">
                      <svg
                        className="mt-0.5 size-4 shrink-0 text-[#312e8e]"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2.5}
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <span className="text-[#17214b]">
                        Selecciona{" "}
                        <strong>
                          {pkg.cantidad_disciplinas_requeridas} disciplina
                          {pkg.cantidad_disciplinas_requeridas !== 1
                            ? "s"
                            : ""}
                        </strong>{" "}
                        de la oferta disponible
                      </span>
                    </li>
                  )}

                <li className="flex items-start gap-3 text-sm">
                  <svg
                    className="mt-0.5 size-4 shrink-0 text-[#312e8e]"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2.5}
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span className="text-[#17214b]">
                    Validación contra padrón salesiano
                  </span>
                </li>

                <li className="flex items-start gap-3 text-sm">
                  <svg
                    className="mt-0.5 size-4 shrink-0 text-[#312e8e]"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2.5}
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span className="text-[#17214b]">
                    Soporte del Comité durante todo el proceso
                  </span>
                </li>
              </ul>

              <PreinscribirCTA />
            </article>
          ))}
        </div>

        <p className="mt-10 text-center text-sm text-[#626195]">
          ¿Tienes dudas sobre el paquete o necesitas una cotización para
          múltiples equipos?{" "}
          <a
            href="#reglamento"
            className="font-bold text-[#312e8e] hover:underline"
          >
            Consulta las condiciones de preinscripción
          </a>
          .
        </p>
      </div>
    </section>
  );
}
