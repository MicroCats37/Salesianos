/**
 * The wire of the PUBLIC surface of the encounters.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * These are EXAMPLES of the wire, not a transport: no module of production
 * imports this file. They are the JSON that the presenters of
 * `Aplicacion/backend/modules/competencias/presentation/schemas/competencias_schemas.py`
 * publish for `GET /publico/competenarios/encuentros`.
 */

/** A published encounter in game. */
export const ENCUENTRO_EN_VIVO = {
  id: "11111111-1111-4111-8111-111111111111",
  ronda_id: "22222222-2222-4222-8222-222222222222",
  ronda_etiqueta: "Cuartos de final",
  ronda_orden: 1,
  competencia_id: "33333333-3333-4333-8333-333333333333",
  orden: 1,
  estado_publico: "EN_VIVO",
  es_bye: false,
  participantes: [
    {
      slot: "PARTICIPANTE_1",
      competencia_equipo_id: "44444444-4444-4444-8444-444444444444",
      equipo_id: "55555555-5555-4555-8555-555555555555",
      equipo_nombre: "Salesianos A",
      orden: 1,
    },
    {
      slot: "PARTICIPANTE_2",
      competencia_equipo_id: "66666666-6666-4666-8666-666666666666",
      equipo_id: "77777777-7777-4777-8777-777777777777",
      equipo_nombre: "Salesianos B",
      orden: 2,
    },
  ],
  inicio_programado: "2027-03-14T15:00:00Z",
  fin_programado: "2027-03-14T16:00:00Z",
  iniciado_en: "2027-03-14T15:03:00Z",
  finalizado_en: null,
  puntaje_1: 1,
  puntaje_2: 1,
  marcador_detalle: "Set 1: 25-19",
  ganador_equipo_id: null,
  ganador_equipo_nombre: null,
  version: 4,
};

/**
 * A published encounter with a result.
 *
 * The score does NOT match the winner on purpose: the score is INFORMATIVE
 * and the winner is the authority. A mirror that derived the winner from the
 * score would break here.
 */
export const ENCUENTRO_FINALIZADO = {
  id: "88888888-8888-4888-8888-888888888888",
  ronda_id: "22222222-2222-4222-8222-222222222222",
  ronda_etiqueta: "Cuartos de final",
  ronda_orden: 1,
  competencia_id: "33333333-3333-4333-8333-333333333333",
  orden: 2,
  estado_publico: "FINALIZADO",
  es_bye: false,
  participantes: [
    {
      slot: "PARTICIPANTE_1",
      competencia_equipo_id: "44444444-4444-4444-8444-444444444444",
      equipo_id: "55555555-5555-4555-8555-555555555555",
      equipo_nombre: "Salesianos A",
      orden: 1,
    },
    {
      slot: "PARTICIPANTE_2",
      competencia_equipo_id: "66666666-6666-4666-8666-666666666666",
      equipo_id: "77777777-7777-4777-8777-777777777777",
      equipo_nombre: "Salesianos B",
      orden: 2,
    },
  ],
  inicio_programado: "2027-03-14T13:00:00Z",
  fin_programado: "2027-03-14T14:00:00Z",
  iniciado_en: "2027-03-14T13:02:00Z",
  finalizado_en: "2027-03-14T13:58:00Z",
  puntaje_1: 9,
  puntaje_2: 4,
  marcador_detalle: "Set 1: 9-4",
  ganador_equipo_id: "77777777-7777-4777-8777-777777777777",
  ganador_equipo_nombre: "Salesianos B",
  version: 7,
};

/** A published encounter of the programme. */
export const ENCUENTRO_PROGRAMADO = {
  ...ENCUENTRO_EN_VIVO,
  id: "99999999-9999-4999-8999-999999999999",
  orden: 3,
  estado_publico: "PROGRAMA",
  iniciado_en: null,
  puntaje_1: null,
  puntaje_2: null,
  marcador_detalle: "",
  ganador_equipo_id: null,
  ganador_equipo_nombre: null,
  version: 1,
};

/** The whole public surface of the edition. */
export const ENCUENTROS_PUBLICOS = {
  edicion_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  edicion_nombre: "Salesianos Fest 2027",
  total: 3,
  en_vivo: [ENCUENTRO_EN_VIVO],
  proximos: [ENCUENTRO_PROGRAMADO],
  finalizados: [ENCUENTRO_FINALIZADO],
};
