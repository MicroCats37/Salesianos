import type { EstadoSuperficie } from "@/features/admin/operaciones";

/**
 * The view models of the administration of the participants.
 *
 * They mirror the PROPOSED presenter of the plan, which does NOT exist in the
 * target backend yet:
 *
 * - `AdminParticipanteListaPresenter` -> `AdminParticipanteListItemOut`
 *   (`RT-IN-11`, `GET /administracion/participantes`).
 * - `AdminPersonaListaPresenter` -> `AdminPersonaListItemOut`
 *   (`RT-ID-07`, `GET /administracion/personas`).
 *
 * Neither controller is registered in `Aplicacion/backend/config/api.py`, so
 * these types are the SEAM where the real wrappers land in API-04.
 *
 * A conflict is DECLARED by the backend with its reason: the browser never
 * decides that two participations collide (`GOV-02-RB-04b`).
 */

/** A participation of a person, with its edition, team and discipline. */
export interface ParticipacionAdminOut {
  id: string;
  /**
   * The edition the participation belongs to.
   *
   * It is the EDITION and not the "event": the target renamed the concept in
   * `FND-02` and the wire follows the vocabulary of the backend
   * (`XCT-02` · reconciliación del espejo).
   */
  edicion: { id: string; nombre: string };
  equipo: { id: string; nombre: string };
  disciplina: { id: string; nombre: string };
  /** `JUGADOR`, `CAPITAN` or `DELEGADO`. */
  rol: string;
  /** `ACTIVA` or `RETIRADA`. */
  estado: string;
  /** The conflict the backend detected, with its reason. */
  conflicto: { codigo: string; mensaje: string } | null;
}

/** An event of the history of a person. */
export interface EventoDeHistorialAdminOut {
  occurred_at: string;
  tipo: string;
  descripcion: string;
}

/** A person of the administrative search, with her participations. */
export interface ParticipanteAdminOut {
  id: string;
  nombre: string;
  /** The document of the person, as the backend publishes it. */
  documento: string;
  /** The participations of the person, grouped by the views. */
  participaciones: readonly ParticipacionAdminOut[];
  /** The history of the person. */
  historial: readonly EventoDeHistorialAdminOut[];
}

/** The state of the administrative search of participants. */
export type EstadoParticipantesAdmin = EstadoSuperficie<
  readonly ParticipanteAdminOut[]
>;
