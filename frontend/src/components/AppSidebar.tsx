"use client";

import {
  CalendarDays,
  CircleUserRound,
  FilePlus2,
  LogOut,
  Package,
  ScrollText,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
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
  SidebarRail,
} from "@/components/ui/sidebar";
import { useAuthStore } from "@/features/auth/store/auth.store";

const dashboardMenu = [
  {
    title: "Mis Inscripciones",
    icon: Package,
    href: "/dashboard",
    description: "Resumen y estado actual",
  },
  {
    title: "Crear Inscripcion",
    icon: FilePlus2,
    href: "/inscripcion",
    description: "Promocion, paquete y equipos",
  },
  {
    title: "Historial",
    icon: ScrollText,
    href: "/dashboard",
    description: "Tu actividad reciente",
  },
  {
    title: "Evento",
    icon: CalendarDays,
    href: "/",
    description: "Programa del festival",
  },
];

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const user = useAuthStore((s) => s.user);
  const clearStore = useAuthStore((s) => s.logout);

  const fullName =
    [user?.nombres, user?.apellidos].filter(Boolean).join(" ") ||
    user?.email ||
    "Usuario";
  const initials =
    [user?.nombres?.[0], user?.apellidos?.[0]]
      .filter(Boolean)
      .join("")
      .toUpperCase() ||
    (user?.email?.[0] ?? "S").toUpperCase();

  async function handleLogout() {
    try {
      setIsLoggingOut(true);
      try {
        await fetch("/api/auth/logout", { method: "POST" });
      } catch {
        // Server-side cookie cleanup failed; client logout still proceeds.
      }
      clearStore();
      toast.success("Sesion cerrada");
      router.replace("/");
    } finally {
      setIsLoggingOut(false);
    }
  }

  return (
    <Sidebar
      variant="inset"
      collapsible="icon"
      className="border-r border-slate-200/80 bg-gradient-to-b from-[#1f2357] via-[#1a1857] to-[#0c0c1f] text-white [&_[data-slot=sidebar-menu-button]]:!text-white/90 [&_[data-slot=sidebar-menu-button]]:hover:!bg-white/10 [&_[data-slot=sidebar-menu-button]]:data-[active=true]:!bg-white/15 [&_[data-slot=sidebar-menu-button]]:data-[active=true]:!text-white"
    >
      <SidebarHeader className="border-b border-white/10">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              size="lg"
              className="!p-2 transition-transform hover:scale-[1.02]"
            >
                <Link href="/dashboard" className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 shadow-md shadow-amber-500/30">
                    <CircleUserRound className="size-5 text-[#17214b]" />
                  </div>
                  <div className="flex flex-col gap-0.5 leading-none">
                    <span
                      className="text-sm font-black tracking-tight text-white"
                      style={{ fontFamily: "'Brush Script MT', 'Comic Sans MS', cursive" }}
                    >
                      <span style={{ color: "var(--brand-cyan-soft)" }}>
                        Salesianos
                      </span>{" "}
                      <span className="text-brand-cyan">FEST</span>{" "}
                      <span>2026</span>
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-amber-300/90">
                      Panel de equipo
                    </span>
                  </div>
                </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-300/80">
            Navegacion
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {dashboardMenu.map((item) => {
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/" &&
                    pathname.startsWith(`${item.href}/`));
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.title}
                      className="group h-auto flex-col items-start gap-0.5 rounded-xl px-3 py-2.5 transition-all hover:translate-x-0.5"
                    >
                      <Link
                        href={item.href}
                        className="flex w-full items-start gap-3"
                      >
                        <item.icon
                          className={cn(
                            "size-4 mt-0.5 transition-transform group-hover:scale-110",
                            isActive && "text-amber-300",
                          )}
                        />
                        <span className="flex flex-col gap-0">
                          <span className="text-xs font-black uppercase tracking-wider">
                            {item.title}
                          </span>
                          <span className="text-[10px] font-medium normal-case tracking-normal text-white/60">
                            {item.description}
                          </span>
                        </span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-white/10 p-3">
        <div className="rounded-xl border border-white/10 bg-white/5 p-3 backdrop-blur">
          <div className="flex items-center gap-3">
            <Avatar className="h-10 w-10 ring-2 ring-amber-300/60">
              <AvatarFallback className="bg-gradient-to-br from-amber-400 to-amber-600 text-sm font-black text-[#17214b]">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-1 flex-col leading-tight">
              <span className="truncate text-xs font-black uppercase tracking-wider text-white">
                {fullName}
              </span>
              <span className="truncate text-[10px] text-white/60">
                {user?.email ?? "Sin correo"}
              </span>
            </div>
            <Button
              type="button"
              size="icon"
              variant="ghost"
              onClick={handleLogout}
              disabled={isLoggingOut}
              aria-label="Cerrar sesion"
              title="Cerrar sesion"
              className="h-9 w-9 shrink-0 text-white/70 hover:bg-rose-500/20 hover:text-rose-200"
            >
              <LogOut className="size-4" />
            </Button>
          </div>
          <Button
            type="button"
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="group mt-2 flex w-full items-center justify-center gap-2 rounded-lg border border-rose-400/30 bg-rose-500/10 px-3 py-2 text-xs font-black uppercase tracking-wider text-rose-100 transition-colors hover:bg-rose-500/20 hover:text-white"
          >
            <LogOut className="size-3.5 transition-transform group-hover:-translate-x-0.5" />
            {isLoggingOut ? "Saliendo..." : "Cerrar sesion"}
          </Button>
        </div>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}

function cn(...classes: Array<string | false | undefined | null>) {
  return classes.filter(Boolean).join(" ");
}
