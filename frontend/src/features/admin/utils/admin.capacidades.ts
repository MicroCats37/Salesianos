/**
 * Vocabulario de las capacidades de la superficie administrativa.
 *
 * Espejo 1:1 de `backend/core/capacidades.py`. El BACKEND es la autoridad:
 * estas constantes solo sirven para NOMBRAR las capacidades que el backend
 * publica en `GET /api/auth/me` y para filtrar la navegación.
 *
 * Ocultar un botón NO es autorizar: el backend vuelve a evaluar la
 * capacidad en cada petición (`RequireCapability`). El filtro es UX; el 403
 * del backend es el control.
 */

export const ADMIN_CAPACIDADES = {
  /** Leer toda el área de administración. */
  ADMIN_VER: "admin.ver",
  /** Escribir inscripciones y su roster. */
  INSCRIPCIONES_ESCRIBIR: "admin.inscripciones.escribir",
  /** Gestionar las plantillas de los equipos. */
  EQUIPOS_ESCRIBIR: "admin.equipos.escribir",
  /** Gestionar las competencias, el cuadro y los encuentros. */
  COMPETENCIAS_ESCRIBIR: "admin.competencias.escribir",
  /** Gestionar las acreditaciones y el control de acceso. */
  ACREDITACIONES_ESCRIBIR: "admin.acreditaciones.escribir",
  /** Leer los pagos. */
  PAGOS_VER: "admin.pagos.ver",
  /** Aprobar o anular un pago (acción sensible). */
  PAGOS_APROBAR: "admin.pagos.aprobar",
  /** Leer la tabla de cuentas. */
  USUARIOS_VER: "admin.usuarios.ver",
  /** Activar, desactivar, promover o degradar una cuenta. */
  USUARIOS_GESTIONAR: "admin.usuarios.gestionar",
  /** Conceder o revocar el nivel de break-glass. */
  USUARIOS_PROMOVER_SUPERUSUARIO: "admin.usuarios.promover_superusuario",
  /** Configuración del evento (futuro). */
  CONFIGURACION_GESTIONAR: "admin.configuracion.gestionar",
} as const;

/** The code of a capability, exactly as the backend names it. */
export type AdminCapacidad =
  (typeof ADMIN_CAPACIDADES)[keyof typeof ADMIN_CAPACIDADES];

/** The tier of an account, exactly as the backend names it. */
export const ADMIN_NIVELES = {
  USUARIO: "usuario",
  STAFF: "staff",
  SUPERUSUARIO: "superusuario",
} as const;

export type AdminNivel = (typeof ADMIN_NIVELES)[keyof typeof ADMIN_NIVELES];

/**
 * Whether the given set of capabilities holds the required one.
 *
 * An EMPTY or undefined set holds NOTHING: the UI fails closed.
 */
export function adminTieneCapacidad(
  capacidades: readonly string[] | undefined | null,
  capacidad: AdminCapacidad,
): boolean {
  if (!capacidades) {
    return false;
  }

  return capacidades.includes(capacidad);
}

/**
 * The label of a tier, as the administration surface shows it.
 *
 * The break-glass tier is EXPLICIT: an account administrator must be able to
 * see who holds it.
 */
export function adminNivelLabel(nivel: string | undefined | null): string {
  switch (nivel) {
    case ADMIN_NIVELES.SUPERUSUARIO:
      return "Superusuario";
    case ADMIN_NIVELES.STAFF:
      return "Staff";
    default:
      return "Participante";
  }
}
