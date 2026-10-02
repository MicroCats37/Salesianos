"use client";

import { Menu, User, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { NavbarBrand } from "@/components/branding/NavbarBrand";
import { PreinscribirButton } from "./PreinscribirButton";
import { useAuthUser } from "@/features/auth/store/auth.store";

export function Navbar() {
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

  const navLinks = [
    { href: "#disciplinas", label: "Disciplinas" },
    { href: "#paquetes", label: "Paquetes" },
    { href: "#proceso", label: "Proceso" },
    { href: "#reglamento", label: "Reglamento" },
  ];

  return (
    <header
      className={`sticky top-0 z-50 border-b backdrop-blur-xl transition-all ${
        scrolled
          ? "bg-white/92 shadow-lg border-[#312e8e]/10"
          : "bg-white/80 border-transparent"
      }`}
    >
      <div className="mx-auto flex h-[74px] max-w-[1480px] items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <NavbarBrand href="/" />

        {/* Desktop nav links */}
        <nav className="hidden items-center gap-7 text-sm font-bold text-[#4c5480] lg:flex">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="transition hover:text-[#312e8e]"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Right buttons */}
        <div className="hidden items-center gap-3 lg:flex">
          {user ? (
            <>
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
              <Button
                asChild
                className="btn-brand-gradient btn-shine h-11 rounded-full px-6 text-sm font-black"
              >
                <Link href="/inscripcion">Inscribirme</Link>
              </Button>
            </>
          ) : (
            <>
              <Button
                asChild
                variant="ghost"
                className="h-11 rounded-full px-5 text-sm font-black text-[#4c5480]"
              >
                <Link href="/login">Iniciar sesión</Link>
              </Button>
              <PreinscribirButton
                className="btn-brand-gradient btn-shine h-11 rounded-full px-5 text-sm font-black text-white"
              />
            </>
          )}
        </div>

        {/* Mobile menu button */}
        <button
          type="button"
          className="flex size-11 items-center justify-center rounded-xl border border-[#312e8e]/10 lg:hidden"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? (
            <X className="size-5 text-[#312e8e]" />
          ) : (
            <Menu className="size-5 text-[#312e8e]" />
          )}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t border-[#312e8e]/10 bg-white px-4 py-4 lg:hidden">
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
                <>
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
                  <Button
                    asChild
                    className="btn-brand-gradient h-11 rounded-xl font-black text-white"
                  >
                    <Link href="/inscripcion">Inscribirme</Link>
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    asChild
                    variant="outline"
                    className="h-11 rounded-xl font-bold"
                  >
                    <Link href="/login">Iniciar sesión</Link>
                  </Button>
                  <PreinscribirButton
                    className="btn-brand-gradient h-11 rounded-xl font-black text-white"
                  />
                </>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
