import type {
  CuposOperativosOut,
  EstadoSuperficie,
  Veredicto,
} from "@/features/admin/operaciones";

/**
 * The view models of the administration of the teams.
 *
 * They mirror the PROPOSED presenter of the plan, which does NOT exist in the
 * target backend yet:
 *
 * - `EquipoOperativoOut` (plan `contratos/01` §3) — the canonical example of
 *   the frozen fixture contract (`FR-08` §2.3).
 * - `AdminEquipoListaPresenter` -> `AdminEquipoListItemOut`
 *   (`RT-IN-09`, `GET /administracion/equipos`).
 * - `AdminEquipoDetallePresenter` -> `AdminEquipoDetalleOut`
 *   (`RT-IN-10`, `GET /administracion/equipos/{equipo_id}`).
 *
 * The controller is NOT registered in `Aplicacion/backend/config/api.py`, so
 * these types are the SEAM where the real wrappers land in API-04.
 *
 * No business rule lives here. The minimum, the maximum, the roster count
 * and the verdict are DECLARED by the presenter: the browser never subtracts
 * them and never infers that a team is incomplete (`contratos/01` §7).
 */

/** The roster of a team, with the three numbers the server publishes. */
export interface PlantillaEquipoOut {
  /** The participations that are active. */
  registrados: number;
  /** The minimum the discipline declares. */
  minimo: number;
  /** The maximum the discipline declares. */
  maximo: number;
}

/**
 * The team, as the administrative presenter composes it.
 *
 * `acciones_disponibles` is a PROJECTION, not authorisation
 * (`contratos/01` §6 · `GOV-02-RB-03d`): the interface may use it to hide an
 * affordance, but the 403 of the backend remains the control.
 */
export interface EquipoOperativoOut {
  id: string;
  nombre: string;
  disciplina: { id: string; nombre: string };
  categoria: { id: string; nombre: string };
  plantilla: PlantillaEquipoOut;
  /** The understandable state, with its cause. */
  estado_operativo: Veredicto;
  /** The codes of the actions the presenter projects. */
  acciones_disponibles: readonly string[];
}

/** A row of the administrative list of teams (`RT-IN-09`). */
export interface AdminEquipoListItemOut extends EquipoOperativoOut {
  responsable: { id: string; nombre: string };
  inscripcion: { id: string; nombre: string };
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

/**
 * A candidate for a team.
 *
 * The verdict of the candidate is the BACKEND's: the browser never decides
 * that a person may enter a team nor that it may not.
 */
export interface CandidatoAEquipoOut {
  id: string;
  persona_id: string;
  nombre: string;
  documento: string;
  /** The verdict of the backend for this candidate, with its cause. */
  estado_operativo: Veredicto;
}

/** The detail of a team (`RT-IN-10`). */
export interface AdminEquipoDetalleOut extends AdminEquipoListItemOut {
  /** The roster of the team. */
  participantes: readonly ParticipanteDeEquipoOut[];
  /** The three cupos of the linked registration. */
  cupos: CuposOperativosOut;
  /** The registration the team belongs to. */
  inscripcion_detalle: { id: string; nombre: string; referencia: string };
  /** The candidates and the reason of the ones that cannot enter. */
  elegibilidad: readonly CandidatoAEquipoOut[];
}

/** The state of the administrative list of teams. */
export type EstadoListaEquiposAdmin = EstadoSuperficie<
  readonly AdminEquipoListItemOut[]
>;

/** The state of the administrative detail of a team. */
export type EstadoDetalleEquipoAdmin = EstadoSuperficie<AdminEquipoDetalleOut>;
