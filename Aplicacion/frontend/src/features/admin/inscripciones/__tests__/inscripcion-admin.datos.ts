import {
  inscripcionAdminDetalleDesdeWire,
  inscripcionAdminDetalleEnvelope,
  inscripcionAdminListaDesdeWire,
  listaInscripcionesAdminEnvelope,
} from "../schemas/inscripcion-admin.schema";
import type {
  AdminInscripcionDetalleOut,
  AdminInscripcionListItemOut,
} from "../types/inscripciones-admin.types";

/**
 * The data of the suites of the registrations.
 *
 * ## What this is
 *
 * The ANSWER OF THE CONTRACT, parsed by the SAME Zod mirror that the service
 * uses. A shape that the mirror rejects breaks the suite BEFORE it draws
 * anything (`FR-08` §1.4 · `D-API03-05`).
 *
 * ## What this is NOT
 *
 * It is NOT a provisional fixture: the marker of a provisional contract is
 * gone and it will not come back. The values are EXAMPLES of the declared
 * contract, they are literals (they are never calculated) and they are
 * consumed ONLY by the suites of this feature: no production module imports
 * them.
 */

function datosDe<T>(envelope: { data: T | null }): T {
  if (!envelope.data) {
    throw new Error("El espejo del contrato no devolvió datos.");
  }

  return envelope.data;
}

const ESTADO_CREADA = {
  codigo: "CREADA",
  etiqueta: "Inscripción creada",
  descripcion:
    "La inscripción existe y todavía no ha sido cancelada. Los cupos y las personas son los que declara el servidor.",
};

const ESTADO_PAGO_PENDIENTE = {
  codigo: "PENDIENTE",
  etiqueta: "Pago pendiente",
  descripcion: "El pago todavía no se ha completado.",
};

const FILA = {
  id: "00000000-0000-4000-8000-000000000C1",
  responsable: {
    id: "00000000-0000-4000-8000-000000000C2",
    nombre: "RESPONSABLE DE EJEMPLO",
  },
  paquete: {
    id: "00000000-0000-4000-8000-000000000C3",
    nombre: "PAQUETE DE EJEMPLO",
  },
  edicion: {
    id: "00000000-0000-4000-8000-000000000001",
    nombre: "EDICION DE EJEMPLO",
  },
  equipos: 1,
  personas: 1,
  estado: ESTADO_CREADA,
  cupos: { adquiridos: 0, asignados: 0, disponibles: 0 },
  pago: null,
  alerta: null,
  siguiente_accion: null,
};

const PARTICIPANTE = {
  id: "00000000-0000-4000-8000-000000000A11",
  persona_id: "00000000-0000-4000-8000-000000000A12",
  nombre: "PERSONA DE EJEMPLO",
  documento: "00000000",
  rol: "JUGADOR",
  estado: "ACTIVA",
};

const EQUIPO = {
  id: "00000000-0000-4000-8000-000000000A21",
  nombre: "EQUIPO DE EJEMPLO",
  disciplina: {
    id: "00000000-0000-4000-8000-000000000D1",
    nombre: "DISCIPLINA DE EJEMPLO",
  },
  estado: "ACTIVO",
  participantes: [PARTICIPANTE],
  estado_operativo: ESTADO_CREADA,
};

const POOL = {
  cupos_pagados: 0,
  cupos_asignados: 0,
  cupos_disponibles: 0,
  participaciones: [
    {
      id: "00000000-0000-4000-8000-000000000A31",
      persona_id: "00000000-0000-4000-8000-000000000A12",
      equipo_id: "00000000-0000-4000-8000-000000000A21",
      equipo_nombre: "EQUIPO DE EJEMPLO",
      disciplina_nombre: "DISCIPLINA DE EJEMPLO",
      rol: "JUGADOR",
      estado: "ACTIVA",
      ocupa_cupo: true,
    },
  ],
  impedimentos: [],
};

const COMPRA = {
  compra_id: "00000000-0000-4000-8000-000000000B1",
  orden_pago_id: null,
  estado: "PENDIENTE",
  total: "0.00",
  moneda: "PEN",
  estado_operativo: ESTADO_PAGO_PENDIENTE,
};

const HISTORIAL = {
  occurred_at: "2026-01-01T00:00:00Z",
  tipo: "INSCRIPCION_CREADA",
  descripcion: "La inscripción fue creada.",
  actor: "RESPONSABLE DE EJEMPLO",
};

/** The rows of the administrative list of the registrations. */
export const listaInscripcionesAdmin: readonly AdminInscripcionListItemOut[] =
  datosDe(
    listaInscripcionesAdminEnvelope.parse({
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
  ).items.map(inscripcionAdminListaDesdeWire);

/** The administrative detail of a registration. */
export const inscripcionAdminDetalle: AdminInscripcionDetalleOut =
  inscripcionAdminDetalleDesdeWire(
    datosDe(
      inscripcionAdminDetalleEnvelope.parse({
        success: true,
        data: {
          ...FILA,
          equipos_detalle: [EQUIPO],
          pool: POOL,
          compras: [COMPRA],
          historial: [HISTORIAL],
        },
        error: null,
        message: null,
      }),
    ),
  );

/** The pool of a registration, as the view consumes it. */
export const poolDeInscripcion = inscripcionAdminDetalle.pool;
