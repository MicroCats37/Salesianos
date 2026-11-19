"use client";

import { ChevronDown } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandMark } from "@/components/brand/BrandMark";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  type AdminDestino,
  type AdminGrupo,
  adminSeccionActiva,
} from "@/features/admin/utils/admin.secciones";
import { cn } from "@/lib/utils";

/**
 * AdminSidebar - the navigation of the administration area.
 *
 * The destinations arrive as a prop, already filtered by the capability
 * session the server read. The client never decides what an administrator may
 * open: hiding an entry is a courtesy and the 403 of the backend is the
 * control.
 *
 * The active entry is DERIVED from the pathname on every render, so a reload
 * and the back button always mark the right destination. The active marker is
 * the gold rule - the same gesture the public sections use - AND
 * `aria-current="page"` (SH-02 A11Y-10): the visitor who cannot see the gold
 * rule still hears where they are.
 */
export interface AdminSidebarProps {
  resumen: AdminDestino;
  grupos: AdminGrupo[];
  /** Label of the signed-in account, shown in the footer. */
  usuario?: string;
  /** Whether the account holds the break-glass tier. */
  superusuario?: boolean;
}

export function AdminSidebar({
  resumen,
  grupos,
  usuario,
  superusuario = false,
}: AdminSidebarProps) {
  const pathname = usePathname();
  const activo = adminSeccionActiva(pathname);

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border">
      <SidebarHeader className="border-b border-sidebar-border">
        <Link
          href="/"
          className="flex items-center gap-2 rounded-[--radius-sm] px-1 py-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sidebar-ring"
        >
          <BrandMark size={22} />
          <span className="truncate text-sm font-bold text-sidebar-foreground">
            Administración
          </span>
        </Link>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] font-bold uppercase tracking-[0.2em] text-sidebar-foreground/70">
            Edición
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={activo?.id === resumen.id}
                  className={cn(
                    "h-auto min-h-11 py-2",
                    activo?.id === resumen.id &&
                      "border-l-2 border-accent bg-sidebar-accent font-bold",
                  )}
                >
                  <Link
                    href={resumen.href}
                    aria-current={
                      activo?.id === resumen.id ? "page" : undefined
                    }
                  >
                    <resumen.icon className="size-4" aria-hidden="true" />
                    <span className="flex flex-col items-start">
                      <span>{resumen.title}</span>
                      <span className="text-xs font-normal text-sidebar-foreground/70">
                        {resumen.description}
                      </span>
                    </span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {grupos.map((grupo) => (
          <Collapsible key={grupo.id} defaultOpen className="group/grupo">
            <SidebarGroup>
              <CollapsibleTrigger className="flex min-h-11 w-full items-center gap-2 rounded-[--radius-md] px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-sidebar-foreground/70 hover:bg-sidebar-accent">
                {grupo.title}
                <ChevronDown
                  className="ml-auto size-4 transition-transform duration-(--motion-duration-base) group-data-[state=closed]/grupo:-rotate-90"
                  aria-hidden="true"
                />
              </CollapsibleTrigger>
              <CollapsibleContent>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {grupo.destinos.map((destino) => {
                      const esActivo = activo?.id === destino.id;

                      return (
                        <SidebarMenuItem key={destino.id}>
                          <SidebarMenuButton
                            asChild
                            isActive={esActivo}
                            className={cn(
                              "h-auto min-h-11 py-2",
                              esActivo &&
                                "border-l-2 border-accent bg-sidebar-accent font-bold",
                            )}
                          >
                            <Link
                              href={destino.href}
                              aria-current={esActivo ? "page" : undefined}
                            >
                              <destino.icon
                                className="size-4"
                                aria-hidden="true"
                              />
                              <span className="flex flex-col items-start">
                                <span>{destino.title}</span>
                                <span className="text-xs font-normal text-sidebar-foreground/70">
                                  {destino.description}
                                </span>
                              </span>
                            </Link>
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      );
                    })}
                  </SidebarMenu>
                </SidebarGroupContent>
              </CollapsibleContent>
            </SidebarGroup>
          </Collapsible>
        ))}
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <div className="flex flex-col gap-1 px-2 py-1 text-sm">
          {usuario ? (
            <span className="truncate font-medium text-sidebar-foreground">
              {usuario}
            </span>
          ) : null}
          {superusuario ? (
            <span className="text-xs font-bold uppercase tracking-wider text-accent">
              Superusuario
            </span>
          ) : null}
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
