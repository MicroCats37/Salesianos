/**
 * The dates of the competitions area.
 *
 * The backend publishes ISO-8601 instants and the edition lives in the
 * timezone of the server (`TIME_ZONE = "America/Lima"`, `USE_TZ = True` in
 * `Aplicacion/backend/config/settings/base.py`). The formatter pins BOTH the
 * locale and the timezone so the server and the browser render the SAME text:
 * a format that depends on the machine would break the hydration of the
 * route.
 *
 * Formatting a date is PRESENTATION. It never derives a business fact: a
 * duration, an overlap or a schedule is declared by the backend.
 */

/** The timezone of the edition: the one the server publishes. */
const ZONA_EDICION = "America/Lima";

/** The locale of the interface: the one the server publishes. */
const IDIOMA = "es";

/**
 * The readable instant of an encounter: "12 nov 2026 · 15:30".
 *
 * It returns `null` when there is no instant, so the caller shows the real
 * absence instead of a placeholder.
 */
export function formatearInstante(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return null;

  return new Intl.DateTimeFormat(IDIOMA, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: ZONA_EDICION,
  })
    .format(fecha)
    .replace(",", " ·");
}

/**
 * The readable day of a competition or of the agenda: "12 nov 2026".
 *
 * A competition publishes a DAY, not an instant: it is parsed as a plain
 * calendar day so the edition's day never shifts with the timezone.
 */
export function formatearDia(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const dia = /^\d{4}-\d{2}-\d{2}$/.test(iso) ? iso : iso.slice(0, 10);
  const [anio, mes, diaDelMes] = dia.split("-").map(Number);
  if (!anio || !mes || !diaDelMes) return null;

  return new Intl.DateTimeFormat(IDIOMA, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(anio, mes - 1, diaDelMes)));
}

/**
 * The duration between two instants, as the backend schedules them.
 *
 * The backend owns the schedule: this only renders the two instants it
 * published, and it never invents a length for an encounter that has no end.
 */
export function formatearHorario(
  inicio: string | null | undefined,
  fin: string | null | undefined,
): string | null {
  const desde = formatearInstante(inicio);
  if (!desde) return null;
  const hasta = formatearInstante(fin);
  return hasta ? `${desde} → ${hasta}` : desde;
}
