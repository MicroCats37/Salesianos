import type { EstadoSuperficie } from "@/features/admin/operaciones";
import type {
  EventoDeHistorialAdminOut,
  ParticipacionAdminOut,
} from "@/features/admin/participantes/types/participantes-admin.types";

/**
 * The view models of the administrative search of PEOPLE.
 *
 * They mirror the backend `AdminPersonaListItemOut` / `AdminPersonaDetalleOut`
 * (`modules/administracion/presentation/schemas/admin_operacion_schemas.py`).
 *
 * ## ONE owner for ONE shape
 *
 * The wire of a person is the SAME wire as the wire of a participant
 * (`RT-ID-07` and `RT-IN-11` publish the same wrapper). The types and the
 * mirror of the participations are REUSED here: the area never has two
 * descriptions of the same wire, so a drift between the presenter and the
 * browser is a parse error and not a silently wrong field.
 */
export type { EventoDeHistorialAdminOut, ParticipacionAdminOut };

/** A person of the administrative search, with her participations. */
export interface AdminPersonaListItemOut {
  id: string;
  nombre: string;
  /** The document of the person, as the backend publishes it. */
  documento: string;
  /** The participations of the person. */
  participaciones: readonly ParticipacionAdminOut[];
  /** The history of the person. */
  historial: readonly EventoDeHistorialAdminOut[];
}

/** The detail of a person (`RT-ID-08`). */
export interface AdminPersonaDetalleOut extends AdminPersonaListItemOut {
  telefono: string;
  whatsapp: string;
  email: string;
}

/** The state of the administrative search of people. */
export type EstadoPersonasAdmin = EstadoSuperficie<
  readonly AdminPersonaListItemOut[]
>;
