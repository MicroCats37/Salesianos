import { z } from "zod";
import {
  cuposOperativosSchema,
  envelopeAdmin,
  envelopeAdminPaginado,
  estadoOperativoSchema,
} from "@/features/admin/operaciones/schemas/operaciones.schema";
import { veredictoDesdeEstadoOperativo } from "@/features/admin/operaciones/utils/veredicto.adapter";
import type {
  AdminEquipoDetalleOut,
  AdminEquipoListItemOut,
  CandidatoAEquipoOut,
  ParticipanteDeEquipoOut,
} from "../types/equipos-admin.types";

/**
 * The Zod mirrors of the ADMINISTRATION OF THE TEAMS.
 *
 * ## What they mirror
 *
 * The presenters the ledger declares (`RT-IN-09` ->
 * `AdminEquipoListaPresenter` and `RT-IN-10` ->
 * `AdminEquipoDetallePresenter`), with the shapes of the plan
 * (`contratos/01` §3, admin).
 *
 * ## What they are NOT
 *
 * They are NOT the mirror of a live wrapper: `AdminEquipoController` is NOT
 * registered in `Aplicacion/backend/config/api.py`, so these routes do NOT
 * exist. They are the SEAM of the contract (`A0-API04-05`).
 *
 * ## The three numbers of the roster
 *
 * `registrados`, `minimo` and `maximo` are DECLARED by the presenter and they
 * are three DIFFERENT facts: the browser prints them and NEVER compares them
 * (`contratos/01` §7). The verdict of the readiness is the
 * `estado_operativo` of the presenter and never an inference of the browser.
 */

/** A reference to a record of the area. */
export const referenciaEquipoSchema = z.object({
  id: z.string().min(1),
  nombre: z.string(),
});

/** The three numbers of the roster of a team. */
export const plantillaEquipoSchema = z.object({
  registrados: z.number().int().nonnegative(),
  minimo: z.number().int().nonnegative(),
  maximo: z.number().int().nonnegative(),
});

/** A participant of the roster of a team. */
export const participanteDeEquipoSchema = z.object({
  id: z.string().min(1),
  persona_id: z.string().min(1),
  nombre: z.string(),
  documento: z.string(),
  rol: z.string().min(1),
  estado: z.string().min(1),
});

/**
 * A candidate for a team.
 *
 * The verdict of the candidate is the BACKEND's: the browser never decides
 * that a person may enter a team nor that she may not.
 */
export const candidatoAEquipoSchema = z.object({
  id: z.string().min(1),
  persona_id: z.string().min(1),
  nombre: z.string(),
  documento: z.string(),
  estado_operativo: estadoOperativoSchema,
});

/** The team, as the administrative presenter composes it. */
export const equipoOperativoSchema = z.object({
  id: z.string().min(1),
  nombre: z.string(),
  disciplina: referenciaEquipoSchema,
  categoria: referenciaEquipoSchema,
  plantilla: plantillaEquipoSchema,
  estado_operativo: estadoOperativoSchema,
  acciones_disponibles: z.array(z.string().min(1)),
});

/** A row of the administrative list of the teams (`RT-IN-09`). */
export const equipoAdminListItemSchema = equipoOperativoSchema.extend({
  responsable: referenciaEquipoSchema,
  inscripcion: referenciaEquipoSchema,
});

/** The detail of a team (`RT-IN-10`). */
export const equipoAdminDetalleSchema = equipoAdminListItemSchema.extend({
  participantes: z.array(participanteDeEquipoSchema),
  cupos: cuposOperativosSchema,
  inscripcion_detalle: z.object({
    id: z.string().min(1),
    nombre: z.string(),
    referencia: z.string(),
  }),
  elegibilidad: z.array(candidatoAEquipoSchema),
});

/** The envelope of the administrative list of the teams. */
export const listaEquiposAdminEnvelope = envelopeAdminPaginado(
  equipoAdminListItemSchema,
);

/** The envelope of the administrative detail of a team. */
export const equipoAdminDetalleEnvelope = envelopeAdmin(equipoAdminDetalleSchema);

// ── La proyección del wire al modelo de la vista ─────────────────────────────

/** The wire of a participant of a roster. */
export type ParticipanteDeEquipoWire = z.infer<
  typeof participanteDeEquipoSchema
>;

/** The wire of a candidate for a team. */
export type CandidatoAEquipoWire = z.infer<typeof candidatoAEquipoSchema>;

/** The wire of a row of the administrative list of the teams. */
export type AdminEquipoListItemWire = z.infer<typeof equipoAdminListItemSchema>;

/** The wire of the administrative detail of a team. */
export type AdminEquipoDetalleWire = z.infer<typeof equipoAdminDetalleSchema>;

/** A participant of the roster, as the view expects it. */
export function participanteDeEquipoDesdeWire(
  participante: ParticipanteDeEquipoWire,
): ParticipanteDeEquipoOut {
  return participante;
}

/** A candidate for a team, as the view expects it. */
export function candidatoAEquipoDesdeWire(
  candidato: CandidatoAEquipoWire,
): CandidatoAEquipoOut {
  return {
    id: candidato.id,
    persona_id: candidato.persona_id,
    nombre: candidato.nombre,
    documento: candidato.documento,
    estado_operativo: veredictoDesdeEstadoOperativo(candidato.estado_operativo),
  };
}

/** A row of the administrative list of the teams, as the view expects it. */
export function equipoAdminListaDesdeWire(
  fila: AdminEquipoListItemWire,
): AdminEquipoListItemOut {
  return {
    id: fila.id,
    nombre: fila.nombre,
    disciplina: fila.disciplina,
    categoria: fila.categoria,
    plantilla: fila.plantilla,
    estado_operativo: veredictoDesdeEstadoOperativo(fila.estado_operativo),
    acciones_disponibles: fila.acciones_disponibles,
    responsable: fila.responsable,
    inscripcion: fila.inscripcion,
  };
}

/** The administrative detail of a team, as the view expects it. */
export function equipoAdminDetalleDesdeWire(
  detalle: AdminEquipoDetalleWire,
): AdminEquipoDetalleOut {
  return {
    ...equipoAdminListaDesdeWire(detalle),
    participantes: detalle.participantes.map(participanteDeEquipoDesdeWire),
    cupos: detalle.cupos,
    inscripcion_detalle: detalle.inscripcion_detalle,
    elegibilidad: detalle.elegibilidad.map(candidatoAEquipoDesdeWire),
  };
}
