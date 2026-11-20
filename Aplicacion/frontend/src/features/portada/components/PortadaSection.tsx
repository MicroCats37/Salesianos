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
  /**
   * Altura de la sección.
   *
   * `viewport` (por defecto) la hace ocupar al menos una pantalla y la ancla
   * al scroll: la portada avanza sección a sección en vez de dejar el texto
   * disperso. En escritorio la "pantalla" es el espacio REALMENTE disponible
   * (viewport menos el navbar sticky); en móvil la sección fluye a su altura
   * natural, porque una sección de una pantalla en un teléfono deja el texto
   * recortado. `auto` la deja a su altura natural (para el cierre y el pie).
   */
  altura?: "viewport" | "auto";
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
  altura = "viewport",
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
    /*
     * La banda de marca es el índigo PROFUNDO de la identidad, no un bloque
     * de color plano: el degradado institucional (`--brand-deep-blue` →
     * `--brand-deep-night`) es el fondo sobre el que vive la tinta de marca.
     */
    marca: "bg-brand-gradient-deep",
    inverso: "bg-surface-inverse",
  } as const;

  const colorClases = {
    pagina: {
      eyebrow: "text-eyebrow-brand",
      titulo: "text-foreground",
      destacado: "text-info",
      copy: "text-muted-foreground",
    },
    /*
     * La tinta de la banda de marca NO puede depender de `primary-foreground`:
     * ese rol se invierte con el tema y el degradado institucional es OSCURO
     * en los dos temas. Sobre él manda `brand-on-gradient`, que es el mismo
     * contrato en claro y en oscuro.
     */
    marca: {
      eyebrow: "text-brand-cyan",
      titulo: "text-brand-on-gradient",
      destacado: "text-accent",
      copy: "text-brand-on-gradient-muted",
    },
    inverso: {
      eyebrow: "text-brand-cyan/80",
      titulo: "text-surface-inverse-foreground",
      destacado: "text-brand-cyan",
      copy: "text-surface-inverse-foreground/70",
    },
  } as const;

  const color = colorClases[fondo];
  const parrafos = Array.isArray(copy) ? copy : copy ? [copy] : [];

  return (
    <section
      id={id}
      ref={sectionRef}
      className={cn(
        /*
         * El ritmo vertical responde a la ALTURA de la ventana, no sólo a su
         * anchura: en una pantalla baja una sección "de una pantalla" tiene
         * que apretar el aire para que el contenido quepa y el visitante no
         * tenga que desplazarse dentro de ella.
         */
        "scroll-mt-[var(--portada-chrome-height)] py-12 sm:py-16 lg:py-20 [@media(max-height:900px)]:py-8 [@media(max-height:760px)]:py-6",
        altura === "viewport" &&
          "flex snap-start flex-col justify-center lg:portada-altura-disponible",
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
            {/*
              La "firma de oro": la regla de 2px que acompaña al eyebrow de
              sección. Es el gesto reconocible de la marca y marca el
              arranque de cada bloque sin añadir una línea de texto.
            */}
            {eyebrow && (
              <span
                data-portada-stagger
                className="rule-gold mb-3 block h-0.5 w-10 rounded-full"
                aria-hidden="true"
              />
            )}
            {eyebrow && (
              <p
                data-portada-stagger
                className={cn("text-eyebrow-brand", color.eyebrow)}
              >
                {eyebrow}
              </p>
            )}
            {titulo && (
              <h2
                data-portada-stagger
                className={cn(
                  "mt-3 text-3xl font-black uppercase leading-[1.05] tracking-tight sm:text-4xl lg:text-5xl [@media(max-height:900px)]:lg:text-4xl",
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
                  "mt-4 space-y-2 text-sm leading-relaxed sm:mt-5 sm:space-y-3 sm:text-base [@media(max-height:900px)]:mt-3",
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
