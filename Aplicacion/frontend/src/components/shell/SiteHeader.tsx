"use client";

import { Menu, Ticket } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { BrandMark } from "@/components/brand/BrandMark";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { DESTINOS_PUBLICOS, RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";

/**
 * SiteHeader - the public header.
 *
 * One horizontal bar: the brand mark, the public destinations and the primary
 * action. Below 1024 the destinations collapse into a `Sheet`, because the
 * public header must never push the page wider than the viewport.
 *
 * The header does NOT decide which modules are enabled: it renders the
 * destinations the edition scope published. That list arrives as a prop.
 *
 * The current destination is exposed with `aria-current="page"` (SH-02
 * A11Y-10) and carries the gold rule of the active navigation item (UX-01):
 * a visitor who cannot see the colour still hears where they are, and a
 * visitor who cannot hear it still sees it.
 */
export interface SiteHeaderProps {
  /** Destinations the current edition actually offers. */
  destinos?: { href: string; label: string }[];
  /** Whether the visitor already has a session. */
  autenticado?: boolean;
}

export function SiteHeader({
  destinos = DESTINOS_PUBLICOS,
  autenticado = false,
}: SiteHeaderProps) {
  const pathname = usePathname();
  const [abierto, setAbierto] = useState(false);

  /** Whether a destination is the one the visitor is on right now. */
  const esActivo = (href: string) => pathname === href;

  return (
    <header className="sticky top-0 z-(--z-sticky) border-b border-border bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-10">
        <Link
          href={RUTAS.publico.inicio}
          className="rounded-[--radius-sm] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          <BrandMark size={26} />
          <span className="sr-only">Salesianos FEST — Portada</span>
        </Link>

        <nav aria-label="Navegación principal" className="hidden lg:block">
          <ul className="flex items-center gap-1">
            {destinos.map((destino) => {
              const activo = esActivo(destino.href);

              return (
                <li key={destino.href}>
                  <Link
                    href={destino.href}
                    aria-current={activo ? "page" : undefined}
                    className={cn(
                      "rounded-full border-b-2 px-4 py-2 text-sm font-medium transition-colors duration-(--motion-duration-fast) hover:bg-muted hover:text-foreground",
                      activo
                        ? "border-accent bg-muted font-semibold text-foreground"
                        : "border-transparent text-foreground-muted",
                    )}
                  >
                    {destino.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="flex items-center gap-2">
          <Button
            asChild
            className="hidden rounded-full bg-brand-gradient px-5 font-bold uppercase tracking-wider text-primary-foreground sm:inline-flex"
          >
            <Link
              href={autenticado ? RUTAS.cuenta.miCuenta : RUTAS.publico.pases}
            >
              <Ticket className="size-4" aria-hidden="true" />
              {autenticado ? "Mi cuenta" : "Conseguir pase"}
            </Link>
          </Button>

          <Sheet open={abierto} onOpenChange={setAbierto}>
            <SheetTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="size-11 lg:hidden"
                aria-label="Abrir menú de navegación"
              >
                <Menu className="size-5" aria-hidden="true" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-full max-w-sm p-6">
              <SheetTitle className="sr-only">Navegación</SheetTitle>
              <BrandMark size={26} />
              <nav aria-label="Navegación principal" className="mt-6">
                <ul className="flex flex-col gap-1">
                  {destinos.map((destino) => {
                    const activo = esActivo(destino.href);

                    return (
                      <li key={destino.href}>
                        <Link
                          href={destino.href}
                          onClick={() => setAbierto(false)}
                          aria-current={activo ? "page" : undefined}
                          className={cn(
                            "block rounded-[--radius-md] border-l-2 px-3 py-3 text-base font-medium transition-colors duration-(--motion-duration-fast) hover:bg-muted",
                            activo
                              ? "border-accent bg-muted font-semibold text-foreground"
                              : "border-transparent text-foreground",
                          )}
                        >
                          {destino.label}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </nav>
              <Button
                asChild
                className="mt-6 w-full rounded-full bg-brand-gradient font-bold uppercase tracking-wider text-primary-foreground"
              >
                <Link
                  href={
                    autenticado ? RUTAS.cuenta.miCuenta : RUTAS.publico.pases
                  }
                >
                  {autenticado ? "Mi cuenta" : "Conseguir pase"}
                </Link>
              </Button>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
