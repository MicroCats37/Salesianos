"use client";

import { z } from "zod";
import { handleApiError } from "@/errors";
import { ApiQueryError } from "@/hooks/callsApi/useApiQuery";
import { api } from "@/lib/api";
import {
  type AvanceConfirmarPayload,
  AvanceConfirmarPayloadSchema,
  type AvanceEnvelope,
  AvanceEnvelopeSchema,
  type AvancePreviewEnvelope,
  AvancePreviewEnvelopeSchema,
  type CompetenciaEquipoCreatePayload,
  CompetenciaEquipoCreatePayloadSchema,
  type CompetenciaEquipoEnvelope,
  CompetenciaEquipoEnvelopeSchema,
  type CompetenciaEquipoUpdatePayload,
  CompetenciaEquipoUpdatePayloadSchema,
  type CorreccionConfirmarPayload,
  CorreccionConfirmarPayloadSchema,
  type CorreccionEnvelope,
  CorreccionEnvelopeSchema,
  type CorreccionPreviewEnvelope,
  CorreccionPreviewEnvelopeSchema,
  type CorreccionPreviewPayload,
  CorreccionPreviewPayloadSchema,
  type EncuentroByePayload,
  EncuentroByePayloadSchema,
  type EncuentroCreatePayload,
  EncuentroCreatePayloadSchema,
  type EncuentroDesenlacePayload,
  EncuentroDesenlacePayloadSchema,
  type EncuentroEnlacePayload,
  EncuentroEnlacePayloadSchema,
  type EncuentroEnvelope,
  EncuentroEnvelopeSchema,
  type EncuentroParticipantesPayload,
  EncuentroParticipantesPayloadSchema,
  type EncuentroProgramacionPayload,
  EncuentroProgramacionPayloadSchema,
  type ResultadoEncuentroPayload,
  ResultadoEncuentroPayloadSchema,
  type RondaCreatePayload,
  RondaCreatePayloadSchema,
  type RondaEnvelope,
  RondaEnvelopeSchema,
  type RondaUpdatePayload,
  RondaUpdatePayloadSchema,
} from "../schemas";

/**
 * CompetenciasComandosService — the ONLY place where the frontend writes the
 * data of the module.
 *
 * The components NEVER call `fetch` and NEVER build a URL: the hooks receive
 * the payload from here (`contract/next-app-architecture-contract.md` §4 and
 * §8).
 *
 * Two guarantees of this module:
 *
 * 1. The REQUEST body is validated against its 1:1 Zod mirror BEFORE it
 *    leaves: an exact payload is a contract, not a convention.
 * 2. The RESPONSE is validated against its 1:1 Zod mirror too: a drift
 *    fails loudly instead of rendering `undefined` deep inside a table.
 *
 * Every failure is shaped as `ApiQueryError`, so the caller can react to the
 * HTTP status (409 `RESOURCE_CHANGED` → conflict, 403 → access denied) and
 * not only to the public message of the backend.
 */

/** The public message of a drifted contract. */
const MENSAJE_CONTRATO =
  "La respuesta del servidor no coincide con el contrato de la vista de administración.";

/**
 * Send ONE command and validate its answer.
 *
 * The transport is local to this module on purpose: the shared transport of
 * the administration area only knows how to READ, and the module owns its
 * own writes.
 */
async function enviar<TEnvelope>(
  metodo: "post" | "patch",
  url: string,
  esquema: z.ZodType<TEnvelope>,
  cuerpo?: unknown,
): Promise<TEnvelope> {
  try {
    const respuesta = await api.request({ method: metodo, url, data: cuerpo });
    return esquema.parse(respuesta.data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ApiQueryError(MENSAJE_CONTRATO, undefined);
    }

    const { message, status } = handleApiError(error);
    throw new ApiQueryError(message, status);
  }
}

// ── Equipos y semillas ───────────────────────────────────────────────────────

/** Register a team in the bracket with its MANUAL order. */
export async function crearEquipoCompetencia(
  competenciaId: string,
  cuerpo: CompetenciaEquipoCreatePayload,
): Promise<CompetenciaEquipoEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/${competenciaId}/equipos`,
    CompetenciaEquipoEnvelopeSchema,
    CompetenciaEquipoCreatePayloadSchema.parse(cuerpo),
  );
}

/** Update the manual order or the state of a participation. */
export async function actualizarEquipoCompetencia(
  competenciaId: string,
  equipoId: string,
  cuerpo: CompetenciaEquipoUpdatePayload,
): Promise<CompetenciaEquipoEnvelope> {
  return enviar(
    "patch",
    `/administracion/competencias/${competenciaId}/equipos/${equipoId}`,
    CompetenciaEquipoEnvelopeSchema,
    CompetenciaEquipoUpdatePayloadSchema.parse(cuerpo),
  );
}

// ── Rondas ────────────────────────────────────────────────────────────────────

/** Create a round of the bracket. */
export async function crearRondaCompetencia(
  competenciaId: string,
  cuerpo: RondaCreatePayload,
): Promise<RondaEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/${competenciaId}/rondas`,
    RondaEnvelopeSchema,
    RondaCreatePayloadSchema.parse(cuerpo),
  );
}

/** Update the label or the order of a round. */
export async function actualizarRondaCompetencia(
  competenciaId: string,
  rondaId: string,
  cuerpo: RondaUpdatePayload,
): Promise<RondaEnvelope> {
  return enviar(
    "patch",
    `/administracion/competencias/${competenciaId}/rondas/${rondaId}`,
    RondaEnvelopeSchema,
    RondaUpdatePayloadSchema.parse(cuerpo),
  );
}

// ── Encuentros ───────────────────────────────────────────────────────────────

/** Create an encounter in a round of the bracket. */
export async function crearEncuentroCompetencia(
  competenciaId: string,
  cuerpo: EncuentroCreatePayload,
): Promise<EncuentroEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/${competenciaId}/encuentros`,
    EncuentroEnvelopeSchema,
    EncuentroCreatePayloadSchema.parse(cuerpo),
  );
}

/** Move the teams of the two slots of an encounter. */
export async function actualizarParticipantesEncuentro(
  encuentroId: string,
  cuerpo: EncuentroParticipantesPayload,
): Promise<EncuentroEnvelope> {
  return enviar(
    "patch",
    `/administracion/competencias/encuentros/${encuentroId}/participantes`,
    EncuentroEnvelopeSchema,
    EncuentroParticipantesPayloadSchema.parse(cuerpo),
  );
}

/** Schedule an encounter. */
export async function programarEncuentro(
  encuentroId: string,
  cuerpo: EncuentroProgramacionPayload,
): Promise<EncuentroEnvelope> {
  return enviar(
    "patch",
    `/administracion/competencias/encuentros/${encuentroId}/programacion`,
    EncuentroEnvelopeSchema,
    EncuentroProgramacionPayloadSchema.parse(cuerpo),
  );
}

/** Configure a MANUAL bye. The system NEVER chooses one by itself. */
export async function configurarByeEncuentro(
  encuentroId: string,
  cuerpo: EncuentroByePayload,
): Promise<EncuentroEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/encuentros/${encuentroId}/bye`,
    EncuentroEnvelopeSchema,
    EncuentroByePayloadSchema.parse(cuerpo),
  );
}

/** Link an encounter to the next encounter of the bracket. */
export async function enlazarEncuentro(
  encuentroId: string,
  cuerpo: EncuentroEnlacePayload,
): Promise<EncuentroEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/encuentros/${encuentroId}/enlace`,
    EncuentroEnvelopeSchema,
    EncuentroEnlacePayloadSchema.parse(cuerpo),
  );
}

/** Remove the link of an encounter (it needs an audited motive). */
export async function desenlazarEncuentro(
  encuentroId: string,
  cuerpo: EncuentroDesenlacePayload,
): Promise<EncuentroEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/encuentros/${encuentroId}/desenlace`,
    EncuentroEnvelopeSchema,
    EncuentroDesenlacePayloadSchema.parse(cuerpo),
  );
}

// ── Resultado, avance y corrección ───────────────────────────────────────────

/** Register the AUTHORITATIVE result of an encounter. */
export async function registrarResultadoEncuentro(
  encuentroId: string,
  cuerpo: ResultadoEncuentroPayload,
): Promise<EncuentroEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/encuentros/${encuentroId}/resultado`,
    EncuentroEnvelopeSchema,
    ResultadoEncuentroPayloadSchema.parse(cuerpo),
  );
}

/** The proposal of the propagation of the winner. It NEVER writes. */
export async function previsualizarAvance(
  encuentroId: string,
): Promise<AvancePreviewEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/encuentros/${encuentroId}/avance/preview`,
    AvancePreviewEnvelopeSchema,
  );
}

/** Place the winner in the linked slot of the next encounter. */
export async function confirmarAvance(
  encuentroId: string,
  cuerpo: AvanceConfirmarPayload,
): Promise<AvanceEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/encuentros/${encuentroId}/avance/confirm`,
    AvanceEnvelopeSchema,
    AvanceConfirmarPayloadSchema.parse(cuerpo),
  );
}

/** The impact analysis of the correction of the winner. It NEVER writes. */
export async function previsualizarCorreccion(
  encuentroId: string,
  cuerpo: CorreccionPreviewPayload,
): Promise<CorreccionPreviewEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/encuentros/${encuentroId}/correccion/preview`,
    CorreccionPreviewEnvelopeSchema,
    CorreccionPreviewPayloadSchema.parse(cuerpo),
  );
}

/** Correct the authoritative winner of an encounter. */
export async function confirmarCorreccion(
  encuentroId: string,
  cuerpo: CorreccionConfirmarPayload,
): Promise<CorreccionEnvelope> {
  return enviar(
    "post",
    `/administracion/competencias/encuentros/${encuentroId}/correccion/confirm`,
    CorreccionEnvelopeSchema,
    CorreccionConfirmarPayloadSchema.parse(cuerpo),
  );
}
