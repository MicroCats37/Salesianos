"use client";

import { LogOut, UserRound } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandMark } from "@/components/brand/BrandMark";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "./ThemeToggle";

/**
 * AccountTopbar - the chrome of the account area.
 *
 * The responsible has five destinations, so a sidebar of twenty-two items
 * would be noise: the account area gets a slim top bar and the menu of the
 * user. `/mi-cuenta` is the hub.
 *
 * The destination the visitor is on is exposed with `aria-current="page"`
 * (SH-02 A11Y-10) and carries the gold rule of the active navigation item
 * (UX-01), exactly like the public and administration families.
 */
export interface AccountTopbarProps {
  /** Display name of the signed-in account. */
  usuario?: string;
  /** Whether the account may open the administration area. */
  esAdmin?: boolean;
  /**
   * Whether the brand mark is shown.
   *
   * Inside the shell of the authenticated product the brand already lives in
   * the sidebar: repeating it here would say the same thing twice.
   */
  conMarca?: boolean;
  /** The section of the account the visitor is in. */
  seccion?: string;
}

/**
 * The sections of the account area, with the name the bar shows.
 *
 * It is derived from the route on every render, never stored: a hard reload
 * and the browser back button always mark the right section.
 */
const SECCIONES = [
  { href: RUTAS.cuenta.miCuenta, label: "Resumen de tus operaciones" },
  { href: RUTAS.cuenta.misInscripciones, label: "Tus inscripciones" },
  { href: RUTAS.cuenta.misCompras, label: "Tus compras" },
  { href: RUTAS.cuenta.inscripcion, label: "Crear una inscripción" },
];

export function AccountTopbar({
  usuario,
  esAdmin = false,
  conMarca = true,
  seccion,
}: AccountTopbarProps) {
  const pathname = usePathname();

  /**
   * Whether a destination is the one the visitor is on right now.
   *
   * A DETAIL route belongs to its list: `/mis-compras/123` is still "Tus
   * compras". The prefix counts as the same destination, so the bar never
   * loses the context of where the visitor is, and the mark of the current
   * location (`aria-current`) follows the same rule.
   */
  const esActivo = (href: string) =>
    pathname === href || pathname.startsWith(`${href}/`);

  const seccionActual =
    seccion ?? SECCIONES.find((destino) => esActivo(destino.href))?.label;

  return (
    <header className="sticky top-0 z-(--z-sticky) flex h-16 items-center gap-3 border-b border-border bg-background/85 px-4 backdrop-blur-md sm:px-6">
      {conMarca ? (
        <Link
          href={RUTAS.cuenta.miCuenta}
          className="rounded-[var(--radius-sm)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          <BrandMark size={24} />
          <span className="sr-only">Salesianos FEST — Mi cuenta</span>
        </Link>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
          Mi cuenta
        </span>
        {seccionActual ? (
          <span className="truncate text-sm font-semibold text-foreground">
            {seccionActual}
          </span>
        ) : null}
      </div>

      <div className="flex items-center gap-1 sm:gap-2">
        <ThemeToggle />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="min-h-11 gap-2 rounded-full px-3"
              aria-label="Abrir menú de cuenta"
            >
              <span className="inline-flex size-8 items-center justify-center rounded-full bg-muted text-sm font-bold text-primary">
                <UserRound className="size-4" aria-hidden="true" />
              </span>
              {usuario ? (
                <span className="hidden max-w-[18ch] truncate text-sm font-medium sm:inline">
                  {usuario}
                </span>
              ) : null}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>Mi cuenta</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link
                href={RUTAS.cuenta.miCuenta}
                aria-current={
                  esActivo(RUTAS.cuenta.miCuenta) ? "page" : undefined
                }
                className={cn(
                  esActivo(RUTAS.cuenta.miCuenta) &&
                    "border-l-2 border-accent pl-3 font-semibold",
                )}
              >
                Mi cuenta
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link
                href={RUTAS.cuenta.misInscripciones}
                aria-current={
                  esActivo(RUTAS.cuenta.misInscripciones) ? "page" : undefined
                }
                className={cn(
                  esActivo(RUTAS.cuenta.misInscripciones) &&
                    "border-l-2 border-accent pl-3 font-semibold",
                )}
              >
                Mis inscripciones
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link
                href={RUTAS.cuenta.misCompras}
                aria-current={
                  esActivo(RUTAS.cuenta.misCompras) ? "page" : undefined
                }
                className={cn(
                  esActivo(RUTAS.cuenta.misCompras) &&
                    "border-l-2 border-accent pl-3 font-semibold",
                )}
              >
                Mis compras
              </Link>
            </DropdownMenuItem>
            {esAdmin ? (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link
                    href={RUTAS.administracion.resumen}
                    aria-current={
                      esActivo(RUTAS.administracion.resumen)
                        ? "page"
                        : undefined
                    }
                    className={cn(
                      esActivo(RUTAS.administracion.resumen) &&
                        "border-l-2 border-accent pl-3 font-semibold",
                    )}
                  >
                    Administración
                  </Link>
                </DropdownMenuItem>
              </>
            ) : null}
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <a href="/api/auth/logout">
                <LogOut className="size-4" aria-hidden="true" />
                Cerrar sesión
              </a>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
