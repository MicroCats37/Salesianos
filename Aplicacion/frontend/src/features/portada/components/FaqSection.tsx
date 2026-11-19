"use client";

import { Plus } from "lucide-react";
import { PortadaSection } from "@/features/portada/components/PortadaSection";
import { COPY } from "@/features/portada/fixtures/copy";

/**
 * Sección de preguntas frecuentes.
 *
 * Usa `<details>` nativo: el navegador resuelve la apertura y el teclado
 * sin necesidad de una librería de acordeón.
 */
export function FaqSection() {
  return (
    <PortadaSection
      id="preguntas"
      eyebrow={COPY.preguntas.eyebrow}
      titulo={[...COPY.preguntas.titulo]}
      destacado={COPY.preguntas.destacado}
    >
      <div className="mt-12 divide-y divide-primary/10 overflow-hidden rounded-3xl bg-surface-raised shadow-sm ring-1 ring-primary/10">
        {COPY.preguntas.faq.map((pregunta) => (
          <details key={pregunta.pregunta} className="group">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-5 text-left sm:px-7">
              <span className="text-sm font-black uppercase tracking-tight text-foreground sm:text-base">
                {pregunta.pregunta}
              </span>
              <span
                aria-hidden="true"
                className="grid size-8 shrink-0 place-items-center rounded-full border border-primary/20 text-primary transition-transform duration-300 group-open:rotate-45"
              >
                <Plus className="size-4" />
              </span>
            </summary>
            <p className="px-5 pb-6 text-sm leading-relaxed text-muted-foreground sm:px-7 sm:pr-14">
              {pregunta.respuesta}
            </p>
          </details>
        ))}
      </div>
    </PortadaSection>
  );
}
