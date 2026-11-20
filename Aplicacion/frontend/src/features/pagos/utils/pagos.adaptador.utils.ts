import type {
  EstadoActivacion,
  RolActivacion,
  VeredictoActivacion,
} from "../types/pagos.types";

/**
 * The ADAPTER that resolves the visual bucket of the activation verdict.
 *
 * `D-UI01-02` / `D-UI04-03`: the bucket travels WITH the verdict. A component
 * NEVER branches on a business code, because the catalogue of public codes is
 * not closed and a component that decided what a code means would break with
 * the next code the backend catalogues (`SH-03` §6).
 *
 * The codes below are the vocabulary of the activation verdict of the target
 * backend: `Aplicacion/backend/modules/pagos/domain/constants.py` ->
 * `EstadoActivacionPago` (packet XCT-03, freeze `FREEZE-CM-1.0.0`) with its
 * public descriptions in `DESCRIPCIONES_ESTADO_ACTIVACION`.
 * `EstadoOperativoPagoService` is its ONLY owner: the client never recomputes
 * the verdict.
 *
 * The map is PRESENTATIONAL. It decides how a verdict is painted, never what
 * the verdict IS. The label and the explanation always come from the backend.
 */
const ROL_POR_CODIGO_ACTIVACION: Record<string, RolActivacion> = {
  /** The right was enabled. */
  ACTIVADA: "confirmado",
  /** The activation is registered and still unresolved. */
  PENDIENTE: "pendiente",
  /** An activation attempt is reserved right now. */
  EN_CURSO: "verificando",
  /** The attempt failed: the payment is kept and the retry is safe. */
  FALLIDA: "atencion",
  /** There is no activation registered for the purchase. */
  SIN_ACTIVACION: "sin-confirmar",
};

/**
 * The visual bucket of a code of the activation verdict.
 *
 * An unknown code is rendered NEUTRALLY: the client never invents a semantic
 * it was not told (`SH-01` §3.2).
 */
export function rolActivacionDesdeCodigo(codigo: string): RolActivacion {
  return ROL_POR_CODIGO_ACTIVACION[codigo] ?? "desconocido";
}

/**
 * The verdict of the view, from the fact that the backend published.
 *
 * This is the ONLY place where the wire becomes a verdict: the `estado` is
 * copied VERBATIM (the code, the label and the explanation of the backend) and
 * the `rol` is the VISUAL bucket that the adapter decides. The two travel
 * together so that the label and the colour can never disagree.
 */
export function veredictoActivacionDesdeEstado(
  estado: EstadoActivacion,
): VeredictoActivacion {
  return {
    estado,
    rol: rolActivacionDesdeCodigo(estado.codigo),
  };
}

/**
 * The codes of the activation verdict, as the backend names them.
 *
 * The list mirrors `EstadoActivacionPago` of the target backend. It exists so
 * that a filter or a legend has ONE source of truth on this side, and it is
 * NOT a rule: the meaning of a code is always the backend's wording.
 */
export const CODIGOS_ESTADO_ACTIVACION_PAGO: readonly string[] = [
  "SIN_ACTIVACION",
  "ACTIVADA",
  "PENDIENTE",
  "EN_CURSO",
  "FALLIDA",
];
