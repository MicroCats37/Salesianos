"use client";

import { AlertCircle, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { usePaquetes } from "@/features/inscripciones/hooks/useInscripcionCatalogs";
import { PaquetesCards } from "./PaquetesCards";
import { PreinscribirCTA } from "./PreinscribirCTA";

/**
 * Static fallback paquetes — shown when the API is unavailable.
 * Kept for backward compatibility and resilience.
 */
const FALLBACK_PAQUETES = [
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

function FallbackCard({ pkg }: { pkg: (typeof FALLBACK_PAQUETES)[number] }) {
  return (
    <article
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
        <p className="mt-2 text-5xl font-black text-[#17214b]">{pkg.price}</p>
        {pkg.id === "regular" && (
          <p className="mt-1 text-sm text-[#626195]">por equipo</p>
        )}
      </div>

      <p className="mb-6 text-sm leading-7 text-[#626195]">{pkg.description}</p>

      <ul className="mb-8 flex flex-col gap-3">
        {pkg.features.map((feature) => (
          <li key={feature} className="flex items-start gap-3 text-sm">
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
            <span className="text-[#17214b]">{feature}</span>
          </li>
        ))}
      </ul>

      {pkg.id === "regular" ? (
        <PreinscribirCTA />
      ) : (
        <div className="mt-auto flex items-center gap-2 rounded-xl border border-[#312e8e]/10 bg-[#f4f6fb] p-3">
          <AlertCircle className="size-4 shrink-0 text-[#626195]" />
          <p className="text-xs text-[#626195]">
            {pkg.price} — Cuota pendiente de definición por el Comité.
          </p>
        </div>
      )}
    </article>
  );
}

/**
 * Landing page Paquetes section.
 *
 * Architecture:
 * - This file (Paquetes.tsx) is a Server Component — fetches data at render time.
 * - PaquetesCards.tsx is a Client Component — handles GSAP scroll animations.
 * - PreinscribirCTA.tsx is a Client Component — auth-aware CTA using useAuthUser().
 *
 * Data flow:
 * 1. Server fetches paquetes from GET /inscripciones/paquetes/
 * 2. Falls back to FALLBACK_PAQUETES if API is unavailable
 * 3. Passes data to PaquetesCards (client) for rendering + animation
 */
export function Paquetes() {
  const { data: paquetes, isLoading } = usePaquetes();
  const featuredPaquetes = paquetes?.filter((paquete) => paquete.esta_activo) ?? null;

  return (
    <>
      {featuredPaquetes && featuredPaquetes.length > 0 ? (
        <PaquetesCards paquetes={featuredPaquetes} />
      ) : (
        <section
          id="paquetes"
          className="flex min-h-screen w-full items-center bg-white py-16 scroll-mt-20 sm:py-20"
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

            <div className="paquete-reveal mt-12 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-2 lg:items-start xl:grid-cols-4">
              {isLoading ? FALLBACK_PAQUETES.slice(0, 4).map((pkg) => (
                <div
                  key={pkg.id}
                  className="h-[32rem] animate-pulse rounded-3xl bg-[#f4f6fb] shadow-xl ring-1 ring-[#312e8e]/10"
                />
              )) : FALLBACK_PAQUETES.map((pkg) => (
                <FallbackCard key={pkg.id} pkg={pkg} />
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
      )}
    </>
  );
}
