"use client";

import { ArrowRight } from "lucide-react";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { COPY } from "@/features/portada/fixtures/copy";
import { ENLACES } from "@/features/portada/fixtures/festival";

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
          <h2 className="text-3xl font-black uppercase leading-[1.05] tracking-tight text-brand-on-gradient sm:text-4xl lg:text-5xl">
            {COPY.pasosInscripcion.titulo.map((linea, index) => (
              <span key={linea}>
                {index > 0 && <br />}
                {linea}
              </span>
            ))}
          </h2>
          <a
            href={ENLACES.registro}
            className="btn-shine mt-8 inline-flex h-12 items-center justify-center gap-2 rounded-full bg-accent px-6 text-xs font-black uppercase tracking-wider text-accent-foreground shadow-glow-brand transition-colors hover:bg-accent-muted"
          >
            CREAR MI INSCRIPCIÓN
            <ArrowRight className="size-4" aria-hidden="true" />
          </a>
        </div>

        <ol className="grid gap-4 sm:grid-cols-3">
          {COPY.pasosInscripcion.pasos.map((paso) => (
            <li
              key={paso.numero}
              className="rounded-2xl border border-brand-on-gradient-border bg-brand-on-gradient-soft p-5 backdrop-blur-sm"
            >
              <span className="text-2xl font-black text-brand-cyan">
                {paso.numero}
              </span>
              <p className="mt-3 text-sm font-semibold leading-snug text-brand-on-gradient">
                {paso.texto}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </PortadaSection>
  );
}
