import type {
  EstadoDeclarado,
  RolOperativo,
  Veredicto,
} from "../types/operaciones.types";

/**
 * The ADAPTER that resolves the visual bucket of a verdict.
 *
 * `D-UI01-02`: the bucket travels WITH the verdict. A component NEVER
 * branches on a business code, because the catalogue of public codes is not
 * closed and a component that decided what a code means would break with the
 * next code the backend catalogues (`SH-03` §6).
 *
 * The codes below are the FROZEN vocabulary of the operator verdict of the
 * target backend:
 * `Aplicacion/backend/modules/pagos/domain/constants.py` -> `EstadoOperativoPago`
 * (packet FND-04, freeze `FREEZE-CM-1.0.0`) with its public descriptions in
 * `DESCRIPCIONES_ESTADO_OPERATIVO`. `EstadoOperativoPagoService` is its ONLY
 * owner: the client never recomputes the verdict.
 *
 * The map is PRESENTATIONAL. It decides how a verdict is painted, never what
 * the verdict IS. The label and the explanation always come from the backend.
 *
 * The vocabulary of the OTHER domains of this area (the state of a team, of a
 * registration and of a participation) is NOT frozen yet: their presenters do
 * not exist in the target backend (`A0-UI04-03`). A code that is not in the
 * map above renders NEUTRALLY: the client never invents a semantic it was not
 * told, and it never derives a verdict from the raw fields of the record.
 */
const ROL_POR_CODIGO_OPERATIVO: Record<string, RolOperativo> = {
  /** The payment is confirmed, evidenced and dated. */
  PAGADA: "confirmado",
  /** The money arrived but the purchase is not recorded as paid. */
  PAGADA_SIN_LIQUIDAR: "atencion",
  /** The payment is recorded but there is no verifiable evidence. */
  PAGADA_SIN_EVIDENCIA: "atencion",
  /** The payment is confirmed and evidenced but it has no date. */
  PAGADA_SIN_FECHA: "atencion",
  /** The payment has not happened yet. */
  PENDIENTE: "pendiente",
  /** The purchase does not have a payment order yet. */
  SIN_ORDEN: "pendiente",
  /** The order or the purchase were cancelled. */
  CANCELADA: "rechazado",
  /** The order expired. */
  VENCIDA: "rechazado",
};

/**
 * The visual bucket of a code of the operator verdict.
 *
 * An unknown code is rendered NEUTRALLY: the client never invents a semantic
 * it was not told (`SH-01` §3.2 · `GOV-02-RB-06`).
 */
export function rolOperativoDesdeCodigo(codigo: string): RolOperativo {
  return ROL_POR_CODIGO_OPERATIVO[codigo] ?? "desconocido";
}

/**
 * The verdict of the view, from the fact that the backend published.
 *
 * This is the ONLY place where the wire becomes a verdict: the `estado` is
 * copied VERBATIM (the code, the label and the explanation of the backend) and
 * the `rol` is the VISUAL bucket that the adapter decides. The two travel
 * together so that the label and the colour can never disagree
 * (`D-UI04-03`).
 *
 * The browser NEVER crosses the raw fields of the record to decide what a
 * verdict is (`GOV-02-RB-06a`): a payment is not "pending" because the
 * purchase is pending AND the order is pending AND the attempt failed.
 */
export function veredictoDesdeEstadoOperativo(
  estado: EstadoDeclarado,
): Veredicto {
  return {
    estado,
    rol: rolOperativoDesdeCodigo(estado.codigo),
  };
}

/**
 * The codes of the operator verdict that this area publishes as filters.
 *
 * The list is the frozen vocabulary of `EstadoOperativoPago` and it is the
 * `estado_operativo` filter of `RT-PG-04`, which is a FROZEN OBLIGATION of
 * the administration payments interface (`GOV-02-RB-06b`).
 */
export const CODIGOS_ESTADO_OPERATIVO_PAGO: readonly {
  codigo: string;
  etiqueta: string;
  descripcion: string;
}[] = [
  {
    codigo: "SIN_ORDEN",
    etiqueta: "Sin orden",
    descripcion: "La compra todavía no tiene una orden de pago.",
  },
  {
    codigo: "PAGADA",
    etiqueta: "Pagada",
    descripcion: "El pago está confirmado y la compra consta como pagada.",
  },
  {
    codigo: "PAGADA_SIN_LIQUIDAR",
    etiqueta: "Pagada sin liquidar",
    descripcion:
      "El pago está confirmado y la compra todavía no figura como pagada.",
  },
  {
    codigo: "PAGADA_SIN_EVIDENCIA",
    etiqueta: "Pagada sin evidencia",
    descripcion:
      "El pago figura como pagado pero no hay evidencia verificable asociada.",
  },
  {
    codigo: "PAGADA_SIN_FECHA",
    etiqueta: "Pagada sin fecha",
    descripcion:
      "El pago está confirmado y evidenciado, pero no registra fecha de pago.",
  },
  {
    codigo: "PENDIENTE",
    etiqueta: "Pendiente",
    descripcion: "El pago todavía no se ha completado.",
  },
  {
    codigo: "CANCELADA",
    etiqueta: "Cancelada",
    descripcion: "La orden de pago o la compra fueron canceladas.",
  },
  {
    codigo: "VENCIDA",
    etiqueta: "Vencida",
    descripcion: "La orden de pago venció sin completarse.",
  },
];
