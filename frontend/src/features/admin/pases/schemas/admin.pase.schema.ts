import { z } from "zod";
import { AdminErrorSchema } from "@/features/admin/schemas";

/**
 * Zod mirrors of the administrative cancellation of a pass purchase.
 *
 * Source of truth:
 * `backend/modules/administracion/presentation/schemas/admin_pases_schemas.py`.
 *
 * The motive is MANDATORY: a cancellation revokes nominative rights already
 * delivered, so the decision is always audited. The wrapper never carries the
 * QR credential nor any provider internal.
 */

/**
 * The FORM of the cancellation — the audited motive.
 *
 * It collects what the administrator typed; the API payload is built by the
 * mutation hook (`contract/next-app-architecture-contract.md` §5).
 */
export const AdminPaseCancelarFormSchema = z.object({
  motivo: z
    .string()
    .trim()
    .min(1, "El motivo de la cancelación es obligatorio.")
    .max(1000, "El motivo es demasiado largo."),
});

export type AdminPaseCancelarFormData = z.infer<
  typeof AdminPaseCancelarFormSchema
>;

/** The API body of the cancellation — the 1:1 mirror of the backend. */
export const AdminPaseCancelarPayloadSchema = z.object({
  motivo: z.string().min(1).max(1000),
});

export type AdminPaseCancelarPayload = z.infer<
  typeof AdminPaseCancelarPayloadSchema
>;

/**
 * The outcome of the administrative cancellation — backend
 * `AdminPaseCanceladaOut`.
 *
 * It is NOT a monetary refund: no money is returned by this operation.
 */
export const AdminPaseCanceladaSchema = z.object({
  compra_id: z.string(),
  estado_compra: z.string(),
  estado_orden: z.string(),
  /** True when the purchase was already cancelled (idempotent hit). */
  ya_cancelada: z.boolean(),
  /** Nominative rights revoked by the cancellation. */
  beneficiarios_revocados: z.number(),
  /** People affected by the revocation. */
  personas_afectadas: z.number(),
  motivo: z.string(),
});

export type AdminPaseCancelada = z.infer<typeof AdminPaseCanceladaSchema>;

export const AdminPaseCanceladaEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminPaseCanceladaSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminPaseCanceladaEnvelope = z.infer<
  typeof AdminPaseCanceladaEnvelopeSchema
>;
