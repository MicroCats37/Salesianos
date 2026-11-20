/**
 * The view models of the competitions area (`ADM-10`, `ADM-11`, `ADM-12`,
 * `ADM-13`).
 *
 * They are the VIEW CONTRACT of the area, and they are a faithful 1:1
 * projection of the PRESENTERS of the target backend, read directly from
 * `Aplicacion/backend/modules/competencias/presentation/schemas/competencias_schemas.py`:
 * `CompetenciaListadoOut`, `CompetenciaDetalleOut`, `CompetenciaEquipoOut`,
 * `RondaOut`, `EncuentroOut`, `ParticipanteOut`, `AgendaOut`,
 * `EquipoElegibleOut`, `AvancePreviewOut`, `CorreccionPreviewOut` and
 * `CorreccionImpactoOut`.
 *
 * The WIRE mirror lives NEXT to these types, in
 * `schemas/competencia.schema.ts`, and it is the one that parses the answers
 * of the server. These types are what the components draw, so they carry the
 * presentation decorations (the state, the role) and they never carry a
 * field that the presenter does not publish.
 *
 * `CompetenciasController` IS registered in
 * `Aplicacion/backend/config/api.py` and `modules.competencias` IS in
 * `LOCAL_APPS`, so its SIXTEEN routes EXIST at runtime: the area is BOUND and
 * `GET /competencias` is the read of the list of the edition.
 *
 * No business rule lives here. A winner, a bye, an advance, a correction, an
 * eligibility verdict and a schedule are DECLARED by the presenter and never
 * derived in the browser (`SH-01` T-03).
 */

/**
 * A fact of the backend with its label.
 *
 * The presenters publish machine CODES without wording (`estado`,
 * `motivo`). The interface never shows a code (`SH-03` §6), so the label
 * travels with the code and both are resolved by the ADAPTER
 * (`utils/competencias.estados.utils.ts`), never by the component.
 */
export interface EstadoDeclarado {
  /** The machine code, exactly as the backend sent it. */
  codigo: string;
  /** The wording the operator reads. */
  etiqueta: string;
}

/**
 * The visual bucket of a state.
 *
 * It says how the chip is painted, never what the state means (`SH-01` §3.2).
 * A bucket never travels alone: the icon shape and the label travel with it
 * so the colour is never the only signal (`SH-02` A11Y-11).
 */
export type RolEstado =
  | "en-curso"
  | "planificado"
  | "finalizado"
  | "borrador"
  | "cancelado"
  | "activo"
  | "retirado"
  | "elegible"
  | "bloqueado";

/** A state of the backend with the bucket that paints it. */
export interface EstadoConRol {
  estado: EstadoDeclarado;
  rol: RolEstado;
}

/** One slot of an encounter (`ParticipanteOut`). */
export interface ParticipanteEncuentro {
  /** `PARTICIPANTE_1` or `PARTICIPANTE_2`. */
  slot: string;
  /** The participation that fills the slot; `null` when the slot is free. */
  competencia_equipo_id: string | null;
  /** The registration team of the slot; `null` when the slot is free. */
  equipo_id: string | null;
  /** The name of the team; `null` when the slot is free. */
  equipo_nombre: string | null;
  /** The manual seed of the team in the bracket; `null` when the slot is free. */
  orden: number | null;
}

/**
 * An encounter (`EncuentroOut`).
 *
 * ONE shape for the three surfaces: the list of the detail, the agenda and
 * the bracket read the SAME encounter (`FL-11` paso 6, `GOV-02-RB-05a`).
 */
export interface Encuentro {
  id: string;
  ronda_id: string;
  ronda_etiqueta: string;
  ronda_orden: number;
  competencia_id: string;
  /** The order of the encounter inside its round. */
  orden: number;
  /** The operational state, as a code of `EstadoEncuentro`. */
  estado: string;
  /** Whether it is a manual bye. */
  es_bye: boolean;
  /** The two slots, in order. */
  participantes: ParticipanteEncuentro[];
  /** The scheduled start; `null` when it is not scheduled. */
  inicio_programado: string | null;
  /** The scheduled end; `null` when it is not scheduled. */
  fin_programado: string | null;
  /** The score of the first slot; `null` when there is no score. */
  puntaje_1: number | null;
  /** The score of the second slot; `null` when there is no score. */
  puntaje_2: number | null;
  /** The informative detail of the score. */
  marcador_detalle: string;
  /** The authoritative winner; it occupies one of the two slots. */
  ganador_equipo_id: string | null;
  /** The name of the winner. */
  ganador_equipo_nombre: string | null;
  /** The encounter the winner advances to. */
  siguiente_encuentro_id: string | null;
  /** The slot of the destination that receives the winner. */
  slot_destino: string | null;
  /** The moment it started; `null` when it did not start. */
  iniciado_en: string | null;
  /** The moment it ended; `null` when it did not end. */
  finalizado_en: string | null;
  /** The optimistic-lock version. */
  version: number;
  /** The actions the backend admits in this state (`proyeccion.py`). */
  acciones: string[];
}

/** A round of the bracket (`RondaOut`). */
export interface Ronda {
  id: string;
  etiqueta: string;
  orden: number;
  /** `ACTIVA` or `INVALIDADA`. */
  estado: string;
  version: number;
  encuentros: Encuentro[];
}

/** The participation of a team in the bracket (`CompetenciaEquipoOut`). */
export interface CompetenciaEquipo {
  id: string;
  equipo_id: string;
  equipo_nombre: string;
  /** The manual seed of the team in the bracket. */
  orden: number;
  /** `ACTIVO` or `RETIRADO`. */
  estado: string;
  version: number;
}

/** A row of the list of competitions (`CompetenciaListadoOut`). */
export interface CompetenciaListado {
  id: string;
  edicion_id: string;
  disciplina_id: string;
  disciplina_nombre: string;
  /**
   * The competitive band of the bracket.
   *
   * It is part of the IDENTITY of a competition: the browser prints it and
   * never derives it from the discipline or from the roster.
   */
  categoria_id: string;
  categoria_nombre: string;
  nombre: string;
  /** The state of the competition, as a code of `EstadoCompetencia`. */
  estado: string;
  /** The day of the competition, as `YYYY-MM-DD`. */
  fecha: string;
  /** The active teams of the bracket. */
  total_equipos: number;
  /** The encounters of the bracket. */
  total_encuentros: number;
  /** The finished encounters. */
  total_encuentros_finalizados: number;
}

/** The operational detail of a competition (`CompetenciaDetalleOut`). */
export interface CompetenciaDetalle {
  id: string;
  edicion_id: string;
  edicion_nombre: string;
  disciplina_id: string;
  disciplina_nombre: string;
  /** The competitive band of the bracket. */
  categoria_id: string;
  categoria_nombre: string;
  nombre: string;
  estado: string;
  fecha: string;
  version: number;
  equipos: CompetenciaEquipo[];
  rondas: Ronda[];
}

/** The transversal agenda of a day (`AgendaOut`). */
export interface AgendaCompetencias {
  edicion_id: string;
  edicion_nombre: string;
  fecha: string;
  /** The scheduled encounters of the day. */
  total: number;
  /** The encounters of the day, ordered by start time. */
  encuentros: Encuentro[];
}

/**
 * The eligibility verdict of a candidate team (`EquipoElegibleOut`).
 *
 * The verdict is the OWNER of the registration: this module publishes its
 * reason code and never guesses it (`QA-K01`).
 *
 * The band of the candidate travels WITH the verdict, so the interface can
 * name WHY a team is not eligible without comparing bands on its own.
 */
export interface EquipoElegible {
  equipo_id: string;
  nombre: string;
  edicion_id: string;
  disciplina_id: string;
  disciplina_nombre: string;
  /** The competitive band of the candidate team. */
  categoria_id: string;
  categoria_nombre: string;
  /** The state of the team in its registration. */
  estado: string;
  /** Whether the team can compete. */
  es_elegible: boolean;
  /** The reason code of `MotivoNoElegibilidad`. */
  motivo: string;
  /** The active participants of the team in the pool. */
  participantes_activos: number;
  /** The minimum the discipline requires. */
  minimo_requerido: number;
}

/**
 * A competitive band of the edition, as the catalogue of the registration
 * publishes it.
 *
 * The competitions area does not OWN the catalogue: it borrows the shape so
 * that the filter of the band can offer the options that the server
 * declares.
 */
export interface CategoriaDeEdicion {
  id: string;
  nombre: string;
}

/**
 * The preview of an advance (`AvancePreviewOut`).
 *
 * It NEVER WRITES: it describes what the advance WOULD do. The confirm is a
 * different action and a different route (`GOV-02-RB-05b`, `QA-K04`).
 */
export interface VistaPreviaAvance {
  encuentro_id: string;
  siguiente_encuentro_id: string;
  slot_destino: string;
  ganador_equipo_id: string;
  ganador_equipo_nombre: string;
  /** The team that occupies the destination slot today. */
  ocupante_actual_equipo_id: string | null;
  /** Whether the advance is already applied. */
  ya_propagado: boolean;
  /** Whether the destination already happened. */
  bloqueado: boolean;
  /** The business explanation of the block. */
  motivo_bloqueo: string | null;
  /** Whether the backend admits the confirm right now. */
  puede_confirmar: boolean;
}

/** The impact of a correction on one descendant (`CorreccionImpactoOut`). */
export interface ImpactoCorreccion {
  encuentro_id: string;
  slot: string;
  /** Whether the descendant already happened. */
  bloqueado: boolean;
  motivo_bloqueo: string | null;
  /** Whether the propagated value is replaced. */
  reemplaza: boolean;
  /** Whether the slot of the descendant is emptied. */
  limpia_slot: boolean;
  /** Whether the derived result of the descendant is annulled. */
  limpia_resultado: boolean;
  /** Whether the descendant really changes. */
  afecta: boolean;
}

/**
 * The preview of a correction (`CorreccionPreviewOut`).
 *
 * It NEVER WRITES. When a descendant already happened, the correction needs
 * an explicit authorisation (`requiere_override`) and a reason (`S-10`).
 */
export interface VistaPreviaCorreccion {
  encuentro_id: string;
  ganador_actual_equipo_id: string | null;
  ganador_nuevo_equipo_id: string;
  ganador_nuevo_equipo_nombre: string;
  /** Whether a descendant already happened. */
  requiere_override: boolean;
  /** How many descendants really change. */
  total_afectados: number;
  descendientes: ImpactoCorreccion[];
  /** Whether the backend admits the correction right now. */
  puede_confirmar: boolean;
}

/**
 * The parameters of the read of the list of competitions.
 *
 * They are the filters that `GET /competencias` ACCEPTS: `disciplina_id`,
 * `categoria_id` and `estado`. The EDITION is NOT one of them: the server
 * resolves it with the frozen resolution order (`FR-02` §2.2) and the client
 * never chooses it. There is no `page` either: the route publishes the WHOLE
 * list of the edition, so a page in the key would create a SECOND cache entry
 * for the SAME answer.
 */
export type ConsultaCompetenciasParams = {
  /** The discipline of the bracket. */
  disciplina_id?: string;
  /** The competitive band of the bracket. */
  categoria_id?: string;
  /** The state of the bracket, as a code of `EstadoCompetencia`. */
  estado?: string;
};

/**
 * The state a route is in.
 *
 * `sin-datos` is the state of a surface whose route is not connected; the
 * list of competitions IS connected, so its states are `cargando`, `listo`,
 * `sin-permiso` and `error`.
 */
export type EstadoVistaCompetencias =
  | "sin-datos"
  | "cargando"
  | "listo"
  | "sin-permiso"
  | "error";
