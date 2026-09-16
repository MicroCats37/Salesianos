/**
 * Tramites utility functions.
 * Follows naming convention: {domain}.utils.ts → format{name}Error(), etc.
 */

/**
 * Format tramite estado for display.
 */
export function formatTramiteEstado(estado: string): string {
  const estadoMap: Record<string, string> = {
    pendiente: "Pendiente",
    en_proceso: "En Proceso",
    completado: "Completado",
    cancelado: "Cancelado",
  };
  return estadoMap[estado] ?? estado;
}
