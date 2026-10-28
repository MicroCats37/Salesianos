"use client";

import { Menu, Radio, User, X } from "lucide-react";
import Link from "next/link";
import { type ReactNode, useEffect, useState } from "react";
import { NavbarBrand } from "@/components/branding/NavbarBrand";
import { Button } from "@/components/ui/button";
import { useAuthUser } from "@/features/auth/store/auth.store";
import { EN_VIVO } from "@/features/portada/config/festival";

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
      ? "/admin/dashboard"
      : "/dashboard";
  const registrationHref = user ? "/inscripcion" : "/register";
  /**
   * The party passes are bought with an account: a visitor without a session
   * is sent to the registration, exactly like the sports registration.
   */
  const pasesHref = user ? "/pases" : "/register";
  const canShowLive = showLive && EN_VIVO.url.length > 0;

  return (
    <>
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-white focus:px-4 focus:py-2 focus:shadow-lg"
      >
        Saltar al contenido
      </a>

      <header
        className={`sticky top-0 z-50 border-b backdrop-blur-xl transition-all ${
          scrolled
            ? "border-[#312e8e]/10 bg-white/92 shadow-lg"
            : "border-transparent bg-white/80"
        }`}
      >
        <div className="mx-auto flex h-[74px] max-w-[1480px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <div className="shrink-0">{brandSlot}</div>

          <nav className="hidden min-w-0 items-center justify-center gap-5 text-[13px] font-bold text-[#4c5480] xl:flex">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="whitespace-nowrap transition hover:text-[#312e8e]"
              >
                {link.label}
              </a>
            ))}
          </nav>

          <div className="hidden shrink-0 items-center gap-3 lg:flex">
            {canShowLive ? (
              <Button
                asChild
                variant="outline"
                className="h-11 rounded-full border-[#312e8e]/25 px-4 text-xs font-black uppercase tracking-wider text-[#312e8e]"
              >
                <a href={EN_VIVO.url} target="_blank" rel="noopener noreferrer">
                  <Radio className="mr-2 size-4" />
                  En vivo
                </a>
              </Button>
            ) : null}

            {user ? (
              <Button
                asChild
                variant="ghost"
                className="h-11 rounded-full px-5 text-sm font-black text-[#4c5480]"
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
                className="h-11 rounded-full px-5 text-sm font-black text-[#4c5480]"
              >
                <Link href="/login">Iniciar sesión</Link>
              </Button>
            )}

            <Button
              asChild
              variant="outline"
              className="h-11 rounded-full border-[#312e8e]/25 px-4 text-xs font-black uppercase tracking-wider text-[#312e8e]"
            >
              <Link href={pasesHref}>Comprar pase de fiesta</Link>
            </Button>

            <Button
              asChild
              className="btn-brand-gradient btn-shine h-11 rounded-full px-5 text-sm font-black text-white"
            >
              <Link href={registrationHref}>{ctaLabel}</Link>
            </Button>
          </div>

          <button
            type="button"
            className="flex size-11 shrink-0 items-center justify-center rounded-xl border border-[#312e8e]/10 xl:hidden"
            aria-label={mobileOpen ? "Cerrar menú" : "Abrir menú"}
            aria-expanded={mobileOpen}
            aria-controls="navbar-mobile-menu"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? (
              <X className="size-5 text-[#312e8e]" />
            ) : (
              <Menu className="size-5 text-[#312e8e]" />
            )}
          </button>
        </div>

        {mobileOpen ? (
          <div
            id="navbar-mobile-menu"
            className="border-t border-[#312e8e]/10 bg-white px-4 py-4 xl:hidden"
          >
            <nav className="flex flex-col gap-4">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="text-sm font-bold text-[#4c5480]"
                >
                  {link.label}
                </a>
              ))}
              <div className="flex flex-col gap-2 pt-2">
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
                    <Link href="/login">Iniciar sesión</Link>
                  </Button>
                )}

                <Button
                  asChild
                  variant="outline"
                  className="h-11 rounded-xl border-[#312e8e]/25 font-black text-[#312e8e]"
                >
                  <Link href={pasesHref}>Comprar pase de fiesta</Link>
                </Button>

                <Button
                  asChild
                  className="btn-brand-gradient h-11 rounded-xl font-black text-white"
                >
                  <Link href={registrationHref}>{ctaLabel}</Link>
                </Button>

                {canShowLive ? (
                  <Button
                    asChild
                    variant="outline"
                    className="h-11 rounded-xl font-black uppercase tracking-wider text-[#312e8e]"
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
