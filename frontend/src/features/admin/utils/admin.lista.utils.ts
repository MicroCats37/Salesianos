/**
 * Canonical pagination, search and ordering rules of the administration area —
 * the CLIENT mirror of the backend `AdminPaginacionService`.
 *
 * Dependency-free on purpose: the module must stay importable without the
 * React/axios runtime so the mapping can be verified deterministically (same
 * pattern as `features/inscripciones/utils/pool.estado.ts`).
 *
 * The rules are the ones of `sdd/administracion-operativa-fest/admin-surface`
 * §4.1:
 *
 * | Param       | Default | Rule                                                        |
 * |-------------|---------|-------------------------------------------------------------|
 * | `page`      | 1       | 1-based; values below 1 are clamped to 1                    |
 * | `page_size` | 25      | max 100; values ABOVE the max are CLAMPED, never an error   |
 * | `q`         | —       | trimmed and capped at 120 characters                        |
 * | `ordering`  | per     | SERVER-SIDE WHITELIST; format `field` / `-field`            |
 *
 * The client NEVER invents an ordering value: it only offers the public
 * field names of the whitelist and sends them verbatim.
 *
 * NAMESPACES: a page with two lists (the people and the roster rows, the
 * accreditations and the access log) gives each list its own namespace, so
 * the filters of one tab never reach the endpoint of the other one. The
 * namespace is a PREFIX of the URL parameter names; the parameters sent to
 * the backend never carry it.
 */

/** Default page of every administration list. */
export const ADMIN_PAGE_POR_DEFECTO = 1;

/** Default page size of every administration list. */
export const ADMIN_PAGE_SIZE_POR_DEFECTO = 25;

/** Maximum page size accepted by the backend. */
export const ADMIN_PAGE_SIZE_MAXIMO = 100;

/** Maximum length of the free-text term. */
export const ADMIN_Q_MAXIMO = 120;

/**
 * The URL-owned state of one administration list.
 *
 * `filtros` holds the RESOURCE filters (state, package, discipline, ...) as
 * plain strings: they are written to the URL as they are and sent to the
 * backend as they are.
 */
export interface AdminEstadoLista {
  page: number;
  pageSize: number;
  q: string;
  ordering: string;
  filtros: Record<string, string>;
}

/** A sortable field of a resource, with the labels of the two directions. */
export interface AdminCampoOrden {
  /** Public field name — the only thing the backend whitelist accepts. */
  campo: string;
  /** Label of the field. */
  etiqueta: string;
  /** Label of the ascending direction (defaults to `<etiqueta> · asc`). */
  etiquetaAsc?: string;
  /** Label of the descending direction (defaults to `<etiqueta> · desc`). */
  etiquetaDesc?: string;
}

/** An ordering option of the "sort by" control. */
export interface AdminOpcionOrden {
  valor: string;
  etiqueta: string;
}

/** Normalize a page number: 1-based, values below 1 are clamped to 1. */
export function adminNormalizarPage(valor: unknown): number {
  if (valor === null || valor === undefined || valor === "") {
    return ADMIN_PAGE_POR_DEFECTO;
  }

  const numero = Number(valor);
  if (!Number.isFinite(numero)) return ADMIN_PAGE_POR_DEFECTO;
  return Math.max(Math.trunc(numero), ADMIN_PAGE_POR_DEFECTO);
}

/**
 * Normalize a page size.
 *
 * A value ABOVE the maximum is CLAMPED, not rejected: the backend contract
 * says "max 100; values above the max are clamped (not an error)".
 */
export function adminNormalizarPageSize(valor: unknown): number {
  if (valor === null || valor === undefined || valor === "") {
    return ADMIN_PAGE_SIZE_POR_DEFECTO;
  }

  const numero = Number(valor);
  if (!Number.isFinite(numero)) return ADMIN_PAGE_SIZE_POR_DEFECTO;
  return Math.min(Math.max(Math.trunc(numero), 1), ADMIN_PAGE_SIZE_MAXIMO);
}

/** Normalize the free-text term: trimmed, whitespace-collapsed and capped. */
export function adminNormalizarQ(valor: unknown): string {
  if (valor === null || valor === undefined) return "";
  const limpio = String(valor).split(/\s+/).filter(Boolean).join(" ");
  return limpio.slice(0, ADMIN_Q_MAXIMO);
}

/** Normalize the ordering value: trimmed, without a stray leading dash. */
export function adminNormalizarOrdering(valor: unknown): string {
  if (valor === null || valor === undefined) return "";
  const limpio = String(valor).trim();
  if (limpio === "-") return "";
  return limpio;
}

/** The reserved URL parameters of a namespace. */
export function adminClavesReservadas(prefijo = ""): Set<string> {
  return new Set([
    `${prefijo}page`,
    `${prefijo}page_size`,
    `${prefijo}q`,
    `${prefijo}ordering`,
    `${prefijo}detalle`,
  ]);
}

/**
 * Whether a URL parameter belongs to a namespace.
 *
 * A prefixed namespace owns every parameter that starts with its prefix. The
 * main namespace (no prefix) owns the reserved parameters and every
 * parameter that does NOT belong to one of its SIBLING namespaces.
 */
export function adminEsClavePropia(
  clave: string,
  prefijo = "",
  otros: string[] = [],
): boolean {
  if (prefijo) return clave.startsWith(prefijo);

  if (adminClavesReservadas("").has(clave)) return true;

  return !otros.some((otro) => clave.startsWith(otro));
}

function clavesDe(
  parametros: URLSearchParams | Record<string, string> | null | undefined,
): string[] {
  if (!parametros) return [];
  if (parametros instanceof URLSearchParams) {
    return Array.from(parametros.keys());
  }
  return Object.keys(parametros);
}

function leerDe(
  parametros: URLSearchParams | Record<string, string> | null | undefined,
  clave: string,
): string {
  if (!parametros) return "";
  if (parametros instanceof URLSearchParams) {
    return parametros.get(clave) ?? "";
  }
  return parametros[clave] ?? "";
}

/**
 * Read the list state out of the URL.
 *
 * Every parameter that the namespace owns and that is not a reserved one is a
 * RESOURCE filter and is kept verbatim (without the namespace prefix).
 */
export function adminEstadoDesdeParametros(
  parametros: URLSearchParams | Record<string, string> | null | undefined,
  prefijo = "",
  otros: string[] = [],
): AdminEstadoLista {
  const reservadas = adminClavesReservadas(prefijo);
  const filtros: Record<string, string> = {};

  for (const clave of clavesDe(parametros)) {
    if (!adminEsClavePropia(clave, prefijo, otros)) continue;
    if (reservadas.has(clave)) continue;

    const valor = leerDe(parametros, clave).trim();
    if (valor) filtros[clave.slice(prefijo.length)] = valor;
  }

  return {
    page: adminNormalizarPage(leerDe(parametros, `${prefijo}page`)),
    pageSize: adminNormalizarPageSize(
      leerDe(parametros, `${prefijo}page_size`),
    ),
    q: adminNormalizarQ(leerDe(parametros, `${prefijo}q`)),
    ordering: adminNormalizarOrdering(leerDe(parametros, `${prefijo}ordering`)),
    filtros,
  };
}

/**
 * The parameters sent to the backend.
 *
 * `page` and `page_size` are ALWAYS sent; the rest only when they carry a
 * value. The namespace prefix never reaches the backend.
 */
export function adminParametrosConsulta(
  estado: AdminEstadoLista,
): Record<string, string | number> {
  const parametros: Record<string, string | number> = {
    page: estado.page,
    page_size: estado.pageSize,
  };

  if (estado.q) parametros.q = estado.q;
  if (estado.ordering) parametros.ordering = estado.ordering;

  for (const [clave, valor] of Object.entries(estado.filtros)) {
    const limpio = String(valor ?? "").trim();
    if (limpio) parametros[clave] = limpio;
  }

  return parametros;
}

/**
 * The parameters written to the browser URL.
 *
 * The defaults are omitted so the URL stays readable and shareable: `?q=ana`
 * means "first page, 25 per page, searching for ana".
 */
export function adminParametrosUrl(
  estado: AdminEstadoLista,
  prefijo = "",
): URLSearchParams {
  const parametros = new URLSearchParams();

  if (estado.page !== ADMIN_PAGE_POR_DEFECTO) {
    parametros.set(`${prefijo}page`, String(estado.page));
  }

  if (estado.pageSize !== ADMIN_PAGE_SIZE_POR_DEFECTO) {
    parametros.set(`${prefijo}page_size`, String(estado.pageSize));
  }

  if (estado.q) parametros.set(`${prefijo}q`, estado.q);
  if (estado.ordering) parametros.set(`${prefijo}ordering`, estado.ordering);

  for (const [clave, valor] of Object.entries(estado.filtros)) {
    const limpio = String(valor ?? "").trim();
    if (limpio) parametros.set(`${prefijo}${clave}`, limpio);
  }

  return parametros;
}

/**
 * The URL of a namespace after an update.
 *
 * The parameters of the SIBLING namespaces are preserved: changing the
 * filters of one tab never erases the state of the other one.
 */
export function adminParametrosUrlActualizados(
  parametros: URLSearchParams,
  estado: AdminEstadoLista,
  prefijo = "",
  otros: string[] = [],
): URLSearchParams {
  const resultado = new URLSearchParams(parametros.toString());
  const detalle = `${prefijo}detalle`;

  for (const clave of Array.from(resultado.keys())) {
    if (!adminEsClavePropia(clave, prefijo, otros)) continue;
    // The open drilldown survives a change of the list state.
    if (clave === detalle) continue;
    resultado.delete(clave);
  }

  for (const [clave, valor] of adminParametrosUrl(estado, prefijo).entries()) {
    resultado.set(clave, valor);
  }

  return resultado;
}

/**
 * Whether a filter is narrowing the list.
 *
 * It drives the difference between the EMPTY state ("there is no data") and
 * the FILTERED-EMPTY state ("there is no data for the current filters").
 */
export function adminHayFiltrosActivos(estado: AdminEstadoLista): boolean {
  if (estado.q) return true;
  return Object.values(estado.filtros).some(
    (valor) => String(valor ?? "").trim() !== "",
  );
}

/**
 * The ordering options of the "sort by" control.
 *
 * Only the PUBLIC field names of the backend whitelist are offered: the
 * client never sends an ORM expression.
 */
export function adminOpcionesOrdering(
  campos: AdminCampoOrden[],
): AdminOpcionOrden[] {
  return campos.flatMap((campo) => [
    {
      valor: campo.campo,
      etiqueta: campo.etiquetaAsc ?? `${campo.etiqueta} · asc`,
    },
    {
      valor: `-${campo.campo}`,
      etiqueta: campo.etiquetaDesc ?? `${campo.etiqueta} · desc`,
    },
  ]);
}

/** The field and the direction of an ordering value. */
export function adminCampoOrdenActual(ordering: string): {
  campo: string;
  descendente: boolean;
} {
  const limpio = adminNormalizarOrdering(ordering);
  if (!limpio) return { campo: "", descendente: false };

  if (limpio.startsWith("-")) {
    return { campo: limpio.slice(1), descendente: true };
  }

  return { campo: limpio, descendente: false };
}

/**
 * Toggle the direction of an ordering.
 *
 * The SAME field toggles asc/desc; a DIFFERENT field starts in ascending
 * order. An unknown field of the current ordering is replaced.
 */
export function adminAlternarOrdering(actual: string, campo: string): string {
  const { campo: campoActual, descendente } = adminCampoOrdenActual(actual);

  if (campoActual === campo) {
    return descendente ? campo : `-${campo}`;
  }

  return campo;
}

/** Whether an ordering value belongs to the whitelist of a resource. */
export function adminEsOrdenValido(
  ordering: string,
  permitidos: string[],
): boolean {
  const { campo } = adminCampoOrdenActual(ordering);
  if (!campo) return true;
  return permitidos.includes(campo);
}
