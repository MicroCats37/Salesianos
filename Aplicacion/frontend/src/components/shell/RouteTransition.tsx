"use client";

import { gsap } from "gsap";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useRef } from "react";
import { useGSAP } from "@/hooks/system/use-gsap";
import { cn } from "@/lib/utils";

/** The transition is longer and more visible: it explains the change. */
const DURACION = 0.46;
const DESPLAZAMIENTO = 28;
const DESPLAZAMIENTO_BLOQUE = 18;
const RETARDO = 0.05;
const ESCALON = 0.07;

/**
 * The last route that was animated.
 *
 * It lives in the module, NOT in a ref of the component, because the
 * container can be REMOUNTED when the layout re-renders: a ref would start
 * again at "first time" and the transition would never play. The module
 * remembers that a route was already shown, so a remount still knows that
 * the route CHANGED.
 */
let ultimaRuta: string | null = null;

export interface RouteTransitionProps {
  children: ReactNode;
  className?: string;
}

/**
 * RouteTransition - the shared transition between routes.
 *
 * It animates THE CONTENT of the route and nothing else: the sidebar, the
 * top bars and the footer stay exactly where they are, because a navigation
 * that moves the chrome reads as a glitch, not as a transition.
 *
 * It works in TWO levels, and each level owns one property so they never
 * fight:
 *
 * - The OUTER box carries the fade of the FIRST paint (CSS). It starts when
 *   the browser paints the server HTML, so there is no flash of content
 *   that appears and disappears, and it survives a browser without JS.
 * - The INNER box carries the GSAP timeline of the ROUTE CHANGE: opacity
 *   and a short vertical displacement, with the blocks of the page arriving
 *   in reading order. It never animates a height, a width or a margin.
 *
 * `prefers-reduced-motion` is honoured with `gsap.matchMedia()`: when the
 * visitor asked for less movement the content is shown immediately, fully
 * visible, with no tween at all.
 */
export function RouteTransition({ children, className }: RouteTransitionProps) {
  const contenedorRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();

  useGSAP(
    () => {
      const contenedor = contenedorRef.current;

      if (!contenedor) return;

      /**
       * A route change is a route that is NOT the one we animated last.
       * The first route of the session is not a change: the CSS fade of the
       * first paint already introduces it.
       */
      const esCambio = ultimaRuta !== null && ultimaRuta !== pathname;
      ultimaRuta = pathname;

      if (!esCambio) return;

      const media = gsap.matchMedia();

      media.add(
        { motionReducido: "(prefers-reduced-motion: reduce)" },
        (contexto) => {
          const condiciones = contexto.conditions as {
            motionReducido?: boolean;
          };
          const bloques = contenedor.querySelectorAll("[data-route-block]");

          if (condiciones.motionReducido) {
            gsap.set(contenedor, { autoAlpha: 1, y: 0, clearProps: "all" });
            gsap.set(bloques, { autoAlpha: 1, y: 0, clearProps: "all" });
            return;
          }

          const linea = gsap.timeline({
            defaults: { ease: "power3.out", overwrite: "auto" },
          });

          linea.fromTo(
            contenedor,
            { autoAlpha: 0, y: DESPLAZAMIENTO },
            {
              autoAlpha: 1,
              y: 0,
              duration: DURACION,
              clearProps: "opacity,visibility,transform",
            },
          );

          if (bloques.length > 0) {
            /**
             * Los bloques suben y se aclaran DESDE un valor alto: el
             * contenedor ya está desvaneciéndose, y dos opacidades a cero
             * multiplicadas dejarían la página en negro un instante de más.
             */
            linea.fromTo(
              bloques,
              { autoAlpha: 0.35, y: DESPLAZAMIENTO_BLOQUE },
              {
                autoAlpha: 1,
                y: 0,
                duration: DURACION - 0.04,
                stagger: ESCALON,
                clearProps: "opacity,visibility,transform",
              },
              RETARDO,
            );
          }
        },
      );

      return () => {
        media.revert();
      };
    },
    { scope: contenedorRef, dependencies: [pathname] },
  );

  return (
    <div
      className={cn(
        "min-w-0 animate-in fade-in-0 duration-500 ease-out",
        className,
      )}
    >
      <div ref={contenedorRef} className="min-w-0">
        {children}
      </div>
    </div>
  );
}
