"use client";

import { gsap } from "gsap";
import { type ReactNode, useEffect } from "react";
import { BrandMark } from "@/components/brand/BrandMark";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import {
  AuthVisualPanel,
  EVENTO_FEST,
} from "@/features/auth/components/AuthVisualPanel";

export type AuthVariant = "login" | "register";

export interface AuthShellProps {
  variant: AuthVariant;
  /** Form column component shown on the opposite side of the carousel. */
  form: ReactNode;
  /** When true, layout is inverted (form left, carousel right). Default keeps carousel left. */
  invertColumns?: boolean;
}

/**
 * AuthShell — la ENVOLVENTE del acceso.
 *
 * Dos columnas en escritorio: la banda de marca y el formulario. En móvil la
 * banda se colapsa en una cabecera de marca sobre el formulario, para que la
 * persona sepa en qué sitio está sin que la fotografía le robe el foco a la
 * tarea.
 *
 * El reveal es UN momento orquestado (pauta §8) y se apaga por completo con
 * `prefers-reduced-motion`.
 */
export function AuthShell({
  variant,
  form,
  invertColumns = false,
}: AuthShellProps) {
  const formOrder = invertColumns ? "lg:order-1" : "lg:order-2";
  const visualOrder = invertColumns ? "lg:order-2" : "lg:order-1";

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        defaults: { ease: "power3.out" },
      });
      tl.fromTo(
        ".auth-shell-visual",
        { x: invertColumns ? 24 : -24, opacity: 0 },
        { x: 0, opacity: 1, duration: 0.7 },
      ).fromTo(
        ".auth-shell-card",
        { x: invertColumns ? -24 : 24, opacity: 0, filter: "blur(6px)" },
        { x: 0, opacity: 1, filter: "blur(0px)", duration: 0.6 },
        "-=0.4",
      );
    });
    return () => ctx.revert();
  }, [invertColumns, variant]);

  return (
    <div className="flex min-h-dvh w-full flex-col overflow-hidden lg:flex-row lg:min-h-svh">
      <div
        className={`relative hidden min-h-svh w-full overflow-hidden lg:block lg:w-1/2 ${visualOrder}`}
      >
        <div className="auth-shell-visual h-full w-full">
          <AuthVisualPanel variant={variant} />
        </div>
      </div>

      <div
        className={`relative flex min-h-dvh w-full items-center justify-center overflow-y-auto bg-brand-gradient-deep px-4 py-8 text-surface-inverse-foreground sm:px-8 lg:min-h-svh lg:w-1/2 lg:px-10 ${formOrder}`}
      >
        {/*
          El acceso no tiene barra superior, pero el tema sigue siendo una
          decisión de la persona: el control vive arriba a la derecha, sobre
          la banda de marca, con la tinta del gradiente.
        */}
        <div className="absolute right-3 top-3 z-20 sm:right-5 sm:top-5">
          <ThemeToggle className="text-brand-on-gradient hover:bg-brand-on-gradient-soft hover:text-brand-on-gradient" />
        </div>

        <div className="auth-shell-card relative z-10 w-full max-w-[480px] py-4">
          {/*
            Debajo de 1024 el panel de marca se colapsa en una CABECERA: el
            formulario sigue mandando, pero la identidad no se pierde.

            El wordmark es la variante para fondo oscuro (`brand.png`, blanco y
            azul): la marina (`brand2.png`) se pierde sobre el gradiente
            profundo. Y la fecha y el lugar son los del propio panel de
            marca, no una segunda version de ese dato.
          */}
          <div className="mb-6 flex flex-col items-center gap-2.5 lg:hidden">
            <BrandMark size={30} wordmark="brand" />
            <span className="text-eyebrow-brand text-accent">
              {EVENTO_FEST.date} · {EVENTO_FEST.place}
            </span>
          </div>
          {form}
        </div>
      </div>
    </div>
  );
}
