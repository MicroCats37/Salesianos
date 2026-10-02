"use client";

import { useEffect, type ReactNode } from "react";
import { gsap } from "gsap";
import { AuthVisualPanel } from "@/features/auth/components/AuthVisualPanel";
import { cn } from "@/lib/utils";

export type AuthVariant = "login" | "register";

export interface AuthShellProps {
  variant: AuthVariant;
  /** Form column component shown on the opposite side of the carousel. */
  form: ReactNode;
  /** When true, layout is inverted (form left, carousel right). Default keeps carousel left. */
  invertColumns?: boolean;
}

export function AuthShell({ variant, form, invertColumns = false }: AuthShellProps) {
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
    <div
      className={cn(
        `${variant}-bg flex min-h-svh w-full flex-col overflow-hidden lg:flex-row`,
      )}
    >
      <div
        className={`relative hidden min-h-svh w-full overflow-hidden lg:block lg:w-1/2 ${visualOrder}`}
      >
        <div className="auth-shell-visual h-full w-full">
          <AuthVisualPanel variant={variant} />
        </div>
      </div>

      <div
        className={`relative flex min-h-svh w-full items-center justify-center overflow-y-auto px-4 py-6 sm:px-8 lg:w-1/2 lg:px-10 bg-[var(--brand-deep-blue)] text-white bg-auth-deep-gradient ${formOrder}`}
      >
        <div className="auth-shell-card relative z-10 w-full max-w-[520px] py-4">
          {form}
        </div>
      </div>
    </div>
  );
}
