import type { ReactNode } from "react";
import { RouteTransition } from "@/components/shell/RouteTransition";
import { SiteFooter } from "@/components/shell/SiteFooter";
import { SiteHeader } from "@/components/shell/SiteHeader";

/**
 * The public layout.
 *
 * A visitor reaches the event without a session. The header offers the
 * destinations the current edition published; the shell does not decide which
 * modules are enabled.
 */
export default function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-(--z-toast) focus:rounded-[var(--radius-md)] focus:bg-primary focus:px-4 focus:py-3 focus:font-semibold focus:text-primary-foreground"
      >
        Saltar al contenido
      </a>

      <SiteHeader />

      <main
        id="contenido"
        className="mx-auto w-full max-w-page flex-1 px-4 py-10 sm:px-6 sm:py-12 lg:px-10"
      >
        <RouteTransition>{children}</RouteTransition>
      </main>

      <SiteFooter />
    </div>
  );
}
