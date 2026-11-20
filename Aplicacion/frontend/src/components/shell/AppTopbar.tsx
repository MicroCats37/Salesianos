"use client";

import { PanelLeft } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { SidebarTrigger, useSidebar } from "@/components/ui/sidebar";
import {
  type AdminDestino,
  type AdminGrupo,
  adminSeccionActiva,
} from "@/features/admin/utils/admin.secciones";
import { RUTAS } from "@/lib/routes";
import { AdminUserMenu } from "./AdminUserMenu";
import { ThemeToggle } from "./ThemeToggle";

export interface AppTopbarProps {
  /** The tier of the account, shown as the subtitle of the area. */
  nivel: string;
  /** Display name of the signed-in account. */
  usuario?: string;
  /** The name of the area, the first crumb of the breadcrumb. */
  area: string;
  /** The route of the area. */
  areaHref: string;
  /** The destinations of the area, to name the section the operator is in. */
  destinos?: AdminDestino[];
}

/**
 * AppTopbar - the chrome of the authenticated product.
 *
 * It is the only bar of the product that lives next to a sidebar, so it
 * complements it instead of repeating it: the trigger of the sidebar, the
 * place where the operator is, the theme and the account. The account is
 * ALSO in the footer of the sidebar, but only one of the two is visible at
 * a time: with the sidebar open the footer owns it, and when the sidebar
 * collapses the compact avatar takes over.
 */
export function AppTopbar({
  nivel,
  usuario,
  area,
  areaHref,
  destinos = [],
}: AppTopbarProps) {
  const pathname = usePathname();
  const { isMobile, state } = useSidebar();
  const sidebarColapsada = state === "collapsed";

  const seccion = adminSeccionActiva(pathname, destinos)?.title;

  return (
    <header className="sticky top-0 z-(--z-sticky) flex h-16 items-center gap-3 border-b border-border bg-background/85 px-4 backdrop-blur-md sm:px-6">
      <SidebarTrigger
        className="size-11 shrink-0"
        aria-label="Abrir navegación"
      >
        <PanelLeft className="size-5" aria-hidden="true" />
      </SidebarTrigger>

      <div className="flex min-w-0 flex-1 flex-col">
        <Breadcrumb className="min-w-0">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink asChild>
                <Link
                  href={areaHref}
                  className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:text-foreground"
                >
                  {area}
                </Link>
              </BreadcrumbLink>
            </BreadcrumbItem>
            {seccion && seccion !== area ? (
              <>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage className="truncate text-sm font-semibold text-foreground">
                    {seccion}
                  </BreadcrumbPage>
                </BreadcrumbItem>
              </>
            ) : null}
          </BreadcrumbList>
        </Breadcrumb>

        <span className="hidden truncate text-xs text-muted-foreground sm:block">
          {nivel}
        </span>
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-2">
        <ThemeToggle />

        {/*
          La cuenta vive en el pie del sidebar. Sólo cuando el sidebar no
          está a la vista (móvil, o colapsado a iconos) el topbar muestra el
          avatar compacto: el acceso a la cuenta nunca desaparece.
        */}
        {isMobile || sidebarColapsada ? (
          <AdminUserMenu
            usuario={usuario}
            nivel={nivel}
            tone="surface"
            compact
            className="w-auto"
          />
        ) : null}
      </div>
    </header>
  );
}
