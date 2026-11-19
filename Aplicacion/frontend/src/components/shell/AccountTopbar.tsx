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
}

export function AccountTopbar({
  usuario,
  esAdmin = false,
}: AccountTopbarProps) {
  const pathname = usePathname();

  /** Whether a destination is the one the visitor is on right now. */
  const esActivo = (href: string) => pathname === href;

  return (
    <header className="sticky top-0 z-(--z-sticky) border-b border-border bg-background/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1100px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link
          href={RUTAS.cuenta.miCuenta}
          className="rounded-[--radius-sm] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          <BrandMark size={24} />
          <span className="sr-only">Salesianos FEST — Mi cuenta</span>
        </Link>

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
