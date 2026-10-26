import { z } from "zod";
import { AdminErrorSchema } from "@/features/admin/schemas";

/**
 * Zod mirrors of the payloads of the `competencias` module (Phase 4).
 *
 * Source of truth: `backend/modules/competencias/presentation/schemas/competencias_schemas.py`.
 *
 * The rules of the mirror:
 *
 * - ONE mirror per backend payload, never one per view: the list row, the
 *   detail, the bracket and the agenda all reuse the same blocks
 *   (`contract/SCHEMA_DRY_INTENTION.md`).
 * - Every wrapper is EXPLICIT: there is no generic `data` / `contexto`
 *   envelope and no `z.any()` anywhere
 *   (`contract/api-wrapper-presenter-contract.md` §5 and §7).
 * - `date` and `datetime` are typed as STRINGS on purpose: the backend
 *   serializes a `date` as `YYYY-MM-DD` and a `datetime` as a naive ISO-8601
 *   instant, and a strict ISO validator would reject valid payloads.
 * - `marcador_detalle` is the ONLY nullable free text: the shared
 *   `BaseSchema` of the backend normalizes an empty string to `None`, so the
 *   mirror accepts both the empty string and the null.
 */

/** Mirror 1:1 of `CompetenciaListOut` — the row of the list. */
export const CompetenciaListaItemSchema = z.object({
  id: z.string(),
  evento_id: z.string(),
  disciplina_id: z.string(),
  categoria_id: z.string(),
  nombre: z.string(),
  fecha: z.string(),
  estado: z.string(),
  version: z.number(),
  total_equipos: z.number(),
  total_encuentros: z.number(),
  total_encuentros_finalizados: z.number(),
});

export type CompetenciaListaItem = z.infer<typeof CompetenciaListaItemSchema>;

/** Mirror 1:1 of `CompetenciaEquipoOut` — the participation of a team. */
export const CompetenciaEquipoSchema = z.object({
  id: z.string(),
  competencia_id: z.string(),
  equipo_id: z.string(),
  equipo_nombre: z.string(),
  orden: z.number(),
  estado: z.string(),
  version: z.number(),
});

export type CompetenciaEquipo = z.infer<typeof CompetenciaEquipoSchema>;

/** Mirror 1:1 of `RondaOut` — a round of the bracket. */
export const RondaSchema = z.object({
  id: z.string(),
  competencia_id: z.string(),
  etiqueta: z.string(),
  orden: z.number(),
  estado: z.string(),
  version: z.number(),
  total_encuentros: z.number(),
});

export type Ronda = z.infer<typeof RondaSchema>;

/** Mirror 1:1 of `EncuentroOut` — an encounter of the bracket. */
export const EncuentroSchema = z.object({
  id: z.string(),
  ronda_id: z.string(),
  ronda_etiqueta: z.string().nullable(),
  ronda_orden: z.number().nullable(),
  competencia_id: z.string().nullable(),
  competencia_nombre: z.string().nullable(),
  orden: z.number(),
  participante_1_id: z.string().nullable(),
  participante_1_nombre: z.string().nullable(),
  participante_2_id: z.string().nullable(),
  participante_2_nombre: z.string().nullable(),
  inicio_programado: z.string().nullable(),
  fin_programado: z.string().nullable(),
  estado: z.string(),
  estado_pre_suspension: z.string().nullable(),
  iniciado_en: z.string().nullable(),
  finalizado_en: z.string().nullable(),
  es_bye: z.boolean(),
  ganador_id: z.string().nullable(),
  puntaje_1: z.number().nullable(),
  puntaje_2: z.number().nullable(),
  marcador_detalle: z.string().nullable(),
  siguiente_encuentro_id: z.string().nullable(),
  slot_destino: z.string().nullable(),
  ganador_propagado_id: z.string().nullable(),
  version: z.number(),
});

export type Encuentro = z.infer<typeof EncuentroSchema>;

/**
 * Mirror 1:1 of `CompetenciaDetalleOut` — the detail INHERITS the row of the
 * list instead of repeating its fields (`contract/SCHEMA_DRY_INTENTION.md`).
 */
export const CompetenciaDetalleSchema = CompetenciaListaItemSchema.extend({
  created_at: z.string(),
  equipos: z.array(CompetenciaEquipoSchema),
  rondas: z.array(RondaSchema),
});

export type CompetenciaDetalle = z.infer<typeof CompetenciaDetalleSchema>;

/** Mirror 1:1 of `RondaCuadroOut` — a column of the bracket. */
export const RondaCuadroSchema = z.object({
  id: z.string(),
  etiqueta: z.string(),
  orden: z.number(),
  estado: z.string(),
  encuentros: z.array(EncuentroSchema),
});

export type RondaCuadro = z.infer<typeof RondaCuadroSchema>;

/** Mirror 1:1 of `CuadroOut` — the bracket of a competition. */
export const CuadroSchema = z.object({
  competencia_id: z.string(),
  nombre: z.string(),
  fecha: z.string(),
  estado: z.string(),
  total_equipos: z.number(),
  rondas: z.array(RondaCuadroSchema),
});

export type Cuadro = z.infer<typeof CuadroSchema>;

/** Mirror 1:1 of `AgendaOut` — the agenda of ONE day. */
export const AgendaSchema = z.object({
  fecha: z.string(),
  total: z.number(),
  encuentros: z.array(EncuentroSchema),
});

export type Agenda = z.infer<typeof AgendaSchema>;

/**
 * Factory of the 1:1 mirror of the backend `core.responses.ApiResponse`
 * envelope.
 *
 * The envelope is COMPOSED, never duplicated per endpoint, and the payload
 * type stays EXPLICIT: there is no generic `data` contract and no `z.any()`
 * (`contract/api-wrapper-presenter-contract.md` §5 and §7).
 */
export function competenciaEnvelopeSchema<TData extends z.ZodType>(
  data: TData,
) {
  return z.object({
    success: z.boolean(),
    data: data.nullable(),
    error: AdminErrorSchema.nullable(),
    message: z.string().nullable(),
  });
}

/** Envelope of `GET /administracion/competencias`. */
export const CompetenciasListaEnvelopeSchema = competenciaEnvelopeSchema(
  z.array(CompetenciaListaItemSchema),
);

export type CompetenciasListaEnvelope = z.infer<
  typeof CompetenciasListaEnvelopeSchema
>;

/** Envelope of `GET /administracion/competencias/{id}`. */
export const CompetenciaDetalleEnvelopeSchema = competenciaEnvelopeSchema(
  CompetenciaDetalleSchema,
);

export type CompetenciaDetalleEnvelope = z.infer<
  typeof CompetenciaDetalleEnvelopeSchema
>;

/** Envelope of `GET /administracion/competencias/{id}/cuadro`. */
export const CuadroEnvelopeSchema = competenciaEnvelopeSchema(CuadroSchema);

export type CuadroEnvelope = z.infer<typeof CuadroEnvelopeSchema>;

/** Envelope of `GET /administracion/competencias/agenda`. */
export const AgendaEnvelopeSchema = competenciaEnvelopeSchema(AgendaSchema);

export type AgendaEnvelope = z.infer<typeof AgendaEnvelopeSchema>;
