import {
  equipoAdminDetalleDesdeWire,
  equipoAdminDetalleEnvelope,
  equipoAdminListaDesdeWire,
  listaEquiposAdminEnvelope,
} from "../schemas/equipo-admin.schema";
import type {
  AdminEquipoDetalleOut,
  AdminEquipoListItemOut,
} from "../types/equipos-admin.types";

/**
 * The data of the suites of the teams.
 *
 * It is the ANSWER OF THE CONTRACT, parsed by the SAME Zod mirror that the
 * service uses: a shape that the mirror rejects breaks the suite before it
 * draws anything (`FR-08` §1.4).
 *
 * The three numbers of the roster (6 · 7 · 10) are DECLARED literals and they
 * are NEVER calculated: the browser does not compare the roster with the
 * minimum (`contratos/01` §7).
 */

function datosDe<T>(envelope: { data: T | null }): T {
  if (!envelope.data) {
    throw new Error("El espejo del contrato no devolvió datos.");
  }

  return envelope.data;
}

const ESTADO_INCOMPLETO = {
  codigo: "INCOMPLETO",
  etiqueta: "Falta 1 jugador",
  descripcion: "Se necesita al menos 7 jugadores para competir",
};

const ESTADO_SIN_CUPO = {
  codigo: "SIN_CUPO_DEPORTIVO",
  etiqueta: "Sin cupo deportivo disponible",
  descripcion:
    "No hay cupos deportivos disponibles en esta inscripción para sumar a otra persona.",
};

const EQUIPO = {
  id: "00000000-0000-4000-8000-0000000000A1",
  nombre: "EQUIPO DE EJEMPLO",
  disciplina: {
    id: "00000000-0000-4000-8000-0000000000D1",
    nombre: "DISCIPLINA DE EJEMPLO",
  },
  categoria: {
    id: "00000000-0000-4000-8000-0000000000C1",
    nombre: "CATEGORIA DE EJEMPLO",
  },
  plantilla: { registrados: 6, minimo: 7, maximo: 10 },
  estado_operativo: ESTADO_INCOMPLETO,
  acciones_disponibles: ["VER_PARTICIPANTES", "AGREGAR_PARTICIPANTE"],
};

const FILA = {
  ...EQUIPO,
  responsable: {
    id: "00000000-0000-4000-8000-0000000000B2",
    nombre: "RESPONSABLE DE EJEMPLO",
  },
  inscripcion: {
    id: "00000000-0000-4000-8000-0000000000C1",
    nombre: "INSCRIPCION DE EJEMPLO",
  },
};

const PARTICIPANTE = {
  id: "00000000-0000-4000-8000-0000000000A2",
  persona_id: "00000000-0000-4000-8000-0000000000A3",
  nombre: "PERSONA DE EJEMPLO",
  documento: "00000000",
  rol: "JUGADOR",
  estado: "ACTIVA",
};

const CANDIDATO = {
  id: "00000000-0000-4000-8000-0000000000A4",
  persona_id: "00000000-0000-4000-8000-0000000000A5",
  nombre: "CANDIDATO DE EJEMPLO",
  documento: "00000000",
  estado_operativo: ESTADO_SIN_CUPO,
};

/** The rows of the administrative list of the teams. */
export const listaEquiposAdmin: readonly AdminEquipoListItemOut[] = datosDe(
  listaEquiposAdminEnvelope.parse({
    success: true,
    data: {
      items: [FILA],
      total: 1,
      page: 1,
      page_size: 25,
      total_pages: 1,
    },
    error: null,
    message: null,
  }),
).items.map(equipoAdminListaDesdeWire);

/** The administrative detail of a team. */
export const equipoAdminDetalle: AdminEquipoDetalleOut =
  equipoAdminDetalleDesdeWire(
    datosDe(
      equipoAdminDetalleEnvelope.parse({
        success: true,
        data: {
          ...FILA,
          participantes: [PARTICIPANTE],
          cupos: { adquiridos: 0, asignados: 0, disponibles: 0 },
          inscripcion_detalle: {
            id: "00000000-0000-4000-8000-0000000000C1",
            nombre: "INSCRIPCION DE EJEMPLO",
            referencia: "REFERENCIA DE EJEMPLO",
          },
          elegibilidad: [CANDIDATO],
        },
        error: null,
        message: null,
      }),
    ),
  );
