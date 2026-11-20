import type { ReactNode } from "react";
import { RouteTransition } from "@/components/shell/RouteTransition";

/**
 * The authentication layout.
 *
 * It is NEUTRAL on purpose: the band of brand and the glass card belong to
 * `AuthShell`, which composes them per variant (login / register). A chrome
 * here would duplicate the panel and the form column.
 *
 * It is NOT chrome-free, though. The access route is reached from anywhere,
 * often with the keyboard, and the other three families of the product open
 * with the same skip link: the landmark `main` and the link that jumps to it
 * are the contract of every route group, not a luxury of the public one.
 */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-(--z-toast) focus:rounded-[var(--radius-md)] focus:bg-primary focus:px-4 focus:py-3 focus:font-semibold focus:text-primary-foreground"
      >
        Saltar al contenido
      </a>

      <main id="contenido">
        <RouteTransition>{children}</RouteTransition>
      </main>
    </div>
  );
}
