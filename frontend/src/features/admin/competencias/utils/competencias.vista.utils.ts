/**
 * The states of the views of the `competencias` module — loading, error and
 * empty.
 *
 * The resolution is a PURE function so the contract of the states can be
 * verified without rendering anything: the priority between the states never
 * changes by accident, and the difference between "there is no data" and
 * "there is no data for the current filters" is explicit.
 *
 * Dependency-free on purpose (same pattern as
 * `features/admin/utils/admin.lista.utils.ts`).
 */

/** The state a view can be in. */
export type CompetenciaEstadoVista = "cargando" | "error" | "vacio" | "listo";

/** The inputs of the resolution of a state. */
export interface CompetenciaEstadoVistaEntrada {
  /** Whether the query is still running. */
  cargando: boolean;
  /** Message of the failure of the query, if it failed. */
  error: string | null;
  /** How many rows the answer carries. */
  total: number;
}

/**
 * Resolve the state of a view.
 *
 * The priority is fixed: a running query is a LOADING view even when the
 * previous answer is still on screen, a failed query is an ERROR view, and
 * only a successful answer with no rows is an EMPTY view.
 */
export function resolverEstadoVista(
  entrada: CompetenciaEstadoVistaEntrada,
): CompetenciaEstadoVista {
  if (entrada.cargando) return "cargando";
  if (entrada.error) return "error";
  if (entrada.total === 0) return "vacio";
  return "listo";
}

/** The copy of an empty view. */
export interface CompetenciaVistaVacio {
  /** Title of the empty state. */
  titulo: string;
  /** Description of the empty state. */
  descripcion: string;
  /** Label of the action that clears the filters, if there are filters. */
  accion: string | null;
}

/**
 * The copy of the empty state.
 *
 * An empty list because there is nothing yet and an empty list because the
 * filters are too narrow are DIFFERENT situations: the second one offers the
 * action that clears the filters.
 */
export function resolverVistaVacio(
  hayFiltros: boolean,
  tituloSinFiltros: string,
  descripcionSinFiltros: string,
): CompetenciaVistaVacio {
  if (!hayFiltros) {
    return {
      titulo: tituloSinFiltros,
      descripcion: descripcionSinFiltros,
      accion: null,
    };
  }

  return {
    titulo: "Sin resultados",
    descripcion:
      "No hay resultados para los filtros actuales. Ajusta la búsqueda o limpia los filtros para ver todo.",
    accion: "Limpiar filtros",
  };
}
