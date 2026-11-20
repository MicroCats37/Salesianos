import { z } from "zod";
import {
  causaSchema,
  envelopeAdminPaginado,
} from "@/features/admin/operaciones/schemas/operaciones.schema";
import type {
  EventoDeHistorialAdminOut,
  ParticipacionAdminOut,
  ParticipanteAdminOut,
} from "../types/participantes-admin.types";

/**
 * The Zod mirrors of the ADMINISTRATION OF THE PARTICIPANTS.
 *
 * ## What they mirror
 *
 * The presenters the ledger declares (`RT-IN-11` ->
 * `AdminParticipanteListaPresenter` and `RT-ID-07` ->
 * `AdminPersonaListaPresenter`), with the shapes of the plan
 * (`contratos/01`, admin).
 *
 * ## What they are NOT
 *
 * They are NOT the mirror of a live wrapper: `AdminParticipanteController`
 * and `AdminPersonaController` are NOT registered in
 * `Aplicacion/backend/config/api.py`, so these routes do NOT exist. They are
 * the SEAM of the contract (`A0-API04-05`).
 *
 * ## The conflict of a participation
 *
 * A conflict is DECLARED by the backend with its reason: the browser never
 * decides that two participations collide (`GOV-02-RB-04b`). The conflict is
 * a CAUSE (`{codigo, mensaje}`) and it travels with its prose.
 */

/** A reference to a record of the area. */
export const referenciaParticipanteSchema = z.object({
  id: z.string().min(1),
  nombre: z.string(),
});

/** A participation of a person, with its event, team and discipline. */
export const participacionAdminSchema = z.object({
  id: z.string().min(1),
  evento: referenciaParticipanteSchema,
  equipo: referenciaParticipanteSchema,
  disciplina: referenciaParticipanteSchema,
  rol: z.string().min(1),
  estado: z.string().min(1),
  conflicto: causaSchema.nullable(),
});

/** An event of the history of a person. */
export const eventoDeHistorialAdminSchema = z.object({
  occurred_at: z.string().min(1),
  tipo: z.string().min(1),
  descripcion: z.string(),
});

/** A person of the administrative search, with her participations. */
export const participanteAdminSchema = z.object({
  id: z.string().min(1),
  nombre: z.string(),
  documento: z.string(),
  participaciones: z.array(participacionAdminSchema),
  historial: z.array(eventoDeHistorialAdminSchema),
});

/** The envelope of the administrative list of the participants (`RT-IN-11`). */
export const listaParticipantesAdminEnvelope = envelopeAdminPaginado(
  participanteAdminSchema,
);

// ── La proyección del wire al modelo de la vista ─────────────────────────────

/** The wire of a participation. */
export type ParticipacionAdminWire = z.infer<typeof participacionAdminSchema>;

/** The wire of an event of the history. */
export type EventoDeHistorialAdminWire = z.infer<
  typeof eventoDeHistorialAdminSchema
>;

/** The wire of a person of the administrative search. */
export type ParticipanteAdminWire = z.infer<typeof participanteAdminSchema>;

/** A participation, as the view expects it. */
export function participacionAdminDesdeWire(
  participacion: ParticipacionAdminWire,
): ParticipacionAdminOut {
  return participacion;
}

/** An event of the history, as the view expects it. */
export function eventoDeHistorialAdminDesdeWire(
  evento: EventoDeHistorialAdminWire,
): EventoDeHistorialAdminOut {
  return evento;
}

/** A person of the administrative search, as the view expects it. */
export function participanteAdminDesdeWire(
  persona: ParticipanteAdminWire,
): ParticipanteAdminOut {
  return {
    id: persona.id,
    nombre: persona.nombre,
    documento: persona.documento,
    participaciones: persona.participaciones.map(participacionAdminDesdeWire),
    historial: persona.historial.map(eventoDeHistorialAdminDesdeWire),
  };
}
