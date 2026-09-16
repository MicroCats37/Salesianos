/**
 * Asignaciones utility functions.
 */

/**
 * Format asignacion rol for display.
 */
export function formatAsignacionRol(rol: string): string {
  const rolMap: Record<string, string> = {
    revisor: "Revisor",
    inspector: "Inspector",
    aprobador: "Aprobador",
    supervisor: "Supervisor",
  };
  return rolMap[rol] ?? rol;
}
