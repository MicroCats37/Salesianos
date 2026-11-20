"use client";

import {
  CalendarRange,
  ChevronDown,
  ClipboardList,
  Contact,
  CreditCard,
  Handshake,
  LayoutDashboard,
  type LucideIcon,
  PackageCheck,
  ScanLine,
  ScrollText,
  Store,
  Swords,
  Ticket,
  Trophy,
  UserCog,
  UsersRound,
} from "lucide-react";
import { gsap } from "gsap";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
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
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  type AdminDestino,
  type AdminGrupo,
  type AdminIcono,
  adminSeccionActiva,
} from "@/features/admin/utils/admin.secciones";
import { useGSAP } from "@/hooks/system/use-gsap";
import { RUTAS } from "@/lib/routes";
import { cn } from "@/lib/utils";
import { AdminUserMenu } from "./AdminUserMenu";

const ADMIN_ICONOS: Record<AdminIcono, LucideIcon> = {
  resumen: LayoutDashboard,
  ediciones: CalendarRange,
  inscripciones: ClipboardList,
  equipos: Trophy,
  participantes: UsersRound,
  competencias: Swords,
  pagos: CreditCard,
  pases: Ticket,
  ingreso: ScanLine,
  tienda: Store,
  entregas: PackageCheck,
  patrocinadores: Handshake,
  personas: Contact,
  usuarios: UserCog,
  validaciones: ScrollText,
};

/**
 * The destinations of the RESPONSIBLE, at the head of the navigation.
 *
 * The operator of the console is also a responsible: the two areas of the
 * product share the same navigation and the same person. These destinations
 * live here instead of in a second menu that nobody opens.
 *
 * They are ALWAYS visible: they do not depend on any capability.
 */
export const DESTINOS_CUENTA = [
  {
    id: "mi-cuenta",
    titulo: "Mi cuenta",
    descripcion: "Resumen de tus operaciones",
    href: RUTAS.cuenta.miCuenta,
    icon: UserCog,
  },
  {
    id: "mis-inscripciones",
    titulo: "Mis inscripciones",
    descripcion: "Registros y su estado",
    href: RUTAS.cuenta.misInscripciones,
    icon: ClipboardList,
  },
  {
    id: "mis-compras",
    titulo: "Mis compras",
    descripcion: "Compras y órdenes de pago",
    href: RUTAS.cuenta.misCompras,
    icon: CreditCard,
  },
  {
    id: "crear-inscripcion",
    titulo: "Crear inscripción",
    descripcion: "Promoción, paquete y equipos",
    href: RUTAS.cuenta.inscripcion,
    icon: Trophy,
  },
  {
    id: "evento",
    titulo: "El festival",
    descripcion: "Programa del evento",
    href: RUTAS.publico.inicio,
    icon: ClipboardList,
  },
] as const;

export interface AppSidebarProps {
  /** The groups of administration, already filtered by capability. */
  grupos?: AdminGrupo[];
  /** The summary of the administration area, when it exists. */
  resumen?: AdminDestino;
  /** Label of the signed-in account, shown in the footer. */
  usuario?: string;
  /** The tier of the account, shown in the footer. */
  nivel?: string;
  /** Whether the account holds the break-glass tier. */
  superusuario?: boolean;
  /** The name of the area, under the logo. */
  area?: string;
}

/**
 * AppSidebar - the navigation of the AUTHENTICATED product.
 *
 * There is ONE navigation for the whole authenticated product: the
 * destinations of the responsible are always at the top, and the groups of
 * administration appear below ONLY when the backend granted the capability
 * that opens them. A responsible never sees a section it cannot open, and
 * an administrator never has to learn two different systems.
 *
 * The surface is the blue of the brand: the console of the event has a
 * colour of its own, and the gold is the accent and the active rule. The
 * active entry is marked with the gold rule, with the weight AND with
 * `aria-current="page"` (SH-02 A11Y-10): the visitor who cannot see the
 * colour still hears where they are.
 */
export function AppSidebar({
  grupos = [],
  resumen,
  usuario,
  nivel,
  superusuario = false,
  area = "Panel de control",
}: AppSidebarProps) {
  const pathname = usePathname();
  const { isMobile, setOpenMobile } = useSidebar();

  const destinos = resumen
    ? [resumen, ...grupos.flatMap((grupo) => grupo.destinos)]
    : [];
  const activo = adminSeccionActiva(pathname, destinos);
  const ResumenIcono = resumen ? ADMIN_ICONOS[resumen.icon] : null;

  /**
   * The groups the operator has closed BY HAND.
   *
   * A group that holds the current route is always open: the operator lands
   * inside it and must see where they are. The manual close only wins for
   * the groups that are not the current one.
   */
  const [cerrados, setCerrados] = useState<Record<string, boolean>>({});
  const grupoActivoId = grupos.find((grupo) =>
    grupo.destinos.some((destino) => destino.id === activo?.id),
  )?.id;
  const grupoActivoPrevio = useRef(grupoActivoId);

  useEffect(() => {
    if (grupoActivoPrevio.current === grupoActivoId) return;

    grupoActivoPrevio.current = grupoActivoId;

    if (!grupoActivoId) return;

    setCerrados((previos) => {
      if (!(grupoActivoId in previos)) return previos;

      const siguiente = { ...previos };
      delete siguiente[grupoActivoId];
      return siguiente;
    });
  }, [grupoActivoId]);

  /** The drawer of mobile closes after navigating: it covers the page. */
  const cerrarEnMovil = () => {
    if (isMobile) setOpenMobile(false);
  };

  return (
    <Sidebar
      collapsible="icon"
      variant="inset"
      className="border-r border-sidebar-border bg-brand-gradient-deep"
    >
      <SidebarHeader className="border-b border-sidebar-border/60 p-3">
        <Link
          href={RUTAS.publico.inicio}
          onClick={cerrarEnMovil}
          className="flex min-h-11 flex-col items-center gap-1.5 rounded-[var(--radius-lg)] px-2 py-3 transition-colors duration-(--motion-duration-fast) hover:bg-sidebar-accent focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sidebar-ring"
        >
          {/*
            La marca es la del producto: el logotipo oficial de Salesianos
            FEST y, debajo, la palabra que dice de quién es esta consola.
          */}
          <Image
            src="/images/brand.png"
            alt="Salesianos FEST"
            width={132}
            height={44}
            priority
            className="h-8 w-auto select-none group-data-[collapsible=icon]:hidden"
          />
          <span
            aria-hidden="true"
            className="hidden size-8 items-center justify-center rounded-[var(--radius-sm)] bg-sidebar-primary text-xs font-black text-sidebar-primary-foreground group-data-[collapsible=icon]:flex"
          >
            SF
          </span>
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-sidebar-primary">
            {area}
          </span>
        </Link>
      </SidebarHeader>

      <SidebarContent className="gap-1 px-2 py-3">
        <SidebarGroup className="p-0">
          <SidebarGroupLabel className="px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-sidebar-primary/80">
            Navegación
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {DESTINOS_CUENTA.map((destino) => {
                const esActivo = pathname === destino.href;
                const DestinoIcono = destino.icon;

                return (
                  <SidebarMenuItem key={destino.id}>
                    <SidebarMenuButton
                      asChild
                      isActive={esActivo}
                      tooltip={destino.titulo}
                      className={cn(
                        "h-auto min-h-11 gap-2.5 rounded-[var(--radius-md)] py-2 transition-transform duration-(--motion-duration-fast) hover:translate-x-0.5",
                        esActivo &&
                          "border-l-2 border-sidebar-primary bg-sidebar-accent font-bold text-sidebar-foreground",
                      )}
                    >
                      <Link
                        href={destino.href}
                        onClick={cerrarEnMovil}
                        aria-current={esActivo ? "page" : undefined}
                      >
                        <DestinoIcono
                          className={cn(
                            "size-4 shrink-0 transition-transform duration-(--motion-duration-fast) group-hover/menu-button:scale-110",
                            esActivo && "text-sidebar-primary",
                          )}
                          aria-hidden="true"
                        />
                        <span className="flex flex-col items-start leading-tight">
                          <span>{destino.titulo}</span>
                          <span className="text-xs font-normal text-sidebar-foreground/70">
                            {destino.descripcion}
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

        {resumen ? (
          <SidebarGroup className="p-0">
            <SidebarGroupLabel className="px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-sidebar-primary/80">
              Edición
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton
                    asChild
                    isActive={activo?.id === resumen.id}
                    tooltip={resumen.title}
                    className={cn(
                      "h-auto min-h-11 gap-2.5 rounded-[var(--radius-md)] py-2 transition-transform duration-(--motion-duration-fast) hover:translate-x-0.5",
                      activo?.id === resumen.id &&
                        "border-l-2 border-sidebar-primary bg-sidebar-accent font-bold text-sidebar-foreground",
                    )}
                  >
                    <Link
                      href={resumen.href}
                      onClick={cerrarEnMovil}
                      aria-current={
                        activo?.id === resumen.id ? "page" : undefined
                      }
                    >
                      {ResumenIcono ? (
                        <ResumenIcono
                          className={cn(
                            "size-4 shrink-0 transition-transform duration-(--motion-duration-fast) group-hover/menu-button:scale-110",
                            activo?.id === resumen.id && "text-sidebar-primary",
                          )}
                          aria-hidden="true"
                        />
                      ) : null}
                      <span className="flex flex-col items-start leading-tight">
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
        ) : null}

        {grupos.map((grupo) => (
          <AppGrupoNavegacion
            key={grupo.id}
            grupo={grupo}
            destinoActivoId={activo?.id}
            abierto={!cerrados[grupo.id]}
            onNavegar={cerrarEnMovil}
            onToggle={(abierto) =>
              setCerrados((previos) => ({
                ...previos,
                [grupo.id]: !abierto,
              }))
            }
          />
        ))}
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border/60 p-3 group-data-[collapsible=icon]:p-1">
        <div className="rounded-[var(--radius-lg)] border border-sidebar-elevated-border bg-sidebar-elevated p-2 transition-colors duration-(--motion-duration-base) hover:border-sidebar-primary/40 group-data-[collapsible=icon]:border-0 group-data-[collapsible=icon]:bg-transparent group-data-[collapsible=icon]:p-0">
          <AdminUserMenu
            usuario={usuario}
            nivel={superusuario ? "Superusuario" : nivel}
          />
        </div>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}

interface AppGrupoNavegacionProps {
  grupo: AdminGrupo;
  destinoActivoId?: string;
  abierto: boolean;
  onToggle: (abierto: boolean) => void;
  onNavegar: () => void;
}

/**
 * One collapsible group of the navigation.
 *
 * The group opens with a short stagger: the destinations do not appear all
 * at once, they arrive in reading order. The motion is a reveal (opacity and
 * a few pixels of translation), it never animates a height, and it is
 * skipped when the visitor asked for reduced motion.
 */
function AppGrupoNavegacion({
  grupo,
  destinoActivoId,
  abierto,
  onToggle,
  onNavegar,
}: AppGrupoNavegacionProps) {
  const contenidoRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const contenido = contenidoRef.current;

      if (!contenido || !abierto) return;

      const destinos = contenido.querySelectorAll("[data-sidebar-destino]");
      const media = gsap.matchMedia();

      media.add(
        { motionReducido: "(prefers-reduced-motion: reduce)" },
        (contexto) => {
          const condiciones = contexto.conditions as {
            motionReducido?: boolean;
          };

          if (condiciones.motionReducido) {
            gsap.set(destinos, { autoAlpha: 1, x: 0, clearProps: "all" });
            return;
          }

          gsap.fromTo(
            destinos,
            { autoAlpha: 0, x: -10 },
            {
              autoAlpha: 1,
              x: 0,
              duration: 0.26,
              ease: "power2.out",
              stagger: 0.035,
              overwrite: "auto",
              clearProps: "opacity,visibility,transform",
            },
          );
        },
      );

      return () => {
        media.revert();
      };
    },
    { scope: contenidoRef, dependencies: [abierto] },
  );

  return (
    <Collapsible
      open={abierto}
      onOpenChange={onToggle}
      className="group/grupo"
    >
      <SidebarGroup className="p-0">
        <CollapsibleTrigger
          className="flex min-h-11 w-full items-center gap-2 rounded-[var(--radius-md)] px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-sidebar-primary/80 transition-colors duration-(--motion-duration-fast) hover:bg-sidebar-accent hover:text-sidebar-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sidebar-ring group-data-[collapsible=icon]:hidden"
          aria-label={`${grupo.title}: ${abierto ? "contraer" : "expandir"}`}
        >
          {grupo.title}
          <ChevronDown
            className="ml-auto size-4 transition-transform duration-(--motion-duration-base) group-data-[state=closed]/grupo:-rotate-90"
            aria-hidden="true"
          />
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div ref={contenidoRef}>
            <SidebarGroupContent>
              <SidebarMenu className="mt-1 gap-0.5">
                {grupo.destinos.map((destino) => {
                  const esActivo = destinoActivoId === destino.id;
                  const DestinoIcono = ADMIN_ICONOS[destino.icon];

                  return (
                    <SidebarMenuItem key={destino.id}>
                      <SidebarMenuButton
                        asChild
                        isActive={esActivo}
                        tooltip={destino.title}
                        data-sidebar-destino
                        className={cn(
                          "h-auto min-h-11 gap-2.5 rounded-[var(--radius-md)] py-2 transition-transform duration-(--motion-duration-fast) hover:translate-x-0.5",
                          esActivo &&
                            "border-l-2 border-sidebar-primary bg-sidebar-accent font-bold text-sidebar-foreground",
                        )}
                      >
                        <Link
                          href={destino.href}
                          onClick={onNavegar}
                          aria-current={esActivo ? "page" : undefined}
                        >
                          <DestinoIcono
                            className={cn(
                              "size-4 shrink-0 transition-transform duration-(--motion-duration-fast) group-hover/menu-button:scale-110",
                              esActivo && "text-sidebar-primary",
                            )}
                            aria-hidden="true"
                          />
                          <span className="flex flex-col items-start leading-tight">
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
          </div>
        </CollapsibleContent>
      </SidebarGroup>
    </Collapsible>
  );
}
