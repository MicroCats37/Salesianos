import { z } from "zod";
import {
  CompetenciaEquipoSchema,
  competenciaEnvelopeSchema,
  EncuentroSchema,
  RondaSchema,
} from "./competencias.schema";

/**
 * Zod mirrors of the WRITE payloads of the `competencias` module (Phase 5).
 *
 * Source of truth: `backend/modules/competencias/presentation/schemas/competencias_schemas.py`.
 *
 * The rules of the mirror (the same ones of the read mirror):
 *
 * - ONE mirror per backend payload, never one per view
 *   (`contract/SCHEMA_DRY_INTENTION.md`): the FORM schema of every editor is
 *   DERIVED from its payload schema with `.omit({ expected_version: true })`,
 *   so the form and the request can never drift apart.
 * - Every wrapper is EXPLICIT: no generic `data` envelope and no `z.any()`
 *   (`contract/api-wrapper-presenter-contract.md` §5 and §7).
 * - The motive of a protected mutation is 5..500 characters: that is the rule
 *   of the DOMAIN (`base_service.MINIMO_MOTIVO` / `MAXIMO_MOTIVO`), mirrored
 *   here only as an aid for the administrator. The backend stays
 *   authoritative and answers 422 `REASON_REQUIRED` when the motive does not
 *   comply (`contract/django-app-architecture-contract.md` §10).
 * - The optimistic lock (`expected_version`) is NOT a form field: it is the
 *   version the server returned, and the mutation hook adds it to the
 *   payload. The administrator never types it.
 */

/** Identifier of an entity of the module (the backend parses it as UUID). */
const identificadorSchema = z.uuid("El identificador no es válido.");

/**
 * An OPTIONAL identifier: an empty text travels as "no participant".
 *
 * It is the way the editors express a slot that is still empty: the bracket
 * stays partial and nothing is invented.
 */
const identificadorOpcionalSchema = z.preprocess(
  (valor) => (typeof valor === "string" && valor.trim() === "" ? null : valor),
  identificadorSchema.nullable(),
);

/**
 * The MANUAL order of a team, a round or an encounter.
 *
 * The numeric input of the shared form sends `NaN` when it is empty: the
 * preprocessor turns it into "not filled" so the message is the one of the
 * administrator and not the technical one of Zod.
 */
const ordenSchema = z.preprocess(
  (valor) =>
    typeof valor === "number" && Number.isNaN(valor) ? undefined : valor,
  z
    .number({ error: "Indica el orden." })
    .int()
    .min(1, "El orden empieza en 1."),
);

/** The audited motive of a protected mutation (the DOMAIN rule: 5..500). */
const motivoSchema = z
  .string()
  .trim()
  .min(5, "Explica el motivo (mínimo 5 caracteres).")
  .max(500, "El motivo no puede superar los 500 caracteres.");

/** An OPTIONAL audited motive: an empty text travels as "no motive". */
const motivoOpcionalSchema = z.preprocess(
  (valor) => (typeof valor === "string" && valor.trim() === "" ? null : valor),
  motivoSchema.nullable(),
);

/** An optional score: it is informative and never determines the winner. */
const puntajeOpcionalSchema = z.preprocess(
  (valor) =>
    valor === "" || valor === null || valor === undefined
      ? null
      : Number(valor),
  z.number().int().min(0, "El puntaje no puede ser negativo.").nullable(),
);

/** The version the server returned: the optimistic lock of every mutation. */
const versionEsperadaSchema = z.number().int().min(1);

/** A day of the schedule (`YYYY-MM-DD`). */
const fechaSchema = z
  .string()
  .trim()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "Indica la fecha como AAAA-MM-DD.");

/** A time of the schedule (`HH:mm`). */
const horaSchema = z
  .string()
  .trim()
  .regex(/^([01]\d|2[0-3]):[0-5]\d$/, "Indica la hora como HH:mm.");

// ── Equipos y semillas ───────────────────────────────────────────────────────

/** Mirror 1:1 of `CompetenciaEquipoCreateIn`. */
export const CompetenciaEquipoCreatePayloadSchema = z.object({
  equipo_id: identificadorSchema,
  orden: ordenSchema,
});

export type CompetenciaEquipoCreatePayload = z.infer<
  typeof CompetenciaEquipoCreatePayloadSchema
>;

/** Mirror 1:1 of `CompetenciaEquipoUpdateIn`. */
export const CompetenciaEquipoUpdatePayloadSchema = z.object({
  orden: ordenSchema.nullable(),
  estado: z.enum(["ACTIVO", "RETIRADO"]).nullable(),
  motivo: motivoSchema.nullable(),
  expected_version: versionEsperadaSchema,
});

export type CompetenciaEquipoUpdatePayload = z.infer<
  typeof CompetenciaEquipoUpdatePayloadSchema
>;

// ── Rondas ────────────────────────────────────────────────────────────────────

/** Mirror 1:1 of `RondaCreateIn`. */
export const RondaCreatePayloadSchema = z.object({
  etiqueta: z
    .string()
    .trim()
    .min(1, "Indica la etiqueta de la ronda.")
    .max(100),
  orden: ordenSchema,
});

export type RondaCreatePayload = z.infer<typeof RondaCreatePayloadSchema>;

/** Mirror 1:1 of `RondaUpdateIn`. */
export const RondaUpdatePayloadSchema = z.object({
  etiqueta: z.string().trim().min(1).max(100).nullable(),
  orden: ordenSchema.nullable(),
  motivo: motivoSchema.nullable(),
  expected_version: versionEsperadaSchema,
});

export type RondaUpdatePayload = z.infer<typeof RondaUpdatePayloadSchema>;

// ── Encuentros ───────────────────────────────────────────────────────────────

/**
 * Mirror 1:1 of `EncuentroCreateIn`.
 *
 * Both participants are OPTIONAL on purpose: an empty or partial bracket
 * must stay editable without inventing a participant.
 */
export const EncuentroCreatePayloadSchema = z.object({
  ronda_id: identificadorSchema,
  orden: ordenSchema,
  participante_1_id: identificadorOpcionalSchema,
  participante_2_id: identificadorOpcionalSchema,
});

export type EncuentroCreatePayload = z.infer<
  typeof EncuentroCreatePayloadSchema
>;

/** Mirror 1:1 of `EncuentroParticipantesIn` (moving a slot needs a motive). */
export const EncuentroParticipantesPayloadSchema = z.object({
  participante_1_id: identificadorOpcionalSchema,
  participante_2_id: identificadorOpcionalSchema,
  motivo: motivoSchema.nullable(),
  expected_version: versionEsperadaSchema,
});

export type EncuentroParticipantesPayload = z.infer<
  typeof EncuentroParticipantesPayloadSchema
>;

/** Mirror 1:1 of `EncuentroProgramacionIn`. */
export const EncuentroProgramacionPayloadSchema = z.object({
  inicio_programado: z.string().min(1),
  fin_programado: z.string().min(1),
  motivo: motivoSchema.nullable(),
  expected_version: versionEsperadaSchema,
});

export type EncuentroProgramacionPayload = z.infer<
  typeof EncuentroProgramacionPayloadSchema
>;

/** Mirror 1:1 of `EncuentroEnlaceIn`. */
export const EncuentroEnlacePayloadSchema = z.object({
  siguiente_encuentro_id: identificadorSchema,
  slot_destino: z.enum(["PARTICIPANTE_1", "PARTICIPANTE_2"]),
  motivo: motivoSchema.nullable(),
  expected_version: versionEsperadaSchema,
});

export type EncuentroEnlacePayload = z.infer<
  typeof EncuentroEnlacePayloadSchema
>;

/** Mirror 1:1 of `EncuentroDesenlaceIn`. */
export const EncuentroDesenlacePayloadSchema = z.object({
  motivo: motivoSchema.nullable(),
  expected_version: versionEsperadaSchema,
});

export type EncuentroDesenlacePayload = z.infer<
  typeof EncuentroDesenlacePayloadSchema
>;

/**
 * Mirror 1:1 of the body of the manual bye.
 *
 * The endpoint of the bye reuses `EncuentroParticipantesIn`, but the DOMAIN
 * only reads the motive and the optimistic lock: the bye is ALWAYS manual
 * and it never assigns a participant by itself.
 */
export const EncuentroByePayloadSchema = z.object({
  motivo: motivoSchema.nullable(),
  expected_version: versionEsperadaSchema,
});

export type EncuentroByePayload = z.infer<typeof EncuentroByePayloadSchema>;

// ── Resultado, avance y corrección ───────────────────────────────────────────

/**
 * Mirror 1:1 of `ResultadoEncuentroIn`.
 *
 * The winner is AUTHORITATIVE and it MUST occupy one of the two slots. The
 * scores are optional and purely informative: they never determine nor
 * contradict the winner.
 */
export const ResultadoEncuentroPayloadSchema = z.object({
  ganador_id: identificadorSchema,
  puntaje_1: puntajeOpcionalSchema,
  puntaje_2: puntajeOpcionalSchema,
  marcador_detalle: z.string().trim().max(500).nullable(),
  motivo: motivoSchema.nullable(),
  expected_version: versionEsperadaSchema,
});

export type ResultadoEncuentroPayload = z.infer<
  typeof ResultadoEncuentroPayloadSchema
>;

/** Mirror 1:1 of `AvanceConfirmarIn`. */
export const AvanceConfirmarPayloadSchema = z.object({
  motivo: motivoSchema.nullable(),
  expected_version: versionEsperadaSchema,
});

export type AvanceConfirmarPayload = z.infer<
  typeof AvanceConfirmarPayloadSchema
>;

/** Mirror 1:1 of `CorreccionPreviewIn`. */
export const CorreccionPreviewPayloadSchema = z.object({
  ganador_id: identificadorSchema,
});

export type CorreccionPreviewPayload = z.infer<
  typeof CorreccionPreviewPayloadSchema
>;

/**
 * Mirror 1:1 of `CorreccionConfirmarIn`.
 *
 * `override` and `acepta_impacto` are only honoured when a descendant of the
 * link already started, finished or was cancelled: without them the
 * correction changes NOTHING (never a silent cascade).
 */
export const CorreccionConfirmarPayloadSchema = z.object({
  ganador_id: identificadorSchema,
  motivo: motivoSchema,
  override: z.boolean(),
  acepta_impacto: z.boolean(),
  expected_version: versionEsperadaSchema,
});

export type CorreccionConfirmarPayload = z.infer<
  typeof CorreccionConfirmarPayloadSchema
>;

// ── Respuestas de los comandos ────────────────────────────────────────────────

/** Mirror 1:1 of `AvancePreviewOut` — the proposal, it never writes. */
export const AvancePreviewSchema = z.object({
  encuentro_id: z.string(),
  siguiente_encuentro_id: z.string(),
  slot_destino: z.string(),
  ganador_id: z.string(),
  ocupante_actual_id: z.string().nullable(),
  ya_propagado: z.boolean(),
  bloqueado: z.boolean(),
  motivo_bloqueo: z.string().nullable(),
});

export type AvancePreview = z.infer<typeof AvancePreviewSchema>;

/** Mirror 1:1 of `AvanceOut` — the outcome of the propagation. */
export const AvanceSchema = z.object({
  encuentro_origen_id: z.string(),
  siguiente_encuentro_id: z.string(),
  slot_destino: z.string(),
  ganador_id: z.string(),
  ya_aplicado: z.boolean(),
  destino: EncuentroSchema,
});

export type Avance = z.infer<typeof AvanceSchema>;

/** Mirror 1:1 of `ImpactoDescendienteOut` — the impact over ONE descendant. */
export const ImpactoDescendienteSchema = z.object({
  encuentro_id: z.string(),
  slot: z.string(),
  estado: z.string(),
  ocupante_actual_id: z.string().nullable(),
  ganador_propagado_id: z.string().nullable(),
  bloqueado: z.boolean(),
  motivo_bloqueo: z.string().nullable(),
  se_reemplaza: z.boolean(),
  se_limpia_resultado: z.boolean(),
});

export type ImpactoDescendiente = z.infer<typeof ImpactoDescendienteSchema>;

/** Mirror 1:1 of `CorreccionPreviewOut` — the impact analysis. */
export const CorreccionPreviewSchema = z.object({
  encuentro_id: z.string(),
  ganador_actual_id: z.string().nullable(),
  ganador_nuevo_id: z.string(),
  requiere_override: z.boolean(),
  descendientes: z.array(ImpactoDescendienteSchema),
});

export type CorreccionPreview = z.infer<typeof CorreccionPreviewSchema>;

/** Mirror 1:1 of `CorreccionOut` — the outcome of the correction. */
export const CorreccionSchema = z.object({
  encuentro_id: z.string(),
  ganador_id: z.string(),
  requirio_override: z.boolean(),
  descendientes_afectados: z.number(),
  encuentro: EncuentroSchema,
  descendientes: z.array(ImpactoDescendienteSchema),
});

export type Correccion = z.infer<typeof CorreccionSchema>;

// ── Envelopes ────────────────────────────────────────────────────────────────

/** Envelope of every write of the module. */
export const CompetenciaEquipoEnvelopeSchema = competenciaEnvelopeSchema(
  CompetenciaEquipoSchema,
);

export type CompetenciaEquipoEnvelope = z.infer<
  typeof CompetenciaEquipoEnvelopeSchema
>;

export const RondaEnvelopeSchema = competenciaEnvelopeSchema(RondaSchema);

export type RondaEnvelope = z.infer<typeof RondaEnvelopeSchema>;

export const EncuentroEnvelopeSchema =
  competenciaEnvelopeSchema(EncuentroSchema);

export type EncuentroEnvelope = z.infer<typeof EncuentroEnvelopeSchema>;

export const AvancePreviewEnvelopeSchema =
  competenciaEnvelopeSchema(AvancePreviewSchema);

export type AvancePreviewEnvelope = z.infer<typeof AvancePreviewEnvelopeSchema>;

export const AvanceEnvelopeSchema = competenciaEnvelopeSchema(AvanceSchema);

export type AvanceEnvelope = z.infer<typeof AvanceEnvelopeSchema>;

export const CorreccionPreviewEnvelopeSchema = competenciaEnvelopeSchema(
  CorreccionPreviewSchema,
);

export type CorreccionPreviewEnvelope = z.infer<
  typeof CorreccionPreviewEnvelopeSchema
>;

export const CorreccionEnvelopeSchema =
  competenciaEnvelopeSchema(CorreccionSchema);

export type CorreccionEnvelope = z.infer<typeof CorreccionEnvelopeSchema>;

// ── Esquemas de formulario (derivados de los payloads) ───────────────────────

/**
 * The form schemas are DERIVED from their payload: the only field that never
 * reaches the form is `expected_version`, because it is the version the
 * SERVER returned and not a decision of the administrator.
 */
export const CompetenciaEquipoCreateFormSchema =
  CompetenciaEquipoCreatePayloadSchema;

export type CompetenciaEquipoCreateFormData = z.infer<
  typeof CompetenciaEquipoCreateFormSchema
>;

export const CompetenciaEquipoUpdateFormSchema =
  CompetenciaEquipoUpdatePayloadSchema.omit({ expected_version: true });

export type CompetenciaEquipoUpdateFormData = z.infer<
  typeof CompetenciaEquipoUpdateFormSchema
>;

export const RondaCreateFormSchema = RondaCreatePayloadSchema;

export type RondaCreateFormData = z.infer<typeof RondaCreateFormSchema>;

export const RondaUpdateFormSchema = RondaUpdatePayloadSchema.omit({
  expected_version: true,
}).extend({ motivo: motivoOpcionalSchema });

export type RondaUpdateFormData = z.infer<typeof RondaUpdateFormSchema>;

export const EncuentroCreateFormSchema = EncuentroCreatePayloadSchema;

export type EncuentroCreateFormData = z.infer<typeof EncuentroCreateFormSchema>;

export const EncuentroParticipantesFormSchema =
  EncuentroParticipantesPayloadSchema.omit({ expected_version: true });

export type EncuentroParticipantesFormData = z.infer<
  typeof EncuentroParticipantesFormSchema
>;

export const ResultadoEncuentroFormSchema =
  ResultadoEncuentroPayloadSchema.omit({ expected_version: true }).extend({
    motivo: motivoSchema,
  });

export type ResultadoEncuentroFormData = z.infer<
  typeof ResultadoEncuentroFormSchema
>;

export const AvanceConfirmarFormSchema = AvanceConfirmarPayloadSchema.omit({
  expected_version: true,
}).extend({ motivo: motivoSchema });

export type AvanceConfirmarFormData = z.infer<typeof AvanceConfirmarFormSchema>;

export const CorreccionConfirmarFormSchema =
  CorreccionConfirmarPayloadSchema.omit({
    expected_version: true,
    override: true,
  });

/** The form of the schedule: the day and the two times of the encounter. */
export const EncuentroProgramacionFormSchema = z.object({
  fecha: fechaSchema,
  hora_inicio: horaSchema,
  hora_fin: horaSchema,
  motivo: motivoSchema,
});

export type EncuentroProgramacionFormData = z.infer<
  typeof EncuentroProgramacionFormSchema
>;

/** The form of the manual bye: only the audited motive is asked. */
export const EncuentroByeFormSchema = z.object({
  motivo: motivoSchema,
});

export type EncuentroByeFormData = z.infer<typeof EncuentroByeFormSchema>;

/** The form of the link of an encounter to the next one. */
export const EncuentroEnlaceFormSchema = z.object({
  siguiente_encuentro_id: identificadorSchema,
  slot_destino: z.enum(["PARTICIPANTE_1", "PARTICIPANTE_2"]),
  motivo: motivoSchema,
});

export type EncuentroEnlaceFormData = z.infer<typeof EncuentroEnlaceFormSchema>;

/** The form of the removal of the link of an encounter. */
export const EncuentroDesenlaceFormSchema = z.object({
  motivo: motivoSchema,
});

export type EncuentroDesenlaceFormData = z.infer<
  typeof EncuentroDesenlaceFormSchema
>;

/**
 * The form of the correction: the new winner, the audited motive and the
 * EXPLICIT acceptance of the impact.
 *
 * It is derived from the payload of the confirmation: the optimistic lock and
 * the flag `override` never reach the form (the second one travels with the
 * acceptance).
 */
export const CorreccionFormSchema = CorreccionConfirmarPayloadSchema.omit({
  expected_version: true,
  override: true,
}).extend({ acepta_impacto: z.boolean() });

export type CorreccionFormData = z.infer<typeof CorreccionFormSchema>;
