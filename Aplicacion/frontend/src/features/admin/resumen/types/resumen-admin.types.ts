import type { EstadoSuperficie } from "@/features/admin/operaciones/types/operaciones.types";

/**
 * The view models of the TRANSVERSAL summary of the administration area.
 *
 * They are the 1:1 mirror of the backend `ResumenOperativoOut`
 * (`modules/administracion/presentation/schemas/admin_resumen_schemas.py`).
 *
 * No business rule lives here: a figure, an issue and a drilldown are
 * DECLARED by the backend and never derived in the browser
 * (`00-contrato-global-de-apply.md`, Hard Prohibitions).
 */

/** A figure of the summary. */
export interface ResumenMetrica {
  /** The stable code of the figure. */
  codigo: string;
  /** The name of the figure, in the words of the operator. */
  etiqueta: string;
  /** What the figure answers. */
  descripcion: string;
  /** The value the SERVER calculated. */
  valor: number;
}

/**
 * The authorized action that resolves an issue.
 *
 * `href` is the FILTERED operational view that the backend published: the
 * browser never builds a route and never invents a filter.
 */
export interface ResumenAccion {
  codigo: string;
  etiqueta: string;
  href: string;
}

/** A visible problem of the edition and the action that resolves it. */
export interface ResumenIncidencia {
  codigo: string;
  etiqueta: string;
  descripcion: string;
  /** How many records the issue covers. */
  cantidad: number;
  accion: ResumenAccion;
}

/** The summary of ONE edition. */
export interface ResumenOperativo {
  edicion_id: string;
  edicion_nombre: string;
  edicion_estado: string;
  metricas: ResumenMetrica[];
  incidencias: ResumenIncidencia[];
}

/** The state of the summary surface. */
export type EstadoResumenAdmin = EstadoSuperficie<ResumenOperativo>;
