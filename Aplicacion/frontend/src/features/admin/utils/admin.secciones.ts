import type { LucideIcon } from "lucide-react";
import {
  Boxes,
  CalendarClock,
  ClipboardList,
  CreditCard,
  Gift,
  LayoutDashboard,
  QrCode,
  ScanLine,
  ShoppingBag,
  Store,
  Swords,
  Ticket,
  Trophy,
  UserCog,
  Users,
} from "lucide-react";
import { ADMIN_CAPACIDADES, type AdminCapacidad } from "./admin.capacidades";

/**
 * A destination of the administration area.
 *
 * The four visible fields (title, icon, href, description) are the ones the
 * sidebar of the product already used; the `id` is the stable key of the
 * destination (React key and identity of the active destination).
 */
export interface AdminDestino {
  /** Stable identifier of the destination. */
  id: string;
  /** Label of the destination. */
  title: string;
  /** Icon of the destination. */
  icon: LucideIcon;
  /** Route of the destination. */
  href: string;
  /** Description of the destination (the sidebar shows it). */
  description: string;
  /**
   * Capability the caller must hold to SEE the destination.
   *
   * Absent means the destination is always visible. Hiding it is a courtesy;
   * the real control is the 403 of the backend.
   */
  capacidad?: AdminCapacidad;
}

/**
 * A group of destinations inside the administration navigation.
 *
 * The three groups come from `frontend/04` §1: Deportivo, Ventas y entradas,
 * Personas y configuración.
 */
export interface AdminGrupo {
  /** Stable identifier of the group. */
  id: string;
  /** Label of the group. */
  title: string;
  /** Destinations of the group. */
  destinos: AdminDestino[];
}

/**
 * The single entry point of the administration area.
 *
 * It lives outside the groups: it is the summary, not a section.
 */
export const ADMIN_RESUMEN: AdminDestino = {
  id: "resumen",
  title: "Resumen",
  icon: LayoutDashboard,
  href: "/administracion",
  description: "Estado de la edición activa",
  capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
};

/**
 * The destinations of the administration area — SINGLE source of truth.
 *
 * Both the sidebar and any other navigation read this list: a destination can
 * never exist in one place and be missing in the other.
 *
 * The `capacidad` of every destination is the DERIVED view of the matrix
 * "destino → ruta → capacidad": it is NOT persisted per user and it does NOT
 * need a table. The backend owns the real decision (`core/capacidades.py` and
 * `RequireCapability`); this field only decides what the navigation SHOWS.
 */
export const ADMIN_GRUPOS: AdminGrupo[] = [
  {
    id: "deportivo",
    title: "Deportivo",
    destinos: [
      {
        id: "ediciones",
        title: "Ediciones",
        icon: CalendarClock,
        href: "/administracion/ediciones",
        description: "Módulos habilitados y fechas",
        capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
      },
      {
        id: "inscripciones",
        title: "Inscripciones",
        icon: ClipboardList,
        href: "/administracion/inscripciones",
        description: "Registros, pool y equipos",
        capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
      },
      {
        id: "equipos",
        title: "Equipos",
        icon: Trophy,
        href: "/administracion/equipos",
        description: "Plantillas y elegibilidad",
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
        id: "competencias",
        title: "Competencias",
        icon: Swords,
        href: "/administracion/competencias",
        description: "Competencias, cuadro y agenda",
        capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
      },
    ],
  },
  {
    id: "ventas",
    title: "Ventas y entradas",
    destinos: [
      {
        id: "pagos",
        title: "Pagos",
        icon: CreditCard,
        href: "/administracion/pagos",
        description: "Compras, órdenes y veredictos",
        // El staff LEE los pagos; aprobar y anular es una acción SENSIBLE
        // (`admin.pagos.aprobar`) que solo tiene el nivel de break-glass.
        capacidad: ADMIN_CAPACIDADES.PAGOS_VER,
      },
      {
        id: "pases",
        title: "Pases",
        icon: Ticket,
        href: "/administracion/pases",
        description: "Pases de fiesta y cortesías",
        capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
      },
      {
        id: "ingreso",
        title: "Control de ingreso",
        icon: ScanLine,
        href: "/administracion/pases/validar",
        description: "Validación de entradas",
        capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
      },
      {
        id: "tienda",
        title: "Tienda",
        icon: Store,
        href: "/administracion/marketplace",
        description: "Productos, pedidos y existencias",
        capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
      },
      {
        id: "entregas",
        title: "Entregas",
        icon: ShoppingBag,
        href: "/administracion/marketplace/entregas",
        description: "Recogidas por confirmar",
        capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
      },
      {
        id: "patrocinadores",
        title: "Patrocinadores",
        icon: Gift,
        href: "/administracion/patrocinadores",
        description: "Aliados y sus piezas",
        capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
      },
    ],
  },
  {
    id: "personas",
    title: "Personas y configuración",
    destinos: [
      {
        id: "personas",
        title: "Personas",
        icon: Boxes,
        href: "/administracion/personas",
        description: "Búsqueda por documento",
        capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
      },
      {
        id: "usuarios",
        title: "Usuarios",
        icon: UserCog,
        href: "/administracion/usuarios",
        description: "Cuentas y habilitación",
        capacidad: ADMIN_CAPACIDADES.USUARIOS_VER,
      },
      {
        id: "validaciones",
        title: "Validaciones",
        icon: QrCode,
        href: "/administracion/validaciones",
        description: "Auditoría de ingresos y entregas",
        capacidad: ADMIN_CAPACIDADES.ADMIN_VER,
      },
    ],
  },
];

/**
 * Every destination of the area, flattened.
 *
 * The order is the reading order of the navigation: summary, then the groups
 * in their declared order.
 */
export const ADMIN_DESTINOS: AdminDestino[] = [
  ADMIN_RESUMEN,
  ...ADMIN_GRUPOS.flatMap((grupo) => grupo.destinos),
];

/**
 * The destinations the caller may see.
 *
 * A destination is kept when it declares NO capability or when the caller
 * holds its capability.
 *
 * The function is PURE and fails closed: an undefined or empty set of
 * capabilities leaves only the destinations without one.
 */
export function adminSeccionesVisibles(
  capacidades: readonly string[] | undefined | null,
  destinos: AdminDestino[] = ADMIN_DESTINOS,
): AdminDestino[] {
  if (!capacidades) {
    return destinos.filter((destino) => !destino.capacidad);
  }

  const concedidas = new Set(capacidades);

  return destinos.filter(
    (destino) => !destino.capacidad || concedidas.has(destino.capacidad),
  );
}

/**
 * The groups the caller may see, keeping only the groups that end up with at
 * least one visible destination.
 *
 * An empty group is not rendered: a header with nothing under it is noise.
 */
export function adminGruposVisibles(
  capacidades: readonly string[] | undefined | null,
  grupos: AdminGrupo[] = ADMIN_GRUPOS,
): AdminGrupo[] {
  const visibles = new Set(
    adminSeccionesVisibles(
      capacidades,
      grupos.flatMap((g) => g.destinos),
    ).map((destino) => destino.id),
  );

  return grupos
    .map((grupo) => ({
      ...grupo,
      destinos: grupo.destinos.filter((destino) => visibles.has(destino.id)),
    }))
    .filter((grupo) => grupo.destinos.length > 0);
}

/**
 * The active destination of a route.
 *
 * A destination is active when the route IS the destination or one of its
 * descendants (`/administracion/inscripciones/123` still marks
 * "Inscripciones"). When several destinations match, the MOST SPECIFIC one
 * wins.
 *
 * The active state is derived from the route on every render: it is never
 * stored, so a hard reload and the browser back button always mark the right
 * destination.
 */
export function adminSeccionActiva(
  pathname: string,
  destinos: AdminDestino[] = ADMIN_DESTINOS,
): AdminDestino | null {
  return destinos.reduce<AdminDestino | null>((mejor, destino) => {
    const coincide =
      pathname === destino.href ||
      (destino.href !== "/" && pathname.startsWith(`${destino.href}/`));

    if (!coincide) return mejor;
    if (!mejor) return destino;

    return destino.href.length > mejor.href.length ? destino : mejor;
  }, null);
}

/**
 * Whether the caller may open the administration area at all.
 *
 * `es_admin` is the backend verdict; this helper only reads it.
 */
export function adminEsAdministrador(
  sesion: {
    es_admin?: boolean;
    is_staff?: boolean;
    is_superuser?: boolean;
  } | null,
): boolean {
  if (!sesion) return false;
  return Boolean(sesion.es_admin || sesion.is_staff || sesion.is_superuser);
}
