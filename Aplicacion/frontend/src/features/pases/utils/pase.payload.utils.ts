import type {
  AsignacionPaseData,
  CompradorPaseData,
} from "../schemas/comprador-pase.schema";
import type {
  AsignarBeneficiarioDatos,
  ComprarPaseDatos,
} from "../schemas/pase.schema";

/**
 * The mapping between the FORM and the WIRE.
 *
 * There are TWO mappings and they never mix: the purchase is a CREATE and
 * the assignment is a CREATE too, so neither of them sends an update diff.
 * A field that is not touched is OMITTED (`undefined`), never sent as `null`
 * and never invented.
 *
 * The mapping lives here, OUTSIDE the component: a component never spells a
 * field of the wire.
 */

/** What the checkout of a batch needs to build its payload. */
export interface SolicitudCompraPase {
  /** The pass that is being bought. */
  pase_id: string;
  /** The amount of passes. */
  cantidad: number;
  /** What the buyer typed. */
  datos: CompradorPaseData;
}

/**
 * The payload of the purchase (`ComprarPaseIn`).
 *
 * It admits NO amount: the price is resolved and frozen by the server
 * against the current catalogue (`RN-C02`), and the quantity limit is a rule
 * of the domain that answers 422 (`CANTIDAD_INVALIDA`).
 */
export function aPayloadComprarPase(
  solicitud: SolicitudCompraPase,
): ComprarPaseDatos {
  return {
    pase_id: solicitud.pase_id,
    cantidad: solicitud.cantidad,
    tipo_documento: solicitud.datos.tipoDocumento,
    numero_documento: solicitud.datos.numeroDocumento,
    nombres: solicitud.datos.nombres,
    apellidos: solicitud.datos.apellidos,
    contacto_email: solicitud.datos.contactoEmail,
  };
}

/**
 * The payload of the assignment (`AsignarBeneficiarioIn`).
 *
 * The person may arrive by IDENTIFIER or by DOCUMENT. This form resolves by
 * document, so `persona_id` is NOT sent: it is `undefined` and the
 * serializer omits it instead of sending a `null` the backend would read as
 * an explicit clear.
 */
export function aPayloadAsignarBeneficiario(
  datos: AsignacionPaseData,
): AsignarBeneficiarioDatos {
  return {
    persona_id: undefined,
    tipo_documento: datos.tipoDocumento,
    numero_documento: datos.numeroDocumento,
    nombres: datos.nombres,
    apellidos: datos.apellidos,
    motivo: datos.motivo,
  };
}
