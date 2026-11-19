"use client";

import { ArrowRight } from "lucide-react";
import { PortadaSection } from "@/components/portada/PortadaSection";
import { ENLACES } from "@/features/portada/config/festival";
import { COPY } from "@/features/portada/copy";

/**
 * Los tres pasos para llegar al festival.
 *
 * Cierra el bloque de paquetes y da el siguiente paso concreto: entrar a la
 * plataforma oficial y registrar al equipo.
 */
export function RegistrationSteps() {
  return (
    <PortadaSection fondo="marca">
      <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:gap-16">
        <div>
          <h2 className="text-3xl font-black uppercase leading-[1.05] tracking-tight text-white sm:text-4xl lg:text-5xl">
            {COPY.pasosInscripcion.titulo.map((linea, index) => (
              <span key={linea}>
                {index > 0 && <br />}
                {linea}
              </span>
            ))}
          </h2>
          <a
            href={ENLACES.registro}
            className="btn-brand-gradient btn-shine mt-8 inline-flex h-12 items-center justify-center gap-2 rounded-full px-6 text-xs font-black uppercase tracking-wider"
          >
            CREAR MI INSCRIPCIÓN
            <ArrowRight className="size-4" aria-hidden="true" />
          </a>
        </div>

        <ol className="grid gap-4 sm:grid-cols-3">
          {COPY.pasosInscripcion.pasos.map((paso) => (
            <li
              key={paso.numero}
              className="rounded-2xl border border-white/15 bg-white/10 p-5 backdrop-blur-sm"
            >
              <span className="text-2xl font-black text-sky-300">
                {paso.numero}
              </span>
              <p className="mt-3 text-sm font-semibold leading-snug text-white">
                {paso.texto}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </PortadaSection>
  );
}
