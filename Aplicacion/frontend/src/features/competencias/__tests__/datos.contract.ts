import {
  agendaSchema,
  avancePreviewSchema,
  competenciaDetalleSchema,
  competenciaListadoSchema,
  correccionImpactoSchema,
  correccionPreviewSchema,
  encuentroSchema,
  equipoElegibleSchema,
  rondaSchema,
} from "../schemas/competencia.schema";

/**
 * The data of the competitions suite, built THROUGH the Zod mirror.
 *
 * ## WHY THE DATA LIVES HERE AND NOT IN A PRODUCTION FIXTURE
 *
 * The provisional fixture of `UI-05` was a file of PRODUCTION code that
 * carried a copy of the wire of the backend. `API-05` removes it, because the
 * wire of the backend is now written down ONCE, in the mirror
 * (`schemas/competencia.schema.ts`), and the suite reads that same mirror.
 *
 * The consequence is the point of the file: a shape that the mirror rejects
 * breaks the suite **BEFORE** a single pixel is drawn. The literals below
 * are the JSON that the presenters of `DOM-07` publish, so the mirror is
 * verifiable by reading them.
 *
 * These are EXAMPLES of the wire, not a transport: no module of production
 * imports this file and it is not exported from any barrel.
 */

/** The encounter that the card, the agenda and the bracket share. */
export const ENCUENTRO = encuentroSchema.parse({
  id: "4e5f6a7b-8c9d-0e1f-2a3b-4c5d6e7f8091",
  ronda_id: "5f6a7b8c-9d0e-1f2a-3b4c-5d6e7f8091a2",
  ronda_etiqueta: "Octavos de final",
  ronda_orden: 1,
  competencia_id: "7c1f0a52-1f4b-4d0a-9a3e-2b7c4d5e6f70",
  orden: 1,
  estado: "FINALIZADO",
  es_bye: false,
  participantes: [
    {
      slot: "PARTICIPANTE_1",
      competencia_equipo_id: "2c3d4e5f-6a7b-8c9d-0e1f-2a3b4c5d6e7f",
      equipo_id: "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80",
      equipo_nombre: "Colegio Norte",
      orden: 1,
    },
    {
      slot: "PARTICIPANTE_2",
      competencia_equipo_id: "3e4f5a6b-7c8d-9e0f-1a2b-3c4d5e6f7a8b",
      equipo_id: "4f5a6b7c-8d9e-0f1a-2b3c-4d5e6f7a8b9c",
      equipo_nombre: "Colegio Sur",
      orden: 2,
    },
  ],
  inicio_programado: "2026-11-21T16:00:00+00:00",
  fin_programado: "2026-11-21T17:00:00+00:00",
  puntaje_1: 2,
  puntaje_2: 1,
  marcador_detalle: "",
  ganador_equipo_id: "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80",
  ganador_equipo_nombre: "Colegio Norte",
  siguiente_encuentro_id: "6a7b8c9d-0e1f-2a3b-4c5d-6e7f8091a2b3",
  slot_destino: "PARTICIPANTE_1",
  iniciado_en: "2026-11-21T16:05:00+00:00",
  finalizado_en: "2026-11-21T16:52:00+00:00",
  version: 4,
  acciones: ["corregir", "avanzar"],
});

/** The round that holds the encounter. */
export const RONDA = rondaSchema.parse({
  id: "5f6a7b8c-9d0e-1f2a-3b4c-5d6e7f8091a2",
  etiqueta: "Octavos de final",
  orden: 1,
  estado: "ACTIVA",
  version: 1,
  encuentros: [ENCUENTRO],
});

/** The row of the list of competitions. */
export const COMPETENCIA = competenciaListadoSchema.parse({
  id: "7c1f0a52-1f4b-4d0a-9a3e-2b7c4d5e6f70",
  edicion_id: "0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  disciplina_id: "1b2c3d4e-5f6a-7b8c-9d0e-1f2a3b4c5d6e",
  disciplina_nombre: "Fútbol 7",
  categoria_id: "8d2e1b64-2a5c-4e1b-8b4f-3c8d5e6f7a81",
  categoria_nombre: "JUNIOR",
  nombre: "Copa Salesianos",
  estado: "PLANIFICADA",
  fecha: "2026-11-21",
  total_equipos: 8,
  total_encuentros: 7,
  total_encuentros_finalizados: 0,
});

/** The operational detail of the competition. */
export const DETALLE = competenciaDetalleSchema.parse({
  id: COMPETENCIA.id,
  edicion_id: COMPETENCIA.edicion_id,
  edicion_nombre: "Salesianos FEST 2026",
  disciplina_id: COMPETENCIA.disciplina_id,
  disciplina_nombre: COMPETENCIA.disciplina_nombre,
  categoria_id: COMPETENCIA.categoria_id,
  categoria_nombre: COMPETENCIA.categoria_nombre,
  nombre: COMPETENCIA.nombre,
  estado: COMPETENCIA.estado,
  fecha: COMPETENCIA.fecha,
  version: 1,
  equipos: [
    {
      id: "2c3d4e5f-6a7b-8c9d-0e1f-2a3b4c5d6e7f",
      equipo_id: "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80",
      equipo_nombre: "Colegio Norte",
      orden: 1,
      estado: "ACTIVO",
      version: 1,
    },
  ],
  rondas: [RONDA],
});

/** The agenda of the day. */
export const AGENDA = agendaSchema.parse({
  edicion_id: COMPETENCIA.edicion_id,
  edicion_nombre: "Salesianos FEST 2026",
  fecha: COMPETENCIA.fecha,
  total: 1,
  encuentros: [ENCUENTRO],
});

/** A candidate team that CAN compete. */
export const EQUIPO_ELEGIBLE = equipoElegibleSchema.parse({
  equipo_id: "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80",
  nombre: "Colegio Norte",
  edicion_id: COMPETENCIA.edicion_id,
  disciplina_id: COMPETENCIA.disciplina_id,
  disciplina_nombre: COMPETENCIA.disciplina_nombre,
  categoria_id: COMPETENCIA.categoria_id,
  categoria_nombre: COMPETENCIA.categoria_nombre,
  estado: "CONFIRMADA",
  es_elegible: true,
  motivo: "ELEGIBLE",
  participantes_activos: 7,
  minimo_requerido: 7,
});

/** A candidate team that CANNOT compete, with the reason of its owner. */
export const EQUIPO_NO_ELEGIBLE = equipoElegibleSchema.parse({
  equipo_id: "4f5a6b7c-8d9e-0f1a-2b3c-4d5e6f7a8b9c",
  nombre: "Colegio Sur",
  edicion_id: COMPETENCIA.edicion_id,
  disciplina_id: COMPETENCIA.disciplina_id,
  disciplina_nombre: COMPETENCIA.disciplina_nombre,
  categoria_id: COMPETENCIA.categoria_id,
  categoria_nombre: COMPETENCIA.categoria_nombre,
  estado: "CONFIRMADA",
  es_elegible: false,
  motivo: "PLANTILLA_INCOMPLETA",
  participantes_activos: 6,
  minimo_requerido: 7,
});

/**
 * The preview of an advance.
 *
 * It describes what the advance WOULD do and it NEVER WRITES (`QA-K04`).
 */
export const VISTA_PREVIA_AVANCE = avancePreviewSchema.parse({
  encuentro_id: ENCUENTRO.id,
  siguiente_encuentro_id: "6a7b8c9d-0e1f-2a3b-4c5d-6e7f8091a2b3",
  slot_destino: "PARTICIPANTE_1",
  ganador_equipo_id: "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80",
  ganador_equipo_nombre: "Colegio Norte",
  ocupante_actual_equipo_id: null,
  ya_propagado: false,
  bloqueado: false,
  motivo_bloqueo: null,
  puede_confirmar: true,
});

/** The impact of a correction on one descendant. */
export const IMPACTO_CORRECCION = correccionImpactoSchema.parse({
  encuentro_id: "6a7b8c9d-0e1f-2a3b-4c5d-6e7f8091a2b3",
  slot: "PARTICIPANTE_1",
  bloqueado: false,
  motivo_bloqueo: null,
  reemplaza: true,
  limpia_slot: false,
  limpia_resultado: false,
  afecta: true,
});

/**
 * The preview of a correction.
 *
 * It NEVER WRITES: it names the descendants that would really change.
 */
export const VISTA_PREVIA_CORRECCION = correccionPreviewSchema.parse({
  encuentro_id: ENCUENTRO.id,
  ganador_actual_equipo_id: "3d4e5f6a-7b8c-9d0e-1f2a-3b4c5d6e7f80",
  ganador_nuevo_equipo_id: "4f5a6b7c-8d9e-0f1a-2b3c-4d5e6f7a8b9c",
  ganador_nuevo_equipo_nombre: "Colegio Sur",
  requiere_override: false,
  total_afectados: 1,
  descendientes: [IMPACTO_CORRECCION],
  puede_confirmar: true,
});
