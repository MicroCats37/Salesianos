"use client";

import { ListTree } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

/** One section of the page and the anchor that reaches it. */
export interface SeccionIndice {
  id: string;
  titulo: string;
}

export interface IndiceInformacionProps {
  /** The sections of the page. Every anchor must resolve to a real one. */
  secciones: SeccionIndice[];
  className?: string;
}

/**
 * IndiceInformacion - the real anchor navigation of the information page.
 *
 * The index is a `<nav>` with a labelled list, and every link points to a
 * section that EXISTS: an anchor that lands nowhere is a broken promise
 * (`RB-01` PUB-02).
 *
 * Below 768 the index is a disclosure, so the content is not pushed down by
 * a rail that nobody asked for. From 768 it is a sticky rail and the
 * section that is being read is marked with `aria-current`.
 */
export function IndiceInformacion({ secciones, className }: IndiceInformacionProps) {
  const [activo, setActivo] = useState<string | null>(null);

  useEffect(() => {
    if (secciones.length === 0) return;

    const observador = new IntersectionObserver(
      (entradas) => {
        const visible = entradas
          .filter((entrada) => entrada.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);

        if (visible[0]) {
          setActivo(visible[0].target.id);
        }
      },
      { rootMargin: "-96px 0px -60% 0px", threshold: 0 },
    );

    for (const seccion of secciones) {
      const elemento = document.getElementById(seccion.id);
      if (elemento) observador.observe(elemento);
    }

    return () => observador.disconnect();
  }, [secciones]);

  return (
    <nav
      aria-label="Contenido de esta página"
      className={cn(
        "rounded-[var(--radius-lg)] border border-border bg-surface-raised p-4 shadow-[var(--elevation-sm)]",
        className,
      )}
    >
      <details className="group lg:hidden" open>
        <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 text-sm font-semibold text-foreground">
          <ListTree className="size-4 text-primary" aria-hidden="true" />
          En esta página
        </summary>
        <ul className="mt-3 flex flex-col gap-1 border-l border-border pl-3">
          {secciones.map((seccion) => (
            <li key={seccion.id}>
              <a
                href={`#${seccion.id}`}
                aria-current={activo === seccion.id ? "true" : undefined}
                className="block py-2 text-sm text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline"
              >
                {seccion.titulo}
              </a>
            </li>
          ))}
        </ul>
      </details>

      <div className="hidden lg:block">
        <p className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <ListTree className="size-4 text-primary" aria-hidden="true" />
          En esta página
        </p>
        <ul className="mt-3 flex flex-col gap-1 border-l border-border pl-3">
          {secciones.map((seccion) => (
            <li key={seccion.id}>
              <a
                href={`#${seccion.id}`}
                aria-current={activo === seccion.id ? "true" : undefined}
                className={cn(
                  "block py-2 text-sm underline-offset-4 transition-colors hover:underline",
                  activo === seccion.id
                    ? "font-semibold text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {seccion.titulo}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
