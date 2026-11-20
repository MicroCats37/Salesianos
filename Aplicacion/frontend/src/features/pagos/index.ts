/**
 * The payment area of the buyer (`XCT-03`).
 *
 * It owns the TYPES and the ADAPTER of the payment verdicts that the target
 * backend publishes:
 *
 * - `estado_operativo` — the operator verdict of the payment
 *   (`EstadoOperativoPago`, `FREEZE-ENV-1.0.0` §5);
 * - `estado_activacion` — the verdict of the activation of the rights, a
 *   channel SEPARATE from the first one (`EstadoActivacionPago`,
 *   `FREEZE-CM-1.0.0` §6).
 *
 * Both are published by `EstadoOperativoPagoService`, their ONLY owner. The
 * browser never crosses the sibling facts to decide what a verdict is.
 */

export { ChipPago, EstadoPagoActivacion } from "./components";
export type {
  EstadoActivacion,
  RolActivacion,
  VeredictoActivacion,
} from "./types/pagos.types";
export {
  CODIGOS_ESTADO_ACTIVACION_PAGO,
  rolActivacionDesdeCodigo,
  veredictoActivacionDesdeEstado,
} from "./utils/pagos.adaptador.utils";
