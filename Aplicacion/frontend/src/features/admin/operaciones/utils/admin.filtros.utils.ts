import type { ParamsListaAdmin } from "./admin.claves.utils";

/**
 * The mapping between the filters of the URL and the query of the server.
 *
 * The filters of the administration lists live in the URL and NOWHERE else
 * (`GOV-02-RB-03b` · `D-UI04-04`): the page reads the query string and the
 * filter bar writes it back.
 *
 * ## The rules
 *
 * 1. **Only the declared parameters travel.** A parameter that the list does
 *    not declare is IGNORED: the browser never invents a filter the backend
 *    does not know.
 * 2. **The numbers are parsed.** `page` and `page_size` are integers in the
 *    wire and strings in the URL. A value that is not a positive integer is
 *    DISCARDED (and not sent as `0` or as `NaN`).
 * 3. **The names are the frozen ones of `RT-PG-04`** (`page, page_size, q,
 *    ordering, estado_operativo, estado_compra, estado_orden, tipo, desde,
 *    hasta`) plus the edition that scopes the area.
 */
const PARAMETROS_TEXTO = [
  "edicion_id",
  "q",
  "ordering",
  "estado_operativo",
  "estado_compra",
  "estado_orden",
  "tipo",
  "desde",
  "hasta",
] as const;

/** A positive integer, or `undefined`. */
function enteroPositivo(valor: string | undefined): number | undefined {
  if (valor === undefined) return undefined;

  const numero = Number(valor);

  if (!Number.isInteger(numero) || numero < 1) return undefined;

  return numero;
}

/**
 * The query of the server, from the parameters of the URL.
 *
 * A parameter that is absent, empty or not a positive integer is DROPPED:
 * it does not travel in the key and it does not travel in the request.
 */
export function parametrosListaAdminDesdeUrl(
  parametros: Record<string, string> | undefined,
): ParamsListaAdmin {
  const origen = parametros ?? {};
  const destino: ParamsListaAdmin = {};

  for (const nombre of PARAMETROS_TEXTO) {
    const valor = origen[nombre];

    if (typeof valor === "string" && valor.trim() !== "") {
      destino[nombre] = valor.trim();
    }
  }

  const pagina = enteroPositivo(origen.page);
  if (pagina !== undefined) destino.page = pagina;

  const tamano = enteroPositivo(origen.page_size);
  if (tamano !== undefined) destino.page_size = tamano;

  return destino;
}

/**
 * The query of the server, as the params of the request.
 *
 * A parameter that is `undefined` is DROPPED: the request never carries an
 * empty filter.
 */
export function parametrosConsultaAdmin(
  parametros: ParamsListaAdmin,
): Record<string, string | number | undefined> {
  const consulta: Record<string, string | number | undefined> = {};

  for (const [nombre, valor] of Object.entries(parametros)) {
    if (valor !== undefined) {
      consulta[nombre] = valor;
    }
  }

  return consulta;
}
