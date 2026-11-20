/**
 * The dates of the validation area.
 *
 * The backend publishes ISO-8601 instants and the edition lives in the
 * timezone of the server (`TIME_ZONE = "America/Lima"`, `USE_TZ = True` in
 * `Aplicacion/backend/config/settings/base.py`). The formatter pins BOTH the
 * locale and the timezone so the server and the browser render the SAME text:
 * a format that depends on the machine would break the hydration of the
 * route.
 *
 * This file repeats the formatter of the competitions area on purpose: a
 * shared root (`src/lib/**`) is out of the allowed roots of this packet, and
 * a cross-feature import would couple two domains that have no reason to
 * know each other. Extracting it to a common place is an A0 request
 * (`A0-UI05-05`).
 *
 * Formatting a date is PRESENTATION. It never derives a business fact.
 */

/** The timezone of the edition: the one the server publishes. */
const ZONA_EDICION = "America/Lima";

/** The locale of the interface: the one the server publishes. */
const IDIOMA = "es";

/**
 * The readable instant of a validation: "21 nov 2026 · 19:05".
 *
 * It returns `null` when there is no instant, so the caller shows the real
 * absence instead of a placeholder.
 */
export function formatearInstante(
  iso: string | null | undefined,
): string | null {
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
