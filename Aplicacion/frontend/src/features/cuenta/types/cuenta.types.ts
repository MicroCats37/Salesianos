/**
 * The view models of the account area.
 *
 * They are TYPES, not Zod schemas, and they are NOT a mirror of a presenter.
 * The reason is a FACT of the backend, not an omission: the wrappers of the
 * account (`RT-ID-04` `MiCuentaOut`, `RT-ID-05` the list of purchases,
 * `RT-ID-06` the detail of a purchase) have NO registered route in
 * `Aplicacion/backend/config/api.py` and NO frozen presenter to mirror. A Zod
 * mirror of a wrapper that does not exist would be an INVENTED contract.
 *
 * These types therefore describe the SHAPE the views expect, and they are the
 * seam where the real wrappers will land: when the backend owns those routes,
 * the mirror arrives next to these types and the views keep consuming the same
 * shape.
 *
 * No business rule lives here. A price, an eligibility, a capacity, a
 * payment state, a stock and a permission are DECLARED by the presenter and
 * never derived in the browser (`00-contrato-global-de-apply.md`, Hard
 * Prohibitions; `SH-01` T-03).
 */

/**
 * The verdict of the backend.
 *
 * It mirrors `EstadoOperativo` (`FREEZE-ENV-1.0.0` §5): the machine code, the
 * label in plain language and the explanation. The frontend NEVER rewrites
 * the label and NEVER shows the code (`SH-03` §6).
 */
export interface EstadoOperativo {
  codigo: string;
  etiqueta: string;
  descripcion: string;
}

/**
 * The visual bucket of a verdict.
 *
 * `SH-01` §3.2: the colour is a PRESENTATIONAL bucket, never the meaning.
 * The label and the meaning always come from the backend. The bucket is
 * resolved by the ADAPTER (the provisional fixture today, the real service in
 * API-01), never by the component: the component only receives the bucket,
 * so it never branches on a business code.
 */
export type RolVeredicto =
  | "confirmado"
  | "pendiente"
  | "verificando"
  | "atencion"
  | "sin-confirmar"
  | "rechazado"
  | "desconocido";

/**
 * A verdict with its visual bucket.
 *
 * `estado` is what the backend says; `rol` is how the adapter decided to
 * paint it. Both travel together so the label and the colour can never
 * disagree.
 */
export interface Veredicto {
  estado: EstadoOperativo;
  rol: RolVeredicto;
}

/**
 * Where a purchase comes from.
 *
 * The three origins of the plan (`frontend/03`): a registration, a pass or a
 * store product. They are never mixed in one checkout (`GOV-02-RB-02a`).
 */
export type OrigenCompra = "INSCRIPCION" | "PASE" | "MARKETPLACE";

/** A purchase of the account, as the list shows it. */
export interface CompraResumen {
  id: string;
  origen: OrigenCompra;
  concepto: string;
  /** The amount as the backend sends it: a string, never a number. */
  monto: string;
  moneda: string;
  /** The date of the purchase, already formatted by the presenter. */
  fecha: string;
  veredicto: Veredicto;
}

/** A purchase of the account, as the detail shows it. */
export interface CompraDetalle extends CompraResumen {
  /** What the purchase granted. The code is never rendered. */
  derechos: { codigo: string; etiqueta: string }[];
  /** Where the buyer goes next: the module that owns the purchase. */
  ruta_origen: string | null;
}

/** A registration of the responsible, as the list shows it. */
export interface InscripcionResumen {
  id: string;
  edicion: string;
  paquete: string;
  equipos: number;
  personas: number;
  /** The cupos the backend still reports as available. */
  cupos_disponibles: number;
  veredicto: Veredicto;
  /**
   * The next permitted step.
   *
   * The LABEL is the backend's wording and the destination is a route of this
   * product. The client never decides WHICH step comes next: it draws the
   * one the presenter named.
   */
  siguiente_accion: { etiqueta: string; href: string } | null;
}

/** The counters of the account hub. */
export interface ResumenCuenta {
  inscripciones: number;
  compras: number;
}

/**
 * The one pagination shape of the frozen envelope
 * (`FREEZE-ENV-1.0.0` §4.3): `items/total/page/page_size/total_pages`.
 */
export interface Pagina<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * The state a route is in.
 *
 * The default of every view is `sin-datos`: the service is not connected
 * yet, and the view says so instead of drawing a list that does not exist.
 */
export type EstadoVista = "sin-datos" | "listo" | "sin-permiso" | "error";
