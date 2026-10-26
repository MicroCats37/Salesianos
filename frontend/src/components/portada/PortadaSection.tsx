"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { type ReactNode, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

gsap.registerPlugin(ScrollTrigger);

export interface PortadaSectionProps {
  /** Ancla de la sección (el header es sticky de 74px). */
  id?: string;
  /** Etiqueta corta arriba del título: "01 / LA EXPERIENCIA". */
  eyebrow?: string;
  /** Título en líneas. La frase `destacado` se pinta con el color de acento. */
  titulo?: string[];
  destacado?: string;
  /** Copy de apoyo: un párrafo o varios. */
  copy?: string | string[];
  children?: ReactNode;
  className?: string;
  /** Fondo de la sección. */
  fondo?: "pagina" | "marca" | "inverso";
  /** Clase extra del contenedor interno. */
  contenidoClassName?: string;
}

/**
 * Cáscara común de las secciones de la portada.
 *
 * Concentra el encabezado (eyebrow + titular + copy), el contenedor, el
 * ritmo vertical y el patrón de animación, para que todas las secciones
 * compartan la misma voz visual.
 */
export function PortadaSection({
  id,
  eyebrow,
  titulo,
  destacado,
  copy,
  children,
  className,
  fondo = "pagina",
  contenidoClassName,
}: PortadaSectionProps) {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const container = sectionRef.current;
    if (!container) return;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      const objetivos = container.querySelectorAll("[data-portada-stagger]");
      if (objetivos.length === 0) return;

      // `immediateRender: false` + `fromTo`: el contenido NUNCA queda
      // invisible. Con `gsap.from` el estado inicial (opacity 0) se aplica al
      // DOM y, si el trigger no dispara, la sección se queda en blanco.
      gsap.fromTo(
        objetivos,
        { y: 28, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.7,
          stagger: 0.1,
          ease: "power3.out",
          immediateRender: false,
          scrollTrigger: {
            trigger: container,
            start: "top 78%",
            once: true,
          },
        },
      );
    }, container);
    return () => ctx.revert();
  }, []);

  const fondoClases = {
    pagina: "surface-page-gradient",
    marca: "bg-[#312e8e]",
    inverso: "bg-[#0b1f4d]",
  } as const;

  const colorClases = {
    pagina: {
      eyebrow: "text-eyebrow-brand",
      titulo: "text-[#17214b]",
      destacado: "text-[#1557b8]",
      copy: "text-[#626195]",
    },
    marca: {
      eyebrow: "text-sky-300",
      titulo: "text-white",
      destacado: "text-[#7dd3fc]",
      copy: "text-white/75",
    },
    inverso: {
      eyebrow: "text-sky-300/80",
      titulo: "text-white",
      destacado: "text-[#7dd3fc]",
      copy: "text-white/70",
    },
  } as const;

  const color = colorClases[fondo];
  const parrafos = Array.isArray(copy) ? copy : copy ? [copy] : [];

  return (
    <section
      id={id}
      ref={sectionRef}
      className={cn(
        "scroll-mt-20 py-16 sm:py-20 lg:py-24",
        fondoClases[fondo],
        className,
      )}
    >
      <div
        className={cn(
          "mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8",
          contenidoClassName,
        )}
      >
        {(eyebrow || titulo || parrafos.length > 0) && (
          <header className="max-w-3xl">
            {eyebrow && (
              <p
                data-portada-stagger
                className={cn(
                  "text-[10px] font-black uppercase tracking-[0.3em]",
                  color.eyebrow,
                )}
              >
                {eyebrow}
              </p>
            )}
            {titulo && (
              <h2
                data-portada-stagger
                className={cn(
                  "mt-3 text-3xl font-black uppercase leading-[1.05] tracking-tight sm:text-4xl lg:text-5xl",
                  color.titulo,
                )}
              >
                {titulo.map((linea, index) => {
                  const esDestacada = Boolean(destacado) && linea === destacado;
                  return (
                    <span key={linea}>
                      {index > 0 && <br />}
                      {esDestacada ? (
                        <em className={cn("not-italic", color.destacado)}>
                          {linea}
                        </em>
                      ) : (
                        linea
                      )}
                    </span>
                  );
                })}
              </h2>
            )}
            {parrafos.length > 0 && (
              <div
                data-portada-stagger
                className={cn(
                  "mt-5 space-y-3 text-sm leading-relaxed sm:text-base",
                  color.copy,
                )}
              >
                {parrafos.map((parrafo) => (
                  <p key={parrafo}>{parrafo}</p>
                ))}
              </div>
            )}
          </header>
        )}
        {children}
      </div>
    </section>
  );
}
