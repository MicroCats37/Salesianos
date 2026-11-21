import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";
import { participanteSchema } from "../../schemas/competencia.schema";

/**
 * The Zod mirror of the PUBLIC surface of the encounters.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * Contract: `contract/api-wrapper-presenter-contract.md` §7 (the mirror is 1:1)
 *
 * It is a 1:1 mirror of the presenters of the target backend
 * (`Aplicacion/backend/modules/competencias/presentation/schemas/competencias_schemas.py`):
 * `EncuentroPublicoOut` and `EncuentrosPublicosOut`, published by
 * `CompetenciasPublicoController` on `GET /publico/competencias/encuentros`.
 *
 * ## The rules of the mirror
 *
 * - **No `z.any()` and no generic field.** Every field is declared.
 * - **The machine codes are `string`, not enums.** The backend owns the
 *   vocabulary: a new public state must NOT break the whole read.
 * - **The winner is AUTHORITATIVE.** It travels as `ganador_equipo_id` and
 *   `ganador_equipo_nombre`; the client NEVER derives it from the score
 *   (`GOV-02-RB-05c`).
 * - **The `version` travels.** It is the optimistic-lock counter of the
 *   encounter, and a future realtime delta needs it to discard an obsolete
 *   event.
 * - **The participant shape is REUSED, not copied.** The public wrapper
 *   publishes the SAME `ParticipanteOut` of the backend, so the mirror of that
 *   block is the one of the administrative area
 *   (`schemas/competencia.schema.ts`).
 */

/** An identifier of the domain: `str` published by the presenter. */
const id = z.string().min(1);

/** A machine code published by the presenter. */
const codigo = z.string().min(1);

/** An instant published by the presenter (`datetime`). */
const marcaTiempo = z.string().min(1);

/**
 * An encounter in its PUBLIC shape (`EncuentroPublicoOut`).
 *
 * It is the canonical encounter of the backend (`EncuentroResult`) wrapped by
 * the public presenter: the DATA is the same one the agenda, the bracket and
 * the detail publish. The public shape adds the PUBLIC state and drops the
 * administrative affordances — the actions the backend admits and the wiring
 * of the bracket.
 */
export const encuentroPublicoSchema = z.object({
  id,
  ronda_id: id,
  ronda_etiqueta: z.string(),
  ronda_orden: z.number().int(),
  competencia_id: id,
  /** The order of the encounter inside its round. */
  orden: z.number().int(),
  /** The PUBLIC state: `PROGRAMA`, `EN_VIVO` or `FINALIZADO`. */
  estado_publico: codigo,
  /** Whether it is a manual bye. */
  es_bye: z.boolean(),
  /** The two slots, in order. */
  participantes: z.array(participanteSchema),
  /** The scheduled start; `null` when it is not scheduled. */
  inicio_programado: marcaTiempo.nullable(),
  /** The scheduled end; `null` when it is not scheduled. */
  fin_programado: marcaTiempo.nullable(),
  /** The moment it started; `null` when it did not start. */
  iniciado_en: marcaTiempo.nullable(),
  /** The moment it ended; `null` when it did not end. */
  finalizado_en: marcaTiempo.nullable(),
  /** The score of the first slot. It is INFORMATIVE: it never decides. */
  puntaje_1: z.number().int().nullable(),
  /** The score of the second slot. It is INFORMATIVE: it never decides. */
  puntaje_2: z.number().int().nullable(),
  /** The informative detail of the score. */
  marcador_detalle: z.string(),
  /** The authoritative winner; it occupies one of the two slots. */
  ganador_equipo_id: id.nullable(),
  /** The name of the winner. */
  ganador_equipo_nombre: z.string().nullable(),
  /** The optimistic-lock version: a future delta is discarded when it is older. */
  version: z.number().int(),
});

/**
 * The public surface of the edition (`EncuentrosPublicosOut`).
 *
 * The three buckets are the PRESENTATION the backend publishes: what is in
 * game, what comes and what already finished. They are disjoint and their
 * union is the whole public surface of the edition.
 */
export const encuentrosPublicosSchema = z.object({
  edicion_id: id,
  edicion_nombre: z.string(),
  /** The publishable encounters of the edition, in the three buckets. */
  total: z.number().int(),
  /** The encounters in game. */
  en_vivo: z.array(encuentroPublicoSchema),
  /** The encounters of the programme, the closest first. */
  proximos: z.array(encuentroPublicoSchema),
  /** The encounters with a result, the most recent first. */
  finalizados: z.array(encuentroPublicoSchema),
});

/** The envelope of the public read (`GET /publico/competencias/encuentros`). */
export const encuentrosPublicosEnvelope = apiResponseSchema(
  encuentrosPublicosSchema,
);

export type EncuentroPublico = z.infer<typeof encuentroPublicoSchema>;
export type EncuentrosPublicos = z.infer<typeof encuentrosPublicosSchema>;
