"use client";

import { Menu, Radio, User, X } from "lucide-react";
import Link from "next/link";
import { type ReactNode, useEffect, useState } from "react";
import { NavbarBrand } from "@/components/brand/NavbarBrand";
import { ThemeToggle } from "@/components/shell/ThemeToggle";
import { Button } from "@/components/ui/button";
import { useAuthUser } from "@/features/auth/store/auth.store";
import { EN_VIVO } from "@/features/portada/fixtures/festival";
import { RUTAS } from "@/lib/routes";

export interface NavbarProps {
  navLinks?: { href: string; label: string }[];
  showLive?: boolean;
  brandSlot?: ReactNode;
  ctaLabel?: string;
}

const DEFAULT_NAV_LINKS = [
  { href: "#disciplinas", label: "Disciplinas" },
  { href: "#paquetes", label: "Paquetes" },
  { href: "#proceso", label: "Proceso" },
  { href: "#reglamento", label: "Reglamento" },
];

export function Navbar({
  navLinks = DEFAULT_NAV_LINKS,
  showLive = false,
  brandSlot = <NavbarBrand />,
  ctaLabel = "Inscribir equipo",
}: NavbarProps) {
  const user = useAuthUser();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const dashboardHref =
    user?.rol === "admin_comite" || user?.rol === "admin_finanzas"
      ? RUTAS.administracion.resumen
      : RUTAS.cuenta.miCuenta;
  const registrationHref = user
    ? RUTAS.cuenta.inscripcion
    : RUTAS.auth.registro;
  /**
   * The party passes are bought with an account: a visitor without a session
   * is sent to the registration, exactly like the sports registration.
   */
  const pasesHref = user ? RUTAS.publico.pases : RUTAS.auth.registro;
  const canShowLive = showLive && EN_VIVO.url.length > 0;

  return (
    <>
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-surface-raised focus:px-4 focus:py-2 focus:shadow-lg"
      >
        Saltar al contenido
      </a>

      {/*
        La barra FLOTA: es una píldora de vidrio pegada al borde superior,
        no una franja que tape la página. El `pointer-events-none` del
        contenedor deja pasar el puntero por los huecos que sobran a los
        lados, y la píldora los recupera: nada de la portada deja de ser
        clicable por culpa del chrome.
      */}
      <header className="pointer-events-none sticky top-0 z-50 pt-3 sm:pt-4">
        <div
          className={`pointer-events-auto mx-auto flex h-16 w-[calc(100%-1.5rem)] max-w-[1400px] items-center justify-between gap-4 rounded-[var(--radius-2xl)] border px-3 transition-all duration-(--motion-duration-base) sm:w-[calc(100%-2rem)] sm:px-5 ${
            scrolled
              ? "border-border bg-surface-raised/90 shadow-[var(--elevation-lg)] backdrop-blur-xl"
              : "border-border/50 bg-surface-raised/65 shadow-[var(--elevation-md)] backdrop-blur-xl"
          }`}
        >
          <div className="shrink-0">{brandSlot}</div>

          <nav className="hidden min-w-0 items-center justify-center gap-5 text-[13px] font-bold text-muted-foreground xl:flex">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="whitespace-nowrap transition-colors hover:text-primary"
              >
                {link.label}
              </a>
            ))}
          </nav>

          <div className="hidden shrink-0 items-center gap-3 lg:flex">
            <ThemeToggle />

            {canShowLive ? (
              <Button
                asChild
                variant="outline"
                className="h-11 rounded-full border-primary/25 px-4 text-xs font-black uppercase tracking-wider text-primary"
              >
                <a
                  href={EN_VIVO.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Radio className="mr-2 size-4" />
                  En vivo
                </a>
              </Button>
            ) : null}

            {user ? (
              <Button
                asChild
                variant="ghost"
                className="h-11 rounded-full px-5 text-sm font-black text-muted-foreground"
              >
                <Link href={dashboardHref}>
                  <User className="mr-2 size-4" />
                  Mi cuenta
                </Link>
              </Button>
            ) : (
              <Button
                asChild
                variant="ghost"
                className="h-11 rounded-full px-5 text-sm font-black text-muted-foreground"
              >
                <Link href={RUTAS.auth.login}>Iniciar sesión</Link>
              </Button>
            )}

            <Button
              asChild
              variant="outline"
              className="h-11 rounded-full border-primary/25 px-4 text-xs font-black uppercase tracking-wider text-primary"
            >
              <Link href={pasesHref}>Comprar pase de fiesta</Link>
            </Button>

            <Button
              asChild
              className="btn-brand-gradient btn-shine h-11 rounded-full px-5 text-sm font-black text-primary-foreground"
            >
              <Link href={registrationHref}>{ctaLabel}</Link>
            </Button>
          </div>

          <button
            type="button"
            className="flex size-11 shrink-0 items-center justify-center rounded-[var(--radius-md)] border border-border/60 transition-colors hover:bg-muted xl:hidden"
            aria-label={mobileOpen ? "Cerrar menú" : "Abrir menú"}
            aria-expanded={mobileOpen}
            aria-controls="navbar-mobile-menu"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? (
              <X className="size-5 text-primary" />
            ) : (
              <Menu className="size-5 text-primary" />
            )}
          </button>
        </div>

        {mobileOpen ? (
          <div
            id="navbar-mobile-menu"
            className="pointer-events-auto mx-auto mt-2 w-[calc(100%-1.5rem)] max-w-[1400px] rounded-[var(--radius-xl)] border border-border/60 bg-surface-raised/95 p-4 shadow-[var(--elevation-lg)] backdrop-blur-xl sm:w-[calc(100%-2rem)] xl:hidden"
          >
            <nav className="flex flex-col gap-4">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="text-sm font-bold text-muted-foreground"
                >
                  {link.label}
                </a>
              ))}
              <div className="flex flex-col gap-2 pt-2">
                <ThemeToggle />

                {user ? (
                  <Button
                    asChild
                    variant="outline"
                    className="h-11 rounded-xl font-bold"
                  >
                    <Link href={dashboardHref}>
                      <User className="mr-2 size-4" />
                      Mi cuenta
                    </Link>
                  </Button>
                ) : (
                  <Button
                    asChild
                    variant="outline"
                    className="h-11 rounded-xl font-bold"
                  >
                    <Link href={RUTAS.auth.login}>Iniciar sesión</Link>
                  </Button>
                )}

                <Button
                  asChild
                  variant="outline"
                  className="h-11 rounded-xl border-primary/25 font-black text-primary"
                >
                  <Link href={pasesHref}>Comprar pase de fiesta</Link>
                </Button>

                <Button
                  asChild
                  className="btn-brand-gradient h-11 rounded-xl font-black text-primary-foreground"
                >
                  <Link href={registrationHref}>{ctaLabel}</Link>
                </Button>

                {canShowLive ? (
                  <Button
                    asChild
                    variant="outline"
                    className="h-11 rounded-xl font-black uppercase tracking-wider text-primary"
                  >
                    <a
                      href={EN_VIVO.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Radio className="mr-2 size-4" />
                      En vivo
                    </a>
                  </Button>
                ) : null}
              </div>
            </nav>
          </div>
        ) : null}
      </header>
    </>
  );
}
