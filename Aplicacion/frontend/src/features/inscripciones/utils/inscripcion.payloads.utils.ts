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
  equipos: readonly { disciplina_id: string; nombre: string }[];
}

/**
 * The CREATE payload of the alta (`RT-IN-14`).
 *
 * The responsible does NOT travel: the server resolves it from the
 * authenticated account (`RN-U04`). The price does NOT travel either: the
 * server resolves it against the catalogue in force (`RN-C02`).
 */
export function construirPayloadAlta(
  solicitud: SolicitudAlta,
): InscripcionInicialIn {
  const equipos: EquipoIn[] = solicitud.equipos.map((equipo) => ({
    disciplina_id: equipo.disciplina_id,
    nombre: equipo.nombre,
  }));

  return {
    edicion_id: solicitud.edicion_id,
    paquete_id: solicitud.paquete_id,
    equipos,
  };
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
