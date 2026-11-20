import type { ComprarCuposIn } from "../schemas/compra-cupos.schema";
import type {
  EquipoIn,
  InscripcionInicialIn,
} from "../schemas/inscripcion.schema";
import type { ParticipanteAsignarIn } from "../schemas/pool.schema";

/**
 * The payloads of the registration area.
 *
 * The payload is built HERE, in the mutation hook's boundary, and never in a
 * component: the component knows WHAT the visitor chose, this module knows
 * HOW it travels.
 *
 * The rules (contract/next-app-architecture-contract.md §5 ·
 * salesianos-api-data "Build payloads in mutation hooks"):
 *
 * - `undefined` means "not sent": a field the visitor did not touch does not
 *   travel;
 * - `null` clears a nullable field, and ONLY a nullable one;
 * - no field that the wire does not declare is ever sent;
 * - the browser never computes a business value: no price, no amount, no
 *   capacity, no eligibility and no payment state are added here.
 */

/** The arguments of the alta, as the wizard knows them. */
export interface SolicitudAlta {
  edicion_id: string;
  paquete_id: string;
  /** The cohort that the visitor selected explicitly. */
  promocion_id: string;
  /** The number of cupos that the registration buys. */
  cantidad: number;
  /**
   * The secondary cohort of a fused registration.
   *
   * It is OPTIONAL and it is DESCRIPTIVE: it names the visible label of a
   * fused cohort and it never changes the band, the cupos, the payment, the
   * team or the eligibility.
   */
  fusion_promocion_id?: string | null;
  /**
   * The version of the price that the quotation resolved.
   *
   * It travels ONLY when a quotation exists: it is the CONCURRENCY TOKEN
   * that lets the server detect a price that moved in between. It is NOT a
   * price and NOT a total: those belong to the server (`RN-C02`).
   */
  cotizacion_version?: number | null;
  equipos: readonly { disciplina_id: string; nombre: string }[];
}

/**
 * The CREATE payload of the alta (`RT-IN-14`).
 *
 * The responsible does NOT travel: the server resolves it from the
 * authenticated account (`RN-U04`). The price does NOT travel either: the
 * server resolves it against the catalogue in force (`RN-C02`).
 *
 * ## What travels about the money
 *
 * ONLY the quantity (the decision of the visitor) and, when a quotation
 * exists, its version (the token of the concurrency check). The unit price
 * and the total NEVER travel as the truth of the purchase: the server
 * resolves them again against the catalogue in force, and it answers 409
 * when the price moved after the quotation.
 *
 * ## What travels about the band
 *
 * NOTHING: the client does not send the competitive band of the teams. The
 * band is DERIVED by the server from the cohort that the visitor selected
 * (`RN-C02`, `QA-K01`).
 */
export function construirPayloadAlta(
  solicitud: SolicitudAlta,
): InscripcionInicialIn {
  const equipos: EquipoIn[] = solicitud.equipos.map((equipo) => ({
    disciplina_id: equipo.disciplina_id,
    nombre: equipo.nombre,
  }));

  const payload: InscripcionInicialIn = {
    edicion_id: solicitud.edicion_id,
    paquete_id: solicitud.paquete_id,
    promocion_id: solicitud.promocion_id,
    cantidad: solicitud.cantidad,
    equipos,
  };

  /**
   * `undefined` means "not sent" and `null` clears a nullable field. The
   * secondary cohort is nullable, so an EMPTY selection travels as `null`
   * and a selection that was never touched travels as nothing.
   *
   * An EMPTY STRING is the "Sin fusión" option of the select, so it is
   * normalized to `null`: an empty identifier never travels.
   */
  if (solicitud.fusion_promocion_id !== undefined) {
    payload.fusion_promocion_id = solicitud.fusion_promocion_id || null;
  }

  if (solicitud.cotizacion_version !== undefined) {
    payload.cotizacion_version = solicitud.cotizacion_version;
  }

  return payload;
}

/** The arguments of the assignment of a participant (`RT-IN-05`). */
export interface SolicitudParticipante {
  /** The person of the register. */
  persona_id?: string;
  /** The type of the document, when the person is resolved by document. */
  tipo_documento?: string;
  /** The number of the document, when the person is resolved by document. */
  numero_documento?: string;
  /** The destination team inside the registration. */
  equipo_id: string;
  /** The role of the person in the team. */
  rol?: string;
  /**
   * The participation that is withdrawn to free its cupo: the MOVEMENT of
   * `FL-05` step 4.
   */
  reemplaza_participacion_id?: string;
}

/**
 * The CREATE payload of the assignment (or movement) of a participant.
 *
 * The person travels EITHER by identifier OR by document, never by both and
 * never by none: the server verifies the exclusive identification and answers
 * 422 when it is ambiguous.
 *
 * The number of cupos does NOT travel: a cupo is unitary and the server
 * assigns it (`RN-I03`).
 */
export function construirPayloadParticipante(
  solicitud: SolicitudParticipante,
): ParticipanteAsignarIn {
  const payload: ParticipanteAsignarIn = {
    equipo_id: solicitud.equipo_id,
  };

  if (solicitud.persona_id) {
    payload.persona_id = solicitud.persona_id;
  }

  if (solicitud.tipo_documento && solicitud.numero_documento) {
    payload.tipo_documento = solicitud.tipo_documento;
    payload.numero_documento = solicitud.numero_documento;
  }

  if (solicitud.rol) {
    payload.rol = solicitud.rol;
  }

  if (solicitud.reemplaza_participacion_id) {
    payload.reemplaza_participacion_id = solicitud.reemplaza_participacion_id;
  }

  return payload;
}

/**
 * The CREATE payload of the purchase of extra cupos (`RT-CM-01`).
 *
 * The amount does NOT travel: the price is resolved by the server against
 * the catalogue in force (`RN-C02`).
 */
export function construirPayloadCompraCupos(cantidad: number): ComprarCuposIn {
  return { cantidad };
}
