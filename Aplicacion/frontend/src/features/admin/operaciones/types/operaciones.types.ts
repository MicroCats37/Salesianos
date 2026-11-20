import type { ReactNode } from "react";

/**
 * The view models of the OPERATIONAL layer of the administration area.
 *
 * They are TYPES, not Zod mirrors: the six presenters of this area
 * (`AdminInscripcionListaPresenter`, `AdminInscripcionDetallePresenter`,
 * `AdminEquipoListaPresenter`, `AdminEquipoDetallePresenter`,
 * `AdminParticipanteListaPresenter` and `AdminPagoPresenter`) do NOT exist in
 * `Aplicacion/backend`, and their routes are NOT registered in
 * `Aplicacion/backend/config/api.py`. A Zod mirror of a presenter that does
 * not exist would be an INVENTED contract (`D-UI01-03`).
 *
 * These types therefore describe the SHAPE the views expect, and they are the
 * seam where the real wrappers will land in API-04.
 *
 * No business rule lives here. A price, an eligibility, a capacity, a payment
 * state, a stock, a right and a permission are DECLARED by the presenter and
 * never derived in the browser (`00-contrato-global-de-apply.md`, Hard
 * Prohibitions; `SH-01` T-03).
 */

/**
 * The visual bucket of an operational verdict.
 *
 * `SH-01` §3.2: the colour is a PRESENTATIONAL bucket, never the meaning. The
 * label and the meaning always come from the backend. The bucket travels WITH
 * the verdict (`D-UI01-02`): a component never branches on a business code.
 */
export type RolOperativo =
  | "confirmado"
  | "pendiente"
  | "atencion"
  | "sin-confirmar"
  | "incompleto"
  | "rechazado"
  | "desconocido";

/**
 * A fact of the backend with its own wording.
 *
 * It mirrors `EstadoOperativo` (`FREEZE-ENV-1.0.0` §5): the machine code, the
 * label in plain language and the explanation. The frontend NEVER rewrites
 * the label and NEVER shows the code (`SH-03` §6).
 */
export interface EstadoDeclarado {
  codigo: string;
  etiqueta: string;
  descripcion: string;
}

/**
 * A verdict with its visual bucket.
 *
 * `estado` is what the backend says; `rol` is how the adapter decided to paint
 * it. Both travel together so the label and the colour can never disagree.
 */
export interface Veredicto {
  estado: EstadoDeclarado;
  rol: RolOperativo;
}

/**
 * An action the operator can take, and the code the presenter published for it.
 *
 * `acciones_disponibles` is a PROJECTION, not authorisation (`contratos/01`
 * §6 · `GOV-02-RB-03d` · `GOV-02-RB-06c`): the interface may use it to hide
 * an affordance, but the 403 of the backend remains the control. The LABEL is
 * the vocabulary of this interface, never a backend code.
 */
export interface AccionOperativa {
  /** The code the presenter publishes in `acciones_disponibles`. */
  codigo: string;
  /** The name of the action, in the words of the operator. */
  etiqueta: string;
  /** The destination of the action, when it has one. */
  href?: string;
}

/**
 * The THREE cupos of a record, as the server publishes them.
 *
 * `GOV-02-RB-04a`: the maximum of a roster and the balance of paid cupos are
 * DIFFERENT numbers and they are never presented as one. The browser prints
 * the three numbers and never subtracts them.
 */
export interface CuposOperativosOut {
  /** The cupos the record acquired (the ones it paid for). */
  adquiridos: number;
  /** The cupos that are already assigned to a participation. */
  asignados: number;
  /** The cupos that are still available. */
  disponibles: number;
}

/**
 * The priority of a column of an operational list.
 *
 * - `1` — always visible in the table (768 and above).
 * - `2` — visible from 1024.
 * - `3` — visible from 1280.
 *
 * The rule exists so that the SAME list answers at every width without
 * losing a column of meaning (`SH-02` · `GOV-02-RB-04`).
 */
export type PrioridadColumna = 1 | 2 | 3;

/** One column of an operational list. */
export interface ColumnaOperativa {
  /** The stable key of the column. */
  key: string;
  /** The name of the column, in sentence case. */
  label: string;
  /** The priority of the column. It defaults to `1`. */
  prioridad?: PrioridadColumna;
  /** Whether the column holds a quantity: it aligns right with tabular figures. */
  numerico?: boolean;
  /** Whether the column holds an identifier: it wears the monospace face. */
  identificador?: boolean;
  /** Whether the column is the title of the row (exactly one per list). */
  titular?: boolean;
}

/** One row of an operational list. */
export interface FilaOperativa {
  /**
   * The stable key of the row.
   *
   * It is unique and stable: the React key of a row is never the index
   * (`GOV-02-RB-06d`).
   */
  id: string;
  /** The content of each cell, keyed by the key of the column. */
  celdas: Record<string, ReactNode>;
}

/**
 * The state a surface of the administration area is in.
 *
 * The default of every view is `sin-datos`: the route is NOT connected yet,
 * and the view says so instead of drawing a list that does not exist
 * (`D-UI03-02` · `SH-03` S-02).
 */
export type EstadoSuperficie<T> =
  | { estado: "sin-datos" }
  | { estado: "cargando" }
  | { estado: "error"; mensaje: string }
  | { estado: "sin-permiso"; mensaje?: string }
  | { estado: "listo"; datos: T };

/**
 * The ONE pagination shape of the frozen envelope (`FREEZE-ENV-1.0.0` §4.3):
 * `items/total/page/page_size/total_pages`. The browser never computes it.
 */
export interface PaginaOperativa<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** One option of a filter. */
export interface OpcionFiltro {
  valor: string;
  etiqueta: string;
}

/**
 * One filter of an operational list.
 *
 * The filters live in the URL, never in a component-local store
 * (`GOV-02-RB-03b` · `D-UI01-10`).
 */
export interface FiltroOperativo {
  /** The query parameter of the filter. */
  clave: string;
  /** The name of the filter, in the words of the operator. */
  etiqueta: string;
  /** The options of the filter. */
  opciones: OpcionFiltro[];
  /**
   * The kind of control.
   *
   * `select` is the default. `fecha` renders a native date field, which is
   * the only control that answers a range of dates without inventing a
   * vocabulary of presets.
   */
  tipo?: "select" | "fecha";
  /**
   * Why the filter has no options yet.
   *
   * A filter whose options come from a route that does not exist is shown
   * DISABLED with this reason, instead of a list of invented values.
   */
  sinOpciones?: string;
}
