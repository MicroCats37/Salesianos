/**
 * The payloads of the SENSITIVE actions of the administration area.
 *
 * ## Why the payload is built HERE and not in the component
 *
 * A component NEVER writes a field of the wire (`salesianos-api-data`): the
 * mapping lives in the feature layer, so the same action cannot be sent in
 * two different shapes from two different screens.
 *
 * ## The two rules of every payload of this area
 *
 * 1. **The REASON travels.** A sensitive action of the administration is
 *    audited: the reason the operator writes is part of the command. A
 *    payload without a reason is not a payload of this area.
 * 2. **The VERSION travels when the backend publishes one.** The version is
 *    the token of the optimistic concurrency: the backend rejects a command
 *    over a stale record and the frontend NEVER decides that a record is
 *    fresh.
 *
 * ## What these payloads are NOT
 *
 * The wire schema of these actions does NOT exist yet: the routes that would
 * carry them (`RT-PG-05` and the administrative withdrawal) are not
 * registered in the backend. These builders are therefore the SEAM of the
 * contract: they declare the fields that the ledger and the plan require and
 * they are the ONE place to reconcile them with the schema that the backend
 * will publish (`A0-API04-01`).
 */

/** The command of the administrative withdrawal of a participant. */
export interface PayloadRetirarParticipanteAdmin {
  /** The registration the participation belongs to. */
  inscripcion_id: string;
  /** The participation that is withdrawn. */
  participacion_id: string;
  /** The audited reason. It is REQUIRED: the action frees a cupo. */
  motivo: string;
  /** The version of the record, when the backend publishes one. */
  version?: string;
}

/**
 * Builds the command of the withdrawal of a participant.
 *
 * The effect is declared by the plan: "Retirar participante libera su cupo en
 * esta inscripción; no genera devolución" (`frontend/04` §4). The reason is
 * not optional: the action is audited.
 */
export function payloadRetirarParticipanteAdmin(entrada: {
  inscripcion_id: string;
  participacion_id: string;
  motivo: string;
  version?: string;
}): PayloadRetirarParticipanteAdmin {
  const payload: PayloadRetirarParticipanteAdmin = {
    inscripcion_id: entrada.inscripcion_id,
    participacion_id: entrada.participacion_id,
    motivo: entrada.motivo.trim(),
  };

  if (entrada.version !== undefined) {
    payload.version = entrada.version;
  }

  return payload;
}

/** The command of the manual approval of a payment. */
export interface PayloadAprobarPagoManualAdmin {
  /** The payment order that is confirmed. */
  orden_pago_id: string;
  /** The amount, EXACTLY as the backend published it. A string, never a number. */
  monto: string;
  /** The ISO-4217 code of the currency. */
  moneda: string;
  /** The audited reason. It is REQUIRED: the action enables rights. */
  motivo: string;
  /** The version of the record, when the backend publishes one. */
  version?: string;
}

/**
 * Builds the command of the manual approval of a payment.
 *
 * The amount is NOT calculated: the browser sends the amount the server
 * published (`FR-08` §2.4) and the backend freezes the one it accepts.
 */
export function payloadAprobarPagoManualAdmin(entrada: {
  orden_pago_id: string;
  monto: string;
  moneda: string;
  motivo: string;
  version?: string;
}): PayloadAprobarPagoManualAdmin {
  const payload: PayloadAprobarPagoManualAdmin = {
    orden_pago_id: entrada.orden_pago_id,
    monto: entrada.monto,
    moneda: entrada.moneda,
    motivo: entrada.motivo.trim(),
  };

  if (entrada.version !== undefined) {
    payload.version = entrada.version;
  }

  return payload;
}
