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
import { ADMIN_CAPACIDADES, type AdminCapacidad } from "./admin.capacidades";

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
  /**
   * Capability the caller must hold to SEE the section.
   *
   * Absent means the section is always visible (the entries of the team
   * panel are not part of the administration area).
   */
  capacidad?: AdminCapacidad;
}

/**
 * The seven sections of the administration area — the SINGLE source of truth.
 *
 * Both the sidebar of the product and the navigation of the area read this
 * list: a section can never exist in one place and be missing in the other.
 *
 * The `capacidad` of every section is the DERIVED view of the matrix
 * "sección → ruta → capability": it is NOT persisted per user and it does
 * NOT need a table. The backend owns the real decision (`core/capacidades.py`
 * and `RequireCapability`); this field only decides what the navigation
 * SHOWS.
 */
export const ADMIN_SECCIONES: AdminSeccion[] = [
  {
    id: "resumen",
    title: "Resumen",
    icon: ShieldCheck,
    href: "/administracion",
    description: "Métricas del evento activo",
    capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
  },
  {
    id: "inscripciones",
    title: "Inscripciones",
    icon: ClipboardList,
    href: "/administracion/inscripciones",
    description: "Registros y su detalle",
    capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
  },
  {
    id: "pagos",
    title: "Pagos",
    icon: CreditCard,
    href: "/administracion/pagos",
    description: "Compras y órdenes de pago",
    // El staff LEE los pagos; aprobar y anular es una acción SENSIBLE
    // (`admin.pagos.aprobar`) que solo tiene el nivel de break-glass.
    capacidad: ADMIN_CAPACIDADES.PAGOS_VER,
  },
  {
    id: "equipos",
    title: "Equipos",
    icon: Trophy,
    href: "/administracion/equipos",
    description: "Plantillas de los equipos",
    capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
  },
  {
    id: "competencias",
    title: "Competencias",
    icon: Swords,
    href: "/administracion/competencias",
    description: "Competencias, cuadro y agenda",
    capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
  },
  {
    id: "participantes",
    title: "Participantes",
    icon: Users,
    href: "/administracion/participantes",
    description: "Personas y participaciones",
    capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
  },
  {
    id: "acreditaciones",
    title: "Acreditaciones",
    icon: QrCode,
    href: "/administracion/acreditaciones",
    description: "Acreditaciones y accesos",
    capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
  },
  {
    id: "usuarios",
    title: "Usuarios",
    icon: UserCog,
    href: "/administracion/usuarios",
    description: "Cuentas del evento",
    capacidad: ADMIN_CAPACIDADES.USUARIOS_VER,
  },
];

/**
 * The sections the caller may see.
 *
 * A section is kept when it declares NO capability (the entries outside the
 * administration area) or when the caller holds its capability.
 *
 * The function is PURE and fails closed: an undefined or empty set of
 * capabilities leaves only the sections without one. Hiding a section is a
 * courtesy — the real control is the 403 of the backend.
 */
export function adminSeccionesVisibles(
  capacidades: readonly string[] | undefined | null,
  secciones: AdminSeccion[] = ADMIN_SECCIONES,
): AdminSeccion[] {
  if (!capacidades) {
    return secciones.filter((seccion) => !seccion.capacidad);
  }

  const concedidas = new Set(capacidades);

  return secciones.filter(
    (seccion) => !seccion.capacidad || concedidas.has(seccion.capacidad),
  );
}

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
