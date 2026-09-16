"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { AlertCircle, CreditCard, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";

gsap.registerPlugin(ScrollTrigger);

const PAQUETES = [
  {
    id: "regular",
    label: "Inscripción Regular",
    price: "S/ 1,350",
    description:
      "Acceso completo a todas las disciplinas y categorías disponibles.",
    features: [
      "4 disciplinas: Fulbito, Vóley, Básquet",
      "Categorías Junior, Senior, Máster",
      "Nómina hasta 12 jugadores por equipo",
      "Validación de joueur contra padrón salesiano",
      "Soporte del Comité durante todo el proceso",
    ],
    badge: "PROMOCIÓN 2002",
    highlight: true,
  },
  {
    id: "anticipada",
    label: "Inscripción Anticipada",
    price: "Por definir",
    description: "Tarifa especial para registros tempranos.",
    features: [
      "Mismos beneficios que la inscripción regular",
      "Precio reducido por inscripción anticipada",
      "Cupos limitados por disciplina",
    ],
    badge: "PRONTO",
    highlight: false,
  },
  {
    id: "extemporanea",
    label: "Inscripción Extemporánea",
    price: "Por definir",
    description: "Para registros después de la fecha límite.",
    features: [
      "Mismos beneficios que la inscripción regular",
      "Tarifa diferenciada",
      "Sujeto a disponibilidad de cupos",
    ],
    badge: "PRONTO",
    highlight: false,
  },
];

export function Paquetes() {
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

        <div className="paquete-reveal mt-12 grid gap-8 lg:grid-cols-3 lg:items-start">
          {PAQUETES.map((pkg) => (
            <article
              key={pkg.id}
              className={`paquete-reveal relative flex flex-col rounded-3xl p-8 ${
                pkg.highlight
                  ? "card-elevated bg-white ring-2 ring-[#312e8e]"
                  : "card-elevated bg-white"
              }`}
            >
              {pkg.highlight && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-[#312e8e] px-4 py-1.5 text-xs font-black text-white shadow-lg">
                    <ShieldCheck className="size-3.5" />
                    {pkg.badge}
                  </span>
                </div>
              )}

              <div className="mb-6">
                <p className="text-sm font-bold uppercase tracking-wider text-[#626195]">
                  {pkg.label}
                </p>
                <p className="mt-2 text-5xl font-black text-[#17214b]">
                  {pkg.price}
                </p>
                {pkg.id === "regular" && (
                  <p className="mt-1 text-sm text-[#626195]">por equipo</p>
                )}
              </div>

              <p className="mb-6 text-sm leading-7 text-[#626195]">
                {pkg.description}
              </p>

              <ul className="mb-8 flex flex-col gap-3">
                {pkg.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-sm">
                    <svg
                      className="mt-0.5 size-4 shrink-0 text-[#312e8e]"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2.5}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span className="text-[#17214b]">{feature}</span>
                  </li>
                ))}
              </ul>

              {pkg.id === "regular" ? (
                <div className="mt-auto space-y-3">
                  <Button
                    asChild
                    className="btn-brand-gradient btn-shine w-full justify-center rounded-2xl h-12 text-sm font-black"
                  >
                    <Link href="/register">Preinscribir equipo</Link>
                  </Button>
                  <div className="flex items-start gap-2 rounded-xl border border-[#f4c64e]/40 bg-[#fffbeb] p-3">
                    <CreditCard className="mt-0.5 size-4 shrink-0 text-[#92650a]" />
                    <div>
                      <p className="text-xs font-bold text-[#7a5209]">
                        Módulo de pago en preparación
                      </p>
                      <p className="mt-0.5 text-xs text-[#92650a]/80">
                        Podrás pagar con izipay una vez que tu inscripción sea
                        validada por el Comité.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mt-auto flex items-center gap-2 rounded-xl border border-[#312e8e]/10 bg-[#f4f6fb] p-3">
                  <AlertCircle className="size-4 shrink-0 text-[#626195]" />
                  <p className="text-xs text-[#626195]">
                    {pkg.price} — Cuota pendiente de definición por el Comité.
                  </p>
                </div>
              )}
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
