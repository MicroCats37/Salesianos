import type { LucideIcon } from "lucide-react";
import {
  ClipboardList,
  CreditCard,
  QrCode,
  ShieldCheck,
  Swords,
  Trophy,
  UserCog,
  Users,
} from "lucide-react";

/**
 * A section of the administration area.
 *
 * The four visible fields (title, icon, href, description) are the ones the
 * sidebar of the product already used; the `id` is the stable key of the
 * section (React key and identity of the active section).
 */
export interface AdminSeccion {
  /** Stable identifier of the section. */
  id: string;
  /** Label of the section. */
  title: string;
  /** Icon of the section. */
  icon: LucideIcon;
  /** Route of the section. */
  href: string;
  /** Description of the section (the sidebar shows it). */
  description: string;
}

/**
 * The seven sections of the administration area — the SINGLE source of truth.
 *
 * Both the sidebar of the product and the navigation of the area read this
 * list: a section can never exist in one place and be missing in the other.
 */
export const ADMIN_SECCIONES: AdminSeccion[] = [
  {
    id: "resumen",
    title: "Resumen",
    icon: ShieldCheck,
    href: "/administracion",
    description: "Métricas del evento activo",
  },
  {
    id: "inscripciones",
    title: "Inscripciones",
    icon: ClipboardList,
    href: "/administracion/inscripciones",
    description: "Registros y su detalle",
  },
  {
    id: "pagos",
    title: "Pagos",
    icon: CreditCard,
    href: "/administracion/pagos",
    description: "Compras y órdenes de pago",
  },
  {
    id: "equipos",
    title: "Equipos",
    icon: Trophy,
    href: "/administracion/equipos",
    description: "Plantillas de los equipos",
  },
  {
    id: "competencias",
    title: "Competencias",
    icon: Swords,
    href: "/administracion/competencias",
    description: "Competencias, cuadro y agenda",
  },
  {
    id: "participantes",
    title: "Participantes",
    icon: Users,
    href: "/administracion/participantes",
    description: "Personas y participaciones",
  },
  {
    id: "acreditaciones",
    title: "Acreditaciones",
    icon: QrCode,
    href: "/administracion/acreditaciones",
    description: "Acreditaciones y accesos",
  },
  {
    id: "usuarios",
    title: "Usuarios",
    icon: UserCog,
    href: "/administracion/usuarios",
    description: "Cuentas del evento",
  },
];

/**
 * The active section of a route.
 *
 * A section is active when the route IS the section or one of its
 * descendants (`/administracion/inscripciones/123` still marks
 * "Inscripciones"). When several sections match, the MOST SPECIFIC one wins.
 *
 * The active state is derived from the route on every render: it is never
 * stored, so a hard reload and the browser back button always mark the right
 * section.
 */
export function adminSeccionActiva(
  pathname: string,
  secciones: AdminSeccion[] = ADMIN_SECCIONES,
): AdminSeccion | null {
  return secciones.reduce<AdminSeccion | null>((mejor, seccion) => {
    const coincide =
      pathname === seccion.href ||
      (seccion.href !== "/" && pathname.startsWith(`${seccion.href}/`));

    if (!coincide) return mejor;
    if (!mejor) return seccion;

    return seccion.href.length > mejor.href.length ? seccion : mejor;
  }, null);
}
