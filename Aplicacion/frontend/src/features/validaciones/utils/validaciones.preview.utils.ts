/**
 * The ADAPTER between the frozen wire and the view models of the area.
 *
 * The backend publishes the FROZEN shape of `FR-05` §3.1 and §3.2:
 * `TicketPreviewOut` and `TicketConfirmadoOut`. The components of the area
 * were drawn against the PROVISIONAL view models of `UI-05`, and this file
 * is the seam between the two.
 *
 * **IT DECIDES NOTHING.** It renames fields and it picks the BUCKET that
 * paints a verdict. Every fact — whether the credential can be redeemed, the
 * quantities, the state and the reason — comes from the server. The browser
 * never subtracts, never rounds and never guesses (`SH-01` T-03).
 *
 * **THE FIELDS THE SERVER DOES NOT PUBLISH.** The frozen preview does not
 * carry the point of control, the operator or the instant: they are NOT
 * business facts of the credential, they are the CONTEXT of the device. They
 * come from the session and from the clock of the operator, and they are
 * labelled as such.
 */

import type {
  TicketConfirmado,
  TicketPreview,
} from "../schemas/validacion.schema";
import type {
  ResultadoValidacion,
  VistaPreviaValidacion,
} from "../types/validacion.types";
import { resolverVeredicto } from "./validaciones.estados.utils";

/**
 * The context of the DEVICE, the part the frozen preview does not publish.
 */
export interface ContextoValidacion {
  /** The point of control where the operator is. */
  punto: string;
  /** The operator, as the session says it. */
  operador: string;
}

/** The code of a verdict that the server does not publish. */
const CODIGO_PERMITIDO = "VALIDACION_PERMITIDA";

/**
 * The preview of the server, as the view model of the area.
 *
 * The verdict is the one the server published: when it refuses, the reason is
 * the `motivo_codigo` and the `motivo_mensaje` of the owner, and the browser
 * never rewrites them (`SH-03` §6).
 */
export function adaptarPreview(
  datos: TicketPreview,
  contexto: ContextoValidacion,
): VistaPreviaValidacion {
  const veredicto = datos.puede_canjear
    ? resolverVeredicto(CODIGO_PERMITIDO)
    : resolverVeredicto(
        datos.motivo_codigo ?? "VEREDICTO_DESCONOCIDO",
        datos.motivo_mensaje ?? undefined,
      );

  return {
    puede_validar: datos.puede_canjear,
    veredicto,
    titular: {
      nombres: datos.titular.nombre,
      apellidos: "",
      tipo_documento: "",
      numero_documento: "",
    },
    derecho: {
      tipo: datos.tipo_derecho,
      nombre: datos.codigo,
      estado: datos.estado,
      cantidad_total: datos.cantidad_total,
      cantidad_consumida: datos.cantidad_consumida,
      cantidad_disponible: datos.cantidad_disponible,
      revocado_en: null,
    },
    punto: contexto.punto,
    operador: contexto.operador,
    instante: new Date().toISOString(),
  };
}

/**
 * The confirmed exchange, as the view model of the area.
 *
 * The instant is the one the SERVER published (`consumido_en`): it is the
 * instant of the record, not the instant of the screen.
 */
export function adaptarResultado(
  datos: TicketConfirmado,
  contexto: ContextoValidacion,
): ResultadoValidacion {
  return {
    validado: true,
    veredicto: resolverVeredicto(CODIGO_PERMITIDO),
    cantidad_consumida: datos.cantidad_consumida,
    punto: contexto.punto,
    operador: contexto.operador,
    instante: datos.consumido_en,
    repetida: datos.repetido,
  };
}
