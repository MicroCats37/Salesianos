"use client";

import { useEffect, type ReactNode } from "react";
import { gsap } from "gsap";
import { AuthVisualPanel } from "@/features/auth/components/AuthVisualPanel";
import { BrandMark } from "@/components/brand/BrandMark";
import { ThemeToggle } from "@/components/shell/ThemeToggle";

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
 * banda se oculta, pero la marca NO desaparece: se queda la marca compacta
 * arriba del formulario, para que la persona sepa en qué sitio está.
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
          <div className="mb-6 flex justify-center lg:hidden">
            <BrandMark size={26} />
          </div>
          {form}
        </div>
      </div>
    </div>
  );
}
