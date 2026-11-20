import { z } from "zod";
import {
  accionOperativaSchema,
  causaSchema,
  cuposOperativosSchema,
  envelopeAdmin,
  envelopeAdminPaginado,
  estadoOperativoSchema,
} from "@/features/admin/operaciones/schemas/operaciones.schema";
import { veredictoDesdeEstadoOperativo } from "@/features/admin/operaciones/utils/veredicto.adapter";
import type {
  AdminInscripcionDetalleOut,
  AdminInscripcionListItemOut,
  CompraDeCuposOut,
  EquipoDeInscripcionOut,
  EventoDeHistorialOut,
  ParticipacionPoolOut,
  ParticipanteDeEquipoOut,
  PoolDeInscripcionOut,
} from "../types/inscripciones-admin.types";

/**
 * The Zod mirrors of the ADMINISTRATION OF THE REGISTRATIONS.
 *
 * ## What they mirror
 *
 * The presenters the ledger declares for this area
 * (`RT-IN-07` -> `AdminInscripcionListaPresenter` and `RT-IN-08` ->
 * `AdminInscripcionDetallePresenter`), with the shapes of the plan
 * (`contratos/01`, admin) that UI-04 published as the view contract.
 *
 * ## What they are NOT
 *
 * They are NOT the mirror of a live wrapper: `AdminInscripcionController` is
 * NOT registered in `Aplicacion/backend/config/api.py`, so these routes do
 * NOT exist and no answer of the backend is ever parsed with them. They are
 * the SEAM of the contract: the day the controller is registered, the mirror
 * is the first thing to reconcile (`A0-API04-05`).
 *
 * ## The rules of the mirror
 *
 * - No `z.any()` and no generic field: every field is declared.
 * - The machine codes are `string`, not enums: the backend owns the
 *   vocabulary and a new value must not break the whole read.
 * - The `estado_operativo` of the wire is the FROZEN `EstadoOperativo`
 *   (`{codigo, etiqueta, descripcion}`). The visual bucket of the view (`rol`)
 *   is NOT on the wire: it is added by the adapter, because it is a decision
 *   of the interface (`D-UI04-03`).
 * - The amounts are strings, exactly as the plan declares them
 *   (`FR-08` §2.4). The projection of the same purchase of DOM-01 sends a
 *   float: the reconciliation is an A0 request (`A0-API04-04`).
 */

/** A person, as the administrative list names her. */
export const personaAdminSchema = z.object({
  id: z.string().min(1),
  nombre: z.string(),
});

/** A reference to a record of the area: the edition, the package, the team. */
export const referenciaAdminSchema = z.object({
  id: z.string().min(1),
  nombre: z.string(),
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

/** A team of a registration, with its roster and its state. */
export const equipoDeInscripcionSchema = z.object({
  id: z.string().min(1),
  nombre: z.string(),
  disciplina: referenciaAdminSchema,
  estado: z.string().min(1),
  participantes: z.array(participanteDeEquipoSchema),
  estado_operativo: estadoOperativoSchema,
});

/** A participation of the pool. */
export const participacionPoolSchema = z.object({
  id: z.string().min(1),
  persona_id: z.string().min(1),
  equipo_id: z.string().min(1),
  equipo_nombre: z.string(),
  disciplina_nombre: z.string(),
  rol: z.string().min(1),
  estado: z.string().min(1),
  ocupa_cupo: z.boolean(),
});

/** The pool of a registration, as the server publishes it. */
export const poolDeInscripcionSchema = z.object({
  cupos_pagados: z.number().int().nonnegative(),
  cupos_asignados: z.number().int().nonnegative(),
  cupos_disponibles: z.number().int().nonnegative(),
  participaciones: z.array(participacionPoolSchema),
  impedimentos: z.array(causaSchema),
});

/** A purchase of extra cupos. */
export const compraDeCuposSchema = z.object({
  compra_id: z.string().min(1),
  orden_pago_id: z.string().min(1).nullable(),
  estado: z.string().min(1),
  total: z.string(),
  moneda: z.string().min(1),
  estado_operativo: estadoOperativoSchema,
});

/** An event of the history of a registration. */
export const eventoDeHistorialSchema = z.object({
  occurred_at: z.string().min(1),
  tipo: z.string().min(1),
  descripcion: z.string(),
  actor: z.string(),
});

/** A row of the administrative list of the registrations (`RT-IN-07`). */
export const inscripcionAdminListItemSchema = z.object({
  id: z.string().min(1),
  responsable: personaAdminSchema,
  paquete: referenciaAdminSchema,
  edicion: referenciaAdminSchema,
  equipos: z.number().int().nonnegative(),
  personas: z.number().int().nonnegative(),
  estado: estadoOperativoSchema,
  cupos: cuposOperativosSchema,
  pago: estadoOperativoSchema.nullable(),
  alerta: causaSchema.nullable(),
  siguiente_accion: accionOperativaSchema.nullable(),
});

/** The detail of a registration (`RT-IN-08`). */
export const inscripcionAdminDetalleSchema = inscripcionAdminListItemSchema.extend({
  equipos_detalle: z.array(equipoDeInscripcionSchema),
  pool: poolDeInscripcionSchema,
  compras: z.array(compraDeCuposSchema),
  historial: z.array(eventoDeHistorialSchema),
});

/** The envelope of the administrative list of the registrations. */
export const listaInscripcionesAdminEnvelope = envelopeAdminPaginado(
  inscripcionAdminListItemSchema,
);

/** The envelope of the administrative detail of a registration. */
export const inscripcionAdminDetalleEnvelope = envelopeAdmin(
  inscripcionAdminDetalleSchema,
);

// ── La proyección del wire al modelo de la vista ─────────────────────────────

/** The wire of a participant of a roster. */
export type ParticipanteDeEquipoWire = z.infer<
  typeof participanteDeEquipoSchema
>;

/** The wire of a team of a registration. */
export type EquipoDeInscripcionWire = z.infer<typeof equipoDeInscripcionSchema>;

/** The wire of a participation of the pool. */
export type ParticipacionPoolWire = z.infer<typeof participacionPoolSchema>;

/** The wire of the pool of a registration. */
export type PoolDeInscripcionWire = z.infer<typeof poolDeInscripcionSchema>;

/** The wire of a purchase of extra cupos. */
export type CompraDeCuposWire = z.infer<typeof compraDeCuposSchema>;

/** The wire of an event of the history. */
export type EventoDeHistorialWire = z.infer<typeof eventoDeHistorialSchema>;

/** The wire of a row of the administrative list. */
export type AdminInscripcionListItemWire = z.infer<
  typeof inscripcionAdminListItemSchema
>;

/** The wire of the administrative detail of a registration. */
export type AdminInscripcionDetalleWire = z.infer<
  typeof inscripcionAdminDetalleSchema
>;

/** A participant of the roster, as the view expects it. */
export function participanteDeEquipoDesdeWire(
  participante: ParticipanteDeEquipoWire,
): ParticipanteDeEquipoOut {
  return participante;
}

/** A team of a registration, as the view expects it. */
export function equipoDeInscripcionDesdeWire(
  equipo: EquipoDeInscripcionWire,
): EquipoDeInscripcionOut {
  return {
    id: equipo.id,
    nombre: equipo.nombre,
    disciplina: equipo.disciplina,
    estado: equipo.estado,
    participantes: equipo.participantes.map(participanteDeEquipoDesdeWire),
    estado_operativo: veredictoDesdeEstadoOperativo(equipo.estado_operativo),
  };
}

/** A participation of the pool, as the view expects it. */
export function participacionPoolDesdeWire(
  participacion: ParticipacionPoolWire,
): ParticipacionPoolOut {
  return participacion;
}

/** The pool of a registration, as the view expects it. */
export function poolDeInscripcionDesdeWire(
  pool: PoolDeInscripcionWire,
): PoolDeInscripcionOut {
  return {
    cupos_pagados: pool.cupos_pagados,
    cupos_asignados: pool.cupos_asignados,
    cupos_disponibles: pool.cupos_disponibles,
    participaciones: pool.participaciones.map(participacionPoolDesdeWire),
    impedimentos: pool.impedimentos,
  };
}

/** A purchase of extra cupos, as the view expects it. */
export function compraDeCuposDesdeWire(
  compra: CompraDeCuposWire,
): CompraDeCuposOut {
  return {
    compra_id: compra.compra_id,
    orden_pago_id: compra.orden_pago_id,
    estado: compra.estado,
    total: compra.total,
    moneda: compra.moneda,
    estado_operativo: veredictoDesdeEstadoOperativo(compra.estado_operativo),
  };
}

/** An event of the history, as the view expects it. */
export function eventoDeHistorialDesdeWire(
  evento: EventoDeHistorialWire,
): EventoDeHistorialOut {
  return evento;
}

/** A row of the administrative list, as the view expects it. */
export function inscripcionAdminListaDesdeWire(
  fila: AdminInscripcionListItemWire,
): AdminInscripcionListItemOut {
  return {
    id: fila.id,
    responsable: fila.responsable,
    paquete: fila.paquete,
    edicion: fila.edicion,
    equipos: fila.equipos,
    personas: fila.personas,
    estado: veredictoDesdeEstadoOperativo(fila.estado),
    cupos: fila.cupos,
    pago: fila.pago ? veredictoDesdeEstadoOperativo(fila.pago) : null,
    alerta: fila.alerta,
    siguiente_accion: fila.siguiente_accion,
  };
}

/** The administrative detail of a registration, as the view expects it. */
export function inscripcionAdminDetalleDesdeWire(
  detalle: AdminInscripcionDetalleWire,
): AdminInscripcionDetalleOut {
  return {
    ...inscripcionAdminListaDesdeWire(detalle),
    equipos_detalle: detalle.equipos_detalle.map(equipoDeInscripcionDesdeWire),
    pool: poolDeInscripcionDesdeWire(detalle.pool),
    compras: detalle.compras.map(compraDeCuposDesdeWire),
    historial: detalle.historial.map(eventoDeHistorialDesdeWire),
  };
}
