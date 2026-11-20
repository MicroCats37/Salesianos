import type {
  BeneficiarioPaseWire,
  CompraPasesWire,
} from "../schemas/pase.schema";
import type { BeneficiarioPase, CompraPases } from "../types/pase.types";

/**
 * The adapter between the wire of `DOM-03` and the view models.
 *
 * It does ONE thing: it resolves the LABEL of the machine codes the backend
 * publishes. The presenters of `DOM-03` publish CODES and no wording
 * (`A0-UI03-04`), and the interface never shows a code (`SH-03` §6). The
 * label travels WITH the code so the two can never disagree.
 *
 * It computes NOTHING: no amount, no count, no state. A count that the
 * server publishes is shown as it was published.
 */

/**
 * The commercial state of a batch purchase (`EstadoCompraPase`).
 *
 * `PENDIENTE` does NOT enable any pass: the assignment waits for a confirmed
 * payment (`RN-P02`).
 */
const ETIQUETA_ESTADO_COMPRA: Record<string, string> = {
  PENDIENTE: "Compra pendiente de pago",
  PAGADA: "Compra pagada",
  ANULADA: "Compra anulada",
};

/** The state of an entry right (`EstadoDerechoPase`). */
const ETIQUETA_ESTADO_DERECHO: Record<string, string> = {
  ACTIVO: "Entrada activa",
  REVOCADO: "Entrada revocada",
};

/**
 * The label of the commercial state of a purchase.
 *
 * An unknown code NEVER reaches the screen: it is a neutral label, not the
 * raw code.
 */
export function etiquetaEstadoCompra(codigo: string): string {
  return ETIQUETA_ESTADO_COMPRA[codigo] ?? "Compra no disponible";
}

/** The label of the state of an entry right. */
export function etiquetaEstadoDerecho(codigo: string): string {
  return ETIQUETA_ESTADO_DERECHO[codigo] ?? "Entrada no disponible";
}

/** One right of entry, with the label of its state. */
export function adaptarBeneficiario(
  beneficiario: BeneficiarioPaseWire,
): BeneficiarioPase {
  return {
    ...beneficiario,
    estado_etiqueta: etiquetaEstadoDerecho(beneficiario.estado),
  };
}

/**
 * The purchase of a batch, with the label of its state and the label of the
 * state of every right it carries.
 */
export function adaptarCompra(compra: CompraPasesWire): CompraPases {
  return {
    ...compra,
    estado_etiqueta: etiquetaEstadoCompra(compra.estado),
    beneficiarios: compra.beneficiarios.map(adaptarBeneficiario),
  };
}
