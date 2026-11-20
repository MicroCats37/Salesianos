import type {
  AccionOperativa,
  CuposOperativosOut,
  EstadoSuperficie,
  Veredicto,
} from "@/features/admin/operaciones";

/**
 * The view models of the administration of the registrations.
 *
 * They mirror the PROPOSED presenters of the plan, which do NOT exist in the
 * target backend yet:
 *
 * - `AdminInscripcionListaPresenter` -> `AdminInscripcionListItemOut`
 *   (`RT-IN-07`, `GET /administracion/inscripciones`).
 * - `AdminInscripcionDetallePresenter` -> `AdminInscripcionDetalleOut`
 *   (`RT-IN-08`, `GET /administracion/inscripciones/{inscripcion_id}`).
 *
 * Neither controller is registered in `Aplicacion/backend/config/api.py`, so
 * these types are the SEAM where the real wrappers land in API-04
 * (`D-UI01-03`).
 *
 * No business rule lives here. The cupos are DECLARED by the presenter and
 * the browser NEVER subtracts them (`GOV-02-RB-04a`).
 */

/** A person, as the administrative list names her. */
export interface PersonaAdminOut {
  id: string;
  nombre: string;
}

/** The three cupos of a registration, as the server publishes them. */
export type CuposInscripcionOut = CuposOperativosOut;

/** A row of the administrative list of registrations (`RT-IN-07`). */
export interface AdminInscripcionListItemOut {
  id: string;
  responsable: PersonaAdminOut;
  paquete: { id: string; nombre: string };
  edicion: { id: string; nombre: string };
  /** The number of teams of the registration. */
  equipos: number;
  /** The number of people of the registration. */
  personas: number;
  /** The understandable state, with its cause. */
  estado: Veredicto;
  /** The three cupos, as three different facts. */
  cupos: CuposInscripcionOut;
  /** The payment state that is relevant for this registration. */
  pago: Veredicto | null;
  /** The alert of the row, with the reason of the backend. */
  alerta: { codigo: string; mensaje: string } | null;
  /** The next permitted step, as the presenter named it. */
  siguiente_accion: AccionOperativa | null;
}

/** A participant of the roster of a team. */
export interface ParticipanteDeEquipoOut {
  id: string;
  persona_id: string;
  nombre: string;
  /** The document of the person, as the backend publishes it. */
  documento: string;
  /** `JUGADOR`, `CAPITAN` or `DELEGADO`. */
  rol: string;
  /** `ACTIVA` or `RETIRADA`. */
  estado: string;
}

/** A team of a registration, with its roster and its state. */
export interface EquipoDeInscripcionOut {
  id: string;
  nombre: string;
  disciplina: { id: string; nombre: string };
  /** `ACTIVO` or `RETIRADO`. */
  estado: string;
  /** The roster of the team. */
  participantes: readonly ParticipanteDeEquipoOut[];
  /** The state of the team, with its cause. */
  estado_operativo: Veredicto;
}

/** A participation of the pool, as the server publishes it (`ParticipacionOut`). */
export interface ParticipacionPoolOut {
  id: string;
  persona_id: string;
  equipo_id: string;
  equipo_nombre: string;
  disciplina_nombre: string;
  /** `JUGADOR`, `CAPITAN` or `DELEGADO`. */
  rol: string;
  /** `ACTIVA` or `RETIRADA`. */
  estado: string;
  /** Whether the participation occupies a cupo of the registration. */
  ocupa_cupo: boolean;
}

/** The pool of a registration, as the server publishes it (`PoolOut`). */
export interface PoolDeInscripcionOut {
  cupos_pagados: number;
  cupos_asignados: number;
  cupos_disponibles: number;
  /** The participations of the pool. */
  participaciones: readonly ParticipacionPoolOut[];
  /** The concrete causes that prevent widening the roster. */
  impedimentos: readonly { codigo: string; mensaje: string }[];
}

/** A purchase of extra cupos, as the server publishes it (`CompraOut`). */
export interface CompraDeCuposOut {
  compra_id: string;
  orden_pago_id: string | null;
  /** `PENDIENTE`, `PAGADA` or `CANCELADA`. */
  estado: string;
  /** The amount as the server sends it: a string, never a number. */
  total: string;
  /** The ISO-4217 code of the currency. */
  moneda: string;
  /** The verdict of the payment of this purchase. */
  estado_operativo: Veredicto;
}

/** An event of the history of a registration. */
export interface EventoDeHistorialOut {
  occurred_at: string;
  tipo: string;
  descripcion: string;
  actor: string;
}

/** The detail of a registration (`RT-IN-08`). */
export interface AdminInscripcionDetalleOut extends AdminInscripcionListItemOut {
  equipos_detalle: readonly EquipoDeInscripcionOut[];
  pool: PoolDeInscripcionOut;
  compras: readonly CompraDeCuposOut[];
  historial: readonly EventoDeHistorialOut[];
}

/** The state of the administrative list of registrations. */
export type EstadoListaInscripcionesAdmin = EstadoSuperficie<
  readonly AdminInscripcionListItemOut[]
>;

/** The state of the administrative detail of a registration. */
export type EstadoDetalleInscripcionAdmin = EstadoSuperficie<
  AdminInscripcionDetalleOut
>;
