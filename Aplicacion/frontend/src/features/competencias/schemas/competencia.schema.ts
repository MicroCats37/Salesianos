import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The Zod mirrors of the COMPETITIONS area (`DOM-07`).
 *
 * They are a 1:1 mirror of the presenters and of the input schemas of the
 * target backend
 * (`Aplicacion/backend/modules/competencias/presentation/schemas/competencias_schemas.py`):
 * `ParticipanteOut`, `EncuentroOut`, `RondaOut`, `CompetenciaEquipoOut`,
 * `CompetenciaListadoOut`, `CompetenciaDetalleOut`, `AgendaOut`,
 * `EquipoElegibleOut`, `ResultadoRegistradoOut`, `AvancePreviewOut`,
 * `AvanceOut`, `CorreccionImpactoOut`, `CorreccionPreviewOut` and
 * `CorreccionOut`; plus the ten `*In` schemas of the writes.
 *
 * ## THE RULES OF THE MIRROR
 *
 * - **No `z.any()` and no generic field.** Every field is declared.
 * - **The envelope is the FROZEN one** (`FREEZE-ENV-1.0.0`): the factory
 *   `apiResponseSchema` of the project builds it, and the pagination lives
 *   INSIDE `data` as `{ items, total, page, page_size, total_pages }`.
 * - **The machine codes are `string`, not enums.** The backend owns the
 *   vocabulary and a new value must NOT break the whole read.
 * - **The optimistic-lock version is a NUMBER** and it travels in EVERY write
 *   (`expected_version`): the client never decides whether a write is current.
 * - **The previews NEVER write.** They are separate schemas from the
 *   confirmations, and the separation is visible in the names.
 *
 * ## THIS MIRROR IS BOUND
 *
 * `CompetenciasController` IS registered in
 * `Aplicacion/backend/config/api.py` and `modules.competencias` IS in
 * `LOCAL_APPS`, so its SIXTEEN routes EXIST at runtime. The list of the
 * edition is bound by `features/competencias/services/competencia.service.ts`
 * and the mirror below is what parses its answer.
 *
 * The `*In` schemas are mirrored for the same reason and with the same
 * honesty: they are the exact wire shapes of the writes, including the
 * `expected_version` of the optimistic lock and the `override` +
 * `acepta_impacto` pair of the correction, so that the moment the routes
 * exist the payloads are already right.
 */

/**
 * An identifier of the domain.
 *
 * `DOM-07` declares its identifiers as `str` (not `UUID`): the mirror is 1:1
 * with the declared type, so a non-UUID value published tomorrow does not
 * break the whole read.
 */
const id = z.string().min(1);

/** A machine code published by the presenter. */
const codigo = z.string().min(1);

/** An instant published by the presenter (`datetime`). */
const marcaTiempo = z.string().min(1);

/** A day published by the presenter (`date`). */
const fecha = z.string().min(1);

// ── Salidas ───────────────────────────────────────────────────────────────────

/** One slot of an encounter (`ParticipanteOut`). */
export const participanteSchema = z.object({
  /** `PARTICIPANTE_1` or `PARTICIPANTE_2`. */
  slot: codigo,
  /** The participation that fills the slot; `null` when the slot is free. */
  competencia_equipo_id: id.nullable(),
  /** The registration team of the slot; `null` when the slot is free. */
  equipo_id: id.nullable(),
  /** The name of the team; `null` when the slot is free. */
  equipo_nombre: z.string().nullable(),
  /** The manual seed of the team in the bracket; `null` when the slot is free. */
  orden: z.number().int().nullable(),
});

/**
 * An encounter (`EncuentroOut`).
 *
 * ONE shape for the three surfaces: the list of the detail, the agenda and
 * the bracket read the SAME encounter (`FL-11` paso 6). The winner is
 * AUTHORITATIVE: it travels as `ganador_equipo_id` and the client never
 * derives it from the score (`GOV-02-RB-05c`).
 */
export const encuentroSchema = z.object({
  id,
  ronda_id: id,
  ronda_etiqueta: z.string(),
  ronda_orden: z.number().int(),
  competencia_id: id,
  /** The order of the encounter inside its round. */
  orden: z.number().int(),
  /** The operational state, as a code of `EstadoEncuentro`. */
  estado: codigo,
  /** Whether it is a manual bye. */
  es_bye: z.boolean(),
  /** The two slots, in order. */
  participantes: z.array(participanteSchema),
  /** The scheduled start; `null` when it is not scheduled. */
  inicio_programado: marcaTiempo.nullable(),
  /** The scheduled end; `null` when it is not scheduled. */
  fin_programado: marcaTiempo.nullable(),
  /** The score of the first slot; `null` when there is no score. */
  puntaje_1: z.number().int().nullable(),
  /** The score of the second slot; `null` when there is no score. */
  puntaje_2: z.number().int().nullable(),
  /** The informative detail of the score. */
  marcador_detalle: z.string(),
  /** The authoritative winner; it occupies one of the two slots. */
  ganador_equipo_id: id.nullable(),
  /** The name of the winner. */
  ganador_equipo_nombre: z.string().nullable(),
  /** The encounter the winner advances to. */
  siguiente_encuentro_id: id.nullable(),
  /** The slot of the destination that receives the winner. */
  slot_destino: codigo.nullable(),
  /** The moment it started; `null` when it did not start. */
  iniciado_en: marcaTiempo.nullable(),
  /** The moment it ended; `null` when it did not end. */
  finalizado_en: marcaTiempo.nullable(),
  /** The optimistic-lock version. */
  version: z.number().int(),
  /** The actions the backend admits in this state. */
  acciones: z.array(codigo),
});

/** A round of the bracket (`RondaOut`). */
export const rondaSchema = z.object({
  id,
  etiqueta: z.string(),
  orden: z.number().int(),
  /** `ACTIVA` or `INVALIDADA`. */
  estado: codigo,
  version: z.number().int(),
  /** The encounters of the round, in order. */
  encuentros: z.array(encuentroSchema),
});

/** The participation of a team in the bracket (`CompetenciaEquipoOut`). */
export const competenciaEquipoSchema = z.object({
  id,
  equipo_id: id,
  equipo_nombre: z.string(),
  /** The manual seed of the team in the bracket. */
  orden: z.number().int(),
  /** `ACTIVO` or `RETIRADO`. */
  estado: codigo,
  version: z.number().int(),
});

/** A row of the list of competitions (`CompetenciaListadoOut`). */
export const competenciaListadoSchema = z.object({
  id,
  edicion_id: id,
  disciplina_id: id,
  disciplina_nombre: z.string(),
  /**
   * The competitive band of the bracket.
   *
   * The band is part of the IDENTITY of a competition: two brackets of the
   * same discipline and the same day are two competitions when their bands
   * differ. The client never derives it: it prints the band that the server
   * published.
   */
  categoria_id: id,
  categoria_nombre: z.string(),
  nombre: z.string(),
  /** The state of the competition, as a code of `EstadoCompetencia`. */
  estado: codigo,
  /** The day of the competition. */
  fecha,
  /** The active teams of the bracket. */
  total_equipos: z.number().int(),
  /** The encounters of the bracket. */
  total_encuentros: z.number().int(),
  /** The finished encounters. */
  total_encuentros_finalizados: z.number().int(),
});

/** The operational detail of a competition (`CompetenciaDetalleOut`). */
export const competenciaDetalleSchema = z.object({
  id,
  edicion_id: id,
  edicion_nombre: z.string(),
  disciplina_id: id,
  disciplina_nombre: z.string(),
  /** The competitive band of the bracket. */
  categoria_id: id,
  categoria_nombre: z.string(),
  nombre: z.string(),
  estado: codigo,
  fecha,
  version: z.number().int(),
  /** The teams of the bracket. */
  equipos: z.array(competenciaEquipoSchema),
  /** The rounds of the bracket, in order. */
  rondas: z.array(rondaSchema),
});

/** The transversal agenda of a day (`AgendaOut`). */
export const agendaSchema = z.object({
  edicion_id: id,
  edicion_nombre: z.string(),
  fecha,
  /** The scheduled encounters of the day. */
  total: z.number().int(),
  /** The encounters of the day, ordered by start time. */
  encuentros: z.array(encuentroSchema),
});

/**
 * The eligibility verdict of a candidate team (`EquipoElegibleOut`).
 *
 * The verdict is the OWNER of the registration: the module publishes the
 * reason code of `MotivoNoElegibilidad` and the client NEVER derives it
 * (`QA-K01`).
 *
 * The band of the candidate travels WITH the verdict, so the interface can
 * say WHY a team is not eligible without comparing bands on its own: the
 * reason code already carries the answer (`CATEGORIA_DISTINTA`,
 * `CATEGORIA_NO_ASIGNADA`).
 */
export const equipoElegibleSchema = z.object({
  equipo_id: id,
  nombre: z.string(),
  edicion_id: id,
  disciplina_id: id,
  disciplina_nombre: z.string(),
  /** The competitive band of the candidate team. */
  categoria_id: id,
  categoria_nombre: z.string(),
  /** The state of the team in its registration. */
  estado: codigo,
  /** Whether the team can compete. */
  es_elegible: z.boolean(),
  /** The reason code of `MotivoNoElegibilidad`. */
  motivo: codigo,
  /** The active participants of the team in the pool. */
  participantes_activos: z.number().int(),
  /** The minimum the discipline requires. */
  minimo_requerido: z.number().int(),
});

/** The authoritative result already registered (`ResultadoRegistradoOut`). */
export const resultadoRegistradoSchema = z.object({
  /** The encounter, already finished. */
  encuentro: encuentroSchema,
  ganador_equipo_id: id,
  ganador_equipo_nombre: z.string(),
});

/**
 * The preview of an advance (`AvancePreviewOut`).
 *
 * It NEVER WRITES: it describes what the advance WOULD do. The confirm is a
 * different schema and a different route (`GOV-02-RB-05b`, `QA-K04`).
 */
export const avancePreviewSchema = z.object({
  encuentro_id: id,
  siguiente_encuentro_id: id,
  /** The slot of the destination that would receive the winner. */
  slot_destino: codigo,
  ganador_equipo_id: id,
  ganador_equipo_nombre: z.string(),
  /** The team that occupies the destination slot today. */
  ocupante_actual_equipo_id: id.nullable(),
  /** Whether the advance is already applied. */
  ya_propagado: z.boolean(),
  /** Whether the destination already happened. */
  bloqueado: z.boolean(),
  /** The business explanation of the block. */
  motivo_bloqueo: z.string().nullable(),
  /** Whether the backend admits the confirm right now. */
  puede_confirmar: z.boolean(),
});

/** The confirmed advance (`AvanceOut`). */
export const avanceSchema = z.object({
  encuentro_origen_id: id,
  siguiente_encuentro_id: id,
  /** The slot of the destination that received the winner. */
  slot_destino: codigo,
  ganador_equipo_id: id,
  ganador_equipo_nombre: z.string(),
  /** Whether the advance was already applied. */
  ya_aplicado: z.boolean(),
  /** The destination, already updated. */
  destino: encuentroSchema,
});

/** The impact of a correction on one descendant (`CorreccionImpactoOut`). */
export const correccionImpactoSchema = z.object({
  encuentro_id: id,
  slot: codigo,
  /** Whether the descendant already happened. */
  bloqueado: z.boolean(),
  /** The business explanation of the block. */
  motivo_bloqueo: z.string().nullable(),
  /** Whether the propagated value is replaced. */
  reemplaza: z.boolean(),
  /** Whether the slot of the descendant is emptied. */
  limpia_slot: z.boolean(),
  /** Whether the derived result of the descendant is annulled. */
  limpia_resultado: z.boolean(),
  /** Whether the descendant really changes. */
  afecta: z.boolean(),
});

/**
 * The preview of a correction (`CorreccionPreviewOut`).
 *
 * It NEVER WRITES. When a descendant already happened, the correction needs
 * an explicit authorisation (`requiere_override`) and a reason (`S-10`).
 */
export const correccionPreviewSchema = z.object({
  encuentro_id: id,
  /** The current winner, when there is one. */
  ganador_actual_equipo_id: id.nullable(),
  ganador_nuevo_equipo_id: id,
  ganador_nuevo_equipo_nombre: z.string(),
  /** Whether a descendant already happened. */
  requiere_override: z.boolean(),
  /** How many descendants really change. */
  total_afectados: z.number().int(),
  /** The impact on each descendant of the chain. */
  descendientes: z.array(correccionImpactoSchema),
  /** Whether the backend admits the correction right now. */
  puede_confirmar: z.boolean(),
});

/** The applied correction (`CorreccionOut`). */
export const correccionSchema = z.object({
  encuentro_id: id,
  ganador_nuevo_equipo_id: id,
  ganador_nuevo_equipo_nombre: z.string(),
  /** How many descendants really changed. */
  descendientes_afectados: z.number().int(),
  /** Whether the cascade was applied with the explicit authorisation. */
  override_aplicado: z.boolean(),
  /** The corrected encounter. */
  encuentro: encuentroSchema,
  /** The applied impact on each descendant. */
  descendientes: z.array(correccionImpactoSchema),
});

// ── Entradas ─────────────────────────────────────────────────────────────────

/**
 * The creation of a competition (`CompetenciaCrearIn`).
 *
 * `categoria_id` is REQUIRED: the band is part of the identity of a
 * competition, so a bracket without a band is not a bracket.
 */
export const competenciaCrearSchema = z.object({
  disciplina_id: id,
  categoria_id: id,
  nombre: z.string().min(1).max(200),
  fecha,
});

/** The incorporation of a team into the bracket (`EquipoIncorporarIn`). */
export const equipoIncorporarSchema = z.object({
  equipo_id: id,
  /** The manual seed in the bracket. */
  orden: z.number().int().min(1).max(999),
});

/**
 * The edition of a team of the bracket (`EquipoEditarIn`).
 *
 * `expected_version` is REQUIRED: the optimistic lock is not optional
 * (`D-DOM07-07`).
 */
export const equipoEditarSchema = z.object({
  /** The new manual seed; `null` means "not touched". */
  orden: z.number().int().min(1).max(999).nullable().optional(),
  /** The new state: `ACTIVO` or `RETIRADO`. */
  estado: codigo.nullable().optional(),
  expected_version: z.number().int(),
  /** The audited reason of the operation. */
  motivo: z.string().max(500).nullable().optional(),
});

/** The creation of a round (`RondaCrearIn`). */
export const rondaCrearSchema = z.object({
  etiqueta: z.string().min(1).max(80),
  orden: z.number().int().min(1).max(999),
});

/** The creation of an encounter (`EncuentroCrearIn`). */
export const encuentroCrearSchema = z.object({
  ronda_id: id,
  orden: z.number().int(),
});

/**
 * The edition of an encounter (`EncuentroActualizarIn`).
 *
 * An ABSENT field means "not touched" and an explicit `null` empties the
 * nullable ones. The two are NOT the same and the wire keeps them apart.
 */
export const encuentroActualizarSchema = z.object({
  /** The participation of the slot 1; an explicit `null` empties it. */
  participante_1_id: id.nullable().optional(),
  /** The participation of the slot 2; an explicit `null` empties it. */
  participante_2_id: id.nullable().optional(),
  inicio_programado: marcaTiempo.nullable().optional(),
  fin_programado: marcaTiempo.nullable().optional(),
  siguiente_encuentro_id: id.nullable().optional(),
  slot_destino: codigo.nullable().optional(),
  es_bye: z.boolean().optional(),
  /** `PROGRAMADO`, `EN_CURSO` or `CANCELADO`. */
  estado: codigo.nullable().optional(),
  /** The audited reason of the operation. */
  motivo: z.string().max(500).nullable().optional(),
  expected_version: z.number().int(),
});

/** The registration of the authoritative result (`ResultadoRegistrarIn`). */
export const resultadoRegistrarSchema = z.object({
  /** The winning participation: it must occupy one of the two slots. */
  ganador_id: id,
  puntaje_1: z.number().int().min(0).nullable().optional(),
  puntaje_2: z.number().int().min(0).nullable().optional(),
  marcador_detalle: z.string().max(500).nullable().optional(),
  motivo: z.string().max(500).nullable().optional(),
  expected_version: z.number().int(),
});

/** The confirmation of the advance (`AvanceConfirmarIn`). */
export const avanceConfirmarSchema = z.object({
  motivo: z.string().max(500).nullable().optional(),
  expected_version: z.number().int(),
});

/** The preview of the impact of a correction (`CorreccionPrevisualizarIn`). */
export const correccionPrevisualizarSchema = z.object({
  /** The new winning participation: it must occupy one of the two slots. */
  ganador_id: id,
});

/**
 * The application of the correction (`CorreccionAplicarIn`).
 *
 * The reason is MANDATORY and the cascade needs BOTH `override` AND
 * `acepta_impacto`: without the two of them, nothing is written
 * (`D-DOM07-05` / `QA-K03`).
 */
export const correccionAplicarSchema = z.object({
  ganador_id: id,
  /** The MANDATORY audited reason of the correction. */
  motivo: z.string().max(500).nullable(),
  /** The explicit authorisation to correct a descendant that already happened. */
  override: z.boolean(),
  /** The administrator accepts the calculated impact. */
  acepta_impacto: z.boolean(),
  expected_version: z.number().int(),
});

// ── Envelopes ────────────────────────────────────────────────────────────────

/** The list of competitions (`GET /competencias`). */
export const competenciasListaEnvelope = apiResponseSchema(
  z.array(competenciaListadoSchema),
);

/** The detail of a competition (`GET /competencias/{id}`). */
export const competenciaDetalleEnvelope = apiResponseSchema(
  competenciaDetalleSchema,
);

export const competenciaEquipoEnvelope = apiResponseSchema(
  competenciaEquipoSchema,
);

/** The bracket of a competition (`GET /competencias/{id}/cuadro`). */
export const cuadroEnvelope = apiResponseSchema(z.array(rondaSchema));

/**
 * ONE encounter (`PATCH /competencias/{id}/encuentros/{encuentro_id}`).
 *
 * The update of an encounter answers with the encounter ITSELF: the operator
 * sees the state the server committed, not the one the browser predicted.
 */
export const encuentroEnvelope = apiResponseSchema(encuentroSchema);

/** The agenda of a day (`GET /competencias/agenda`). */
export const agendaEnvelope = apiResponseSchema(agendaSchema);

/** The eligible teams of a competition (`GET /competencias/{id}/equipos-elegibles`). */
export const equiposElegiblesEnvelope = apiResponseSchema(
  z.array(equipoElegibleSchema),
);

/** The preview of the advance (`POST …/avance/preview`). */
export const avancePreviewEnvelope = apiResponseSchema(avancePreviewSchema);

/** The confirmed advance (`POST …/avance`). */
export const avanceEnvelope = apiResponseSchema(avanceSchema);

/** The preview of the correction (`POST …/correccion/preview`). */
export const correccionPreviewEnvelope = apiResponseSchema(
  correccionPreviewSchema,
);

/** The applied correction (`POST …/correccion`). */
export const correccionEnvelope = apiResponseSchema(correccionSchema);

/** The registered result (`POST …/resultado`). */
export const resultadoRegistradoEnvelope = apiResponseSchema(
  resultadoRegistradoSchema,
);

// ── Inferred types ───────────────────────────────────────────────────────────

export type Participante = z.infer<typeof participanteSchema>;
export type Encuentro = z.infer<typeof encuentroSchema>;
export type Ronda = z.infer<typeof rondaSchema>;
export type CompetenciaEquipo = z.infer<typeof competenciaEquipoSchema>;
export type CompetenciaListado = z.infer<typeof competenciaListadoSchema>;
export type CompetenciaDetalle = z.infer<typeof competenciaDetalleSchema>;
export type AgendaCompetencias = z.infer<typeof agendaSchema>;
export type EquipoElegible = z.infer<typeof equipoElegibleSchema>;
export type ResultadoRegistrado = z.infer<typeof resultadoRegistradoSchema>;
export type VistaPreviaAvance = z.infer<typeof avancePreviewSchema>;
export type Avance = z.infer<typeof avanceSchema>;
export type ImpactoCorreccion = z.infer<typeof correccionImpactoSchema>;
export type VistaPreviaCorreccion = z.infer<typeof correccionPreviewSchema>;
export type Correccion = z.infer<typeof correccionSchema>;

export type CompetenciaCrear = z.infer<typeof competenciaCrearSchema>;
export type EquipoIncorporar = z.infer<typeof equipoIncorporarSchema>;
export type EquipoEditar = z.infer<typeof equipoEditarSchema>;
export type RondaCrear = z.infer<typeof rondaCrearSchema>;
export type EncuentroCrear = z.infer<typeof encuentroCrearSchema>;
export type EncuentroActualizar = z.infer<typeof encuentroActualizarSchema>;
export type ResultadoRegistrar = z.infer<typeof resultadoRegistrarSchema>;
export type AvanceConfirmar = z.infer<typeof avanceConfirmarSchema>;
export type CorreccionPrevisualizar = z.infer<
  typeof correccionPrevisualizarSchema
>;
export type CorreccionAplicar = z.infer<typeof correccionAplicarSchema>;
