/**
 * URL contract of the `competencias` module — the CLIENT mirror of the query
 * parameters of the administrative endpoints.
 *
 * Dependency-free on purpose: the module must stay importable without the
 * React/axios runtime so the mapping can be verified deterministically (same
 * pattern as `features/admin/utils/admin.lista.utils.ts`).
 *
 * Two rules drive this module:
 *
 * 1. The URL OWNS the filters of every view: a filtered list can be shared,
 *    bookmarked and navigated back and forth without losing its context. The
 *    filters are read from the query string by `adminEstadoDesdeParametros`
 *    and written back by `useAdminListaUrl`.
 * 2. The client NEVER sends a parameter the endpoint does not declare. Each
 *    endpoint has its OWN whitelist, because the vocabulary of `estado` is
 *    NOT the same in every surface: in the list it is the state of the
 *    COMPETITION and in the agenda it is the state of the ENCOUNTER.
 */

/** Filters accepted by `GET /administracion/competencias`. */
export const COMPETENCIAS_FILTROS_LISTA = [
  "evento_id",
  "disciplina_id",
  "categoria_id",
  "estado",
  "fecha_desde",
  "fecha_hasta",
] as const;

/** Filters accepted by `GET /administracion/competencias/agenda`. */
export const COMPETENCIAS_FILTROS_AGENDA = [
  "fecha",
  "evento_id",
  "disciplina_id",
  "categoria_id",
  "estado",
] as const;

/** A filter of the module. */
export type CompetenciaFiltro = (typeof COMPETENCIAS_FILTROS_LISTA)[number];

/**
 * Keep only the accepted filters, trimmed, and drop the empty ones.
 *
 * An empty filter is NOT a filter: sending `estado=` would narrow the result
 * to the competitions whose state is the empty string.
 */
export function competenciasParametros(
  filtros: Record<string, string>,
  aceptados: readonly string[],
): Record<string, string> {
  const parametros: Record<string, string> = {};

  for (const clave of aceptados) {
    const limpio = String(filtros[clave] ?? "").trim();
    if (limpio) parametros[clave] = limpio;
  }

  return parametros;
}

/** The parameters of the list of competitions. */
export function competenciasParametrosLista(
  filtros: Record<string, string>,
): Record<string, string> {
  return competenciasParametros(filtros, COMPETENCIAS_FILTROS_LISTA);
}

/** The parameters of the agenda of ONE day. */
export function competenciasParametrosAgenda(
  filtros: Record<string, string>,
): Record<string, string> {
  return competenciasParametros(filtros, COMPETENCIAS_FILTROS_AGENDA);
}

/**
 * The day of the agenda in the LOCAL calendar (`YYYY-MM-DD`).
 *
 * The date is built from the local parts on purpose: `toISOString()` shifts
 * the day when the browser runs in a timezone behind UTC, and the agenda
 * would open on the wrong day.
 */
export function competenciasFechaHoy(): string {
  const ahora = new Date();
  const mes = String(ahora.getMonth() + 1).padStart(2, "0");
  const dia = String(ahora.getDate()).padStart(2, "0");
  return `${ahora.getFullYear()}-${mes}-${dia}`;
}

/**
 * The hour and the minute of an ISO instant (`HH:mm`).
 *
 * The backend serializes a naive ISO-8601 instant (`2026-11-16T14:30:00`),
 * so the hour is read from the TEXT of the payload: parsing it with `Date`
 * would apply the timezone of the browser to an instant that has none.
 */
export function competenciasHora(iso: string | null | undefined): string {
  if (!iso) return "";
  const coincidencia = /T(\d{2}):(\d{2})/.exec(iso);
  if (!coincidencia) return "";
  return `${coincidencia[1]}:${coincidencia[2]}`;
}

/**
 * The minutes of the day of an ISO instant, or `null` when it has none.
 *
 * The domain guarantees that the start and the end of an encounter share the
 * date of the competition, so the difference of the two instants of the day IS
 * the duration of the encounter.
 */
export function competenciasMinutosDelDia(
  iso: string | null | undefined,
): number | null {
  const hora = competenciasHora(iso);
  if (!hora) return null;
  const [horas, minutos] = hora.split(":").map(Number);
  if (!Number.isFinite(horas) || !Number.isFinite(minutos)) return null;
  return horas * 60 + minutos;
}
