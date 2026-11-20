/**
 * The query parameters of a route, as a flat map of strings.
 *
 * `GOV-02-RB-03b`: the filters of the administration lists live in the URL and
 * never in a component-local store. The page reads the query string and
 * hands it to the view; the filter bar writes it back.
 *
 * A repeated parameter keeps its FIRST value: the list reads one value per
 * filter, and a repeated parameter is a mistake of the URL, not a second
 * filter.
 */
export function parametrosDeConsulta(
  searchParams: Record<string, string | string[] | undefined>,
): Record<string, string> {
  const parametros: Record<string, string> = {};

  for (const [clave, valor] of Object.entries(searchParams)) {
    if (typeof valor === "string") {
      parametros[clave] = valor;
    } else if (Array.isArray(valor) && typeof valor[0] === "string") {
      parametros[clave] = valor[0];
    }
  }

  return parametros;
}
