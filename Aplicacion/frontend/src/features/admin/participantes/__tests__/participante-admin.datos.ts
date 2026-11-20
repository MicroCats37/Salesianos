import {
  listaParticipantesAdminEnvelope,
  participanteAdminDesdeWire,
} from "../schemas/participante-admin.schema";
import type { ParticipanteAdminOut } from "../types/participantes-admin.types";

/**
 * The data of the suites of the participants.
 *
 * It is the ANSWER OF THE CONTRACT, parsed by the SAME Zod mirror that the
 * service uses (`FR-08` §1.4).
 *
 * The conflict of a participation is DECLARED by the backend with its reason:
 * the suite never decides that two participations collide
 * (`GOV-02-RB-04b`).
 */

function datosDe<T>(envelope: { data: T | null }): T {
  if (!envelope.data) {
    throw new Error("El espejo del contrato no devolvió datos.");
  }

  return envelope.data;
}

const PERSONA = {
  id: "00000000-0000-4000-8000-0000000000A3",
  nombre: "PERSONA DE EJEMPLO",
  documento: "00000000",
  participaciones: [
    {
      id: "00000000-0000-4000-8000-000000000D1",
      evento: {
        id: "00000000-0000-4000-8000-000000000001",
        nombre: "EDICION DE EJEMPLO",
      },
      equipo: {
        id: "00000000-0000-4000-8000-0000000000A1",
        nombre: "EQUIPO DE EJEMPLO",
      },
      disciplina: {
        id: "00000000-0000-4000-8000-0000000000D2",
        nombre: "DISCIPLINA DE EJEMPLO",
      },
      rol: "JUGADOR",
      estado: "ACTIVA",
      conflicto: {
        codigo: "DUPLICADO_EN_LA_MISMA_DISCIPLINA",
        mensaje:
          "Esta persona ya participa en la misma disciplina en este equipo.",
      },
    },
  ],
  historial: [
    {
      occurred_at: "2026-01-01T00:00:00Z",
      tipo: "PARTICIPACION_AGREGADA",
      descripcion: "La persona se incorporate al equipo.",
    },
  ],
};

/** The rows of the administrative search of the participants. */
export const listaParticipantesAdmin: readonly ParticipanteAdminOut[] = datosDe(
  listaParticipantesAdminEnvelope.parse({
    success: true,
    data: {
      items: [PERSONA],
      total: 1,
      page: 1,
      page_size: 25,
      total_pages: 1,
    },
    error: null,
    message: null,
  }),
).items.map(participanteAdminDesdeWire);
