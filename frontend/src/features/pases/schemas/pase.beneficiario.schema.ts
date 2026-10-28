/**
 * TypeScript mirrors of the backend nominative-rights HTTP contracts.
 *
 * Source of truth (backend):
 *   - `modules/salesianos_fest/presentation/schemas/pase_schemas.py`
 *     (blocks `PaseBeneficiarioBaseOut`, `PaseBeneficiarioAuditadoOut`,
 *     `PaseConteosBeneficiariosOut`, `PaseBeneficiariosListaOut`,
 *     `PaseBeneficiariosAsignadosOut`, `PaseBeneficiarioRevocadoOut`,
 *     `PaseBeneficiariosAsignarIn`, `PaseBeneficiarioRevocarIn`)
 *   - `modules/salesianos_fest/presentation/controllers/pase_controller.py`
 *
 * The schemas are COMPOSED over the same blocks as the backend
 * (`contract/SCHEMA_DRY_INTENTION.md`): the immutable slot accounting is
 * declared once and reused by the list, the assignment and the revocation.
 */

import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";
import { personaResueltaSchema } from "./persona.schema";

// ── Contabilidad INMUTABLE de los slots ───────────────────────────────────────

/**
 * The IMMUTABLE slot accounting of a batch — backend
 * `PaseConteosBeneficiariosOut`.
 *
 * `slots_usados` counts the rows of the batch — ACTIVE **and** REVOKED: a
 * revoked slot is consumed forever and `slots_disponibles` never grows back
 * after a revocation.
 */
export const paseConteosBeneficiariosSchema = z.object({
  /** Number of passes of the batch. */
  cantidad_pases: z.number().int(),
  /** Active rights. */
  activos: z.number().int(),
  /** Revoked rights — their slot is consumed forever. */
  revocados: z.number().int(),
  /** Slots consumed (active + revoked). */
  slots_usados: z.number().int(),
  /** Slots still free. */
  slots_disponibles: z.number().int(),
});

export type PaseConteosBeneficiarios = z.infer<
  typeof paseConteosBeneficiariosSchema
>;

// ── Beneficiario ─────────────────────────────────────────────────────────────

/** One nominative right — backend `PaseBeneficiarioBaseOut`. */
export const paseBeneficiarioBaseSchema = z.object({
  /** `Persona.id` of the holder. */
  persona_id: z.string(),
  /** Display name of the holder. */
  nombre_completo: z.string(),
  /** Document type of the holder. */
  tipo_documento: z.string(),
  /** Document number of the holder. */
  numero_documento: z.string(),
  /** Immutable slot of the batch (1..cantidad_pases). */
  slot: z.number().int(),
  /** ACTIVA | REVOCADA. */
  estado: z.string(),
});

/** One nominative right with its audit — backend `PaseBeneficiarioAuditadoOut`. */
export const paseBeneficiarioAuditadoSchema = paseBeneficiarioBaseSchema.extend(
  {
    /** Instant of the assignment. */
    asignado_en: z.string(),
    /** Instant of the revocation — `null` while the right is active. */
    revocado_en: z.string().nullable(),
    /** Audited motive of the revocation. */
    motivo_revocacion: z.string().nullable(),
  },
);

export type PaseBeneficiarioAuditado = z.infer<
  typeof paseBeneficiarioAuditadoSchema
>;

// ── Listado ──────────────────────────────────────────────────────────────────

/** The list of the rights of a batch — backend `PaseBeneficiariosListaOut`. */
export const paseBeneficiariosListaSchema =
  paseConteosBeneficiariosSchema.extend({
    compra_id: z.string(),
    beneficiarios: z.array(paseBeneficiarioAuditadoSchema),
  });

export type PaseBeneficiariosLista = z.infer<
  typeof paseBeneficiariosListaSchema
>;

// ── Asignación ───────────────────────────────────────────────────────────────

/** The outcome of the assignment — backend `PaseBeneficiariosAsignadosOut`. */
export const paseBeneficiariosAsignadosSchema =
  paseConteosBeneficiariosSchema.extend({
    compra_id: z.string(),
    /** Rights created by this call. */
    asignados: z.number().int(),
    /** Rights that already existed (idempotent no-op). */
    ya_asignados: z.number().int(),
    beneficiarios: z.array(paseBeneficiarioAuditadoSchema),
  });

export type PaseBeneficiariosAsignados = z.infer<
  typeof paseBeneficiariosAsignadosSchema
>;

// ── Revocación ───────────────────────────────────────────────────────────────

/** The outcome of the revocation — backend `PaseBeneficiarioRevocadoOut`. */
export const paseBeneficiarioRevocadoSchema =
  paseConteosBeneficiariosSchema.extend({
    compra_id: z.string(),
    persona_id: z.string(),
    /** ACTIVA | REVOCADA. */
    estado: z.string(),
    revocado_en: z.string().nullable(),
    /** True when the right was already revoked (idempotent hit). */
    ya_revocado: z.boolean(),
  });

export type PaseBeneficiarioRevocado = z.infer<
  typeof paseBeneficiarioRevocadoSchema
>;

// ── Cuerpos de la API ────────────────────────────────────────────────────────

/**
 * Body of the assignment — backend `PaseBeneficiariosAsignarIn`.
 *
 * Each id is the UUID of an EXISTING `Persona`: the API never creates a person
 * out of free text.
 */
export const paseBeneficiariosAsignarInSchema = z.object({
  beneficiario_ids: z
    .array(z.string().min(1, "El identificador de la persona es obligatorio."))
    .min(1, "Selecciona al menos una persona.")
    .max(50, "No se pueden asignar más de 50 personas por lote."),
});

export type PaseBeneficiariosAsignarIn = z.infer<
  typeof paseBeneficiariosAsignarInSchema
>;

/** Body of the revocation — backend `PaseBeneficiarioRevocarIn`. */
export const paseBeneficiarioRevocarInSchema = z.object({
  motivo: z
    .string()
    .trim()
    .min(1, "El motivo de la revocación es obligatorio.")
    .max(1000, "El motivo es demasiado largo."),
});

export type PaseBeneficiarioRevocarIn = z.infer<
  typeof paseBeneficiarioRevocarInSchema
>;

// ── Formularios del navegador ────────────────────────────────────────────────

/**
 * The FORM of the assignment.
 *
 * The browser collects the persons that ALREADY EXIST (resolved by the exact
 * lookup); the API payload is built by the mutation hook, which sends ONLY
 * their ids (`contract/next-app-architecture-contract.md` §5).
 */
export const paseAsignarBeneficiariosFormSchema = z.object({
  personas: z
    .array(personaResueltaSchema)
    .min(1, "Selecciona al menos una persona."),
});

export type PaseAsignarBeneficiariosFormData = z.infer<
  typeof paseAsignarBeneficiariosFormSchema
>;

/** The FORM of the revocation — the motive is mandatory and audited. */
export const paseRevocarBeneficiarioFormSchema = z.object({
  motivo: z
    .string()
    .trim()
    .min(1, "El motivo de la revocación es obligatorio.")
    .max(1000, "El motivo es demasiado largo."),
});

export type PaseRevocarBeneficiarioFormData = z.infer<
  typeof paseRevocarBeneficiarioFormSchema
>;

// ── Envelopes ────────────────────────────────────────────────────────────────

export const paseBeneficiariosListaEnvelopeSchema = apiResponseSchema(
  paseBeneficiariosListaSchema,
);

export type PaseBeneficiariosListaEnvelope = z.infer<
  typeof paseBeneficiariosListaEnvelopeSchema
>;

export const paseBeneficiariosAsignadosEnvelopeSchema = apiResponseSchema(
  paseBeneficiariosAsignadosSchema,
);

export type PaseBeneficiariosAsignadosEnvelope = z.infer<
  typeof paseBeneficiariosAsignadosEnvelopeSchema
>;

export const paseBeneficiarioRevocadoEnvelopeSchema = apiResponseSchema(
  paseBeneficiarioRevocadoSchema,
);

export type PaseBeneficiarioRevocadoEnvelope = z.infer<
  typeof paseBeneficiarioRevocadoEnvelopeSchema
>;
