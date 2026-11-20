"use client";

import {
  ChevronDown,
  Globe,
  LogOut,
  Ticket,
  UserRound,
} from "lucide-react";
import Link from "next/link";
import type { CSSProperties } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ThemeMenuItems } from "@/features/theme/ThemeMenuItems";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";

export interface AdminUserMenuProps {
  /** Display name of the signed-in account. */
  usuario?: string;
  /** The tier of the account, shown under the name. */
  nivel?: string;
  /** The surface the menu lives on. */
  tone?: "sidebar" | "surface";
  /** Render only the avatar, for the narrow topbar. */
  compact?: boolean;
  className?: string;
}

/**
 * The palette of the dropdown when it opens FROM the navy sidebar.
 *
 * The content of a dropdown is portaled to the body: without this, a menu
 * born on the navy console would open in the light palette of the page.
 * Overriding the ROLE tokens (not the raw colors) keeps the menu inside the
 * same design system.
 */
const TONO_SIDEBAR = {
  "--color-popover": "var(--sidebar-background)",
  "--color-popover-foreground": "var(--sidebar-foreground)",
  "--color-accent": "var(--sidebar-accent)",
  "--color-accent-foreground": "var(--sidebar-accent-foreground)",
} as CSSProperties;

/**
 * AdminUserMenu - the account of the operator.
 *
 * The old footer was a name, a role and a logout button floating in the
 * corner. An account is a MENU: it carries the identity, the way back to
 * the account area, the way back to the public site, the theme and the
 * logout, and it separates the destructive action from the rest.
 */
export function AdminUserMenu({
  usuario,
  nivel,
  tone = "sidebar",
  compact = false,
  className,
}: AdminUserMenuProps) {
  const iniciales =
    usuario
      ?.split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((parte) => parte[0])
      .join("")
      .toUpperCase() || "AF";

  const esSidebar = tone === "sidebar";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className={cn(
            "flex w-full items-center gap-3 rounded-[var(--radius-lg)] text-left outline-hidden transition-colors duration-(--motion-duration-fast) focus-visible:outline-2 focus-visible:outline-offset-2",
            esSidebar
              ? "px-2 py-2 hover:bg-sidebar-accent focus-visible:outline-sidebar-ring"
              : "px-1.5 py-1.5 hover:bg-muted focus-visible:outline-ring",
            className,
          )}
          aria-label={`Cuenta de ${usuario ?? "operador"}`}
        >
          <Avatar
            className={cn(
              "size-10 shrink-0",
              esSidebar
                ? "ring-2 ring-sidebar-primary/70"
                : "ring-1 ring-border",
            )}
          >
            <AvatarFallback
              className={cn(
                "text-sm font-bold",
                esSidebar
                  ? "bg-sidebar-primary text-sidebar-primary-foreground"
                  : "bg-primary text-primary-foreground",
              )}
            >
              {iniciales}
            </AvatarFallback>
          </Avatar>

          {!compact ? (
            <span className="flex min-w-0 flex-1 flex-col leading-tight">
              <span
                className={cn(
                  "truncate text-xs font-bold uppercase tracking-wider",
                  esSidebar
                    ? "text-sidebar-foreground"
                    : "text-foreground",
                )}
              >
                {usuario ?? "Operador"}
              </span>
              <span
                className={cn(
                  "truncate text-[11px]",
                  esSidebar
                    ? "text-sidebar-foreground/70"
                    : "text-muted-foreground",
                )}
              >
                {nivel ?? "Staff"}
              </span>
            </span>
          ) : null}

          <ChevronDown
            className={cn(
              "size-4 shrink-0 transition-transform duration-(--motion-duration-fast)",
              esSidebar
                ? "text-sidebar-foreground/70"
                : "text-muted-foreground",
            )}
            aria-hidden="true"
          />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="start"
        side="top"
        sideOffset={8}
        style={esSidebar ? TONO_SIDEBAR : undefined}
        className={cn(
          "w-64",
          esSidebar && "ring-sidebar-border",
        )}
      >
        <DropdownMenuLabel>Sesión</DropdownMenuLabel>
        <DropdownMenuSeparator />

        <DropdownMenuItem asChild>
          <Link href={RUTAS.cuenta.miCuenta}>
            <UserRound className="size-4" aria-hidden="true" />
            Mi cuenta
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem asChild>
          <Link href={RUTAS.publico.inicio}>
            <Globe className="size-4" aria-hidden="true" />
            Volver al sitio público
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem asChild>
          <Link href={RUTAS.publico.pases}>
            <Ticket className="size-4" aria-hidden="true" />
            Pases de fiesta
          </Link>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuSub>
          <DropdownMenuSubTrigger>
            <span className="size-4" aria-hidden="true" />
            Tema
          </DropdownMenuSubTrigger>
          <DropdownMenuSubContent
            style={esSidebar ? TONO_SIDEBAR : undefined}
            className={cn("w-40", esSidebar && "ring-sidebar-border")}
          >
            <ThemeMenuItems />
          </DropdownMenuSubContent>
        </DropdownMenuSub>

        <DropdownMenuSeparator />

        <DropdownMenuItem variant="destructive" asChild>
          <a href="/api/auth/logout">
            <LogOut className="size-4" aria-hidden="true" />
            Cerrar sesión
          </a>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
