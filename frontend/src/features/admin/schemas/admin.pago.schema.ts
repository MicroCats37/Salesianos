import { z } from "zod";
import { AdminErrorSchema } from "./admin.comun.schema";
import { adminPaginadoSchema } from "./admin.paginacion.schema";

/**
 * Zod mirrors of the payments (A5, A6) and of the manual approval of a
 * payment.
 *
 * Source of truth: `backend/modules/administracion/presentation/schemas/admin_pago_schemas.py`.
 *
 * The wrapper is EXPLICIT field by field: the restricted blobs of the payment
 * module (`metadata`, `token_sesion`, `response_message`, `transaction_id`)
 * have NO place in it — they are not even declared, so they can never be
 * modelled, let alone serialized.
 */

/** The closed set of channels through which a manual payment can arrive. */
export const ADMIN_CANAL_PAGO_MANUAL = [
  "TRANSFERENCIA_BANCARIA",
  "EFECTIVO",
  "YAPE",
  "PLIN",
  "OTRO",
] as const;

export type AdminCanalPagoManual = (typeof ADMIN_CANAL_PAGO_MANUAL)[number];

/**
 * The closed set of purchase types of the payments table.
 *
 * ONE row is ONE purchase with exactly ONE supported composition: a sports
 * registration (`INICIAL` / `AMPLIACION`) OR a batch of party passes (`PASE`).
 * The two identities are never both present.
 */
export const ADMIN_TIPO_COMPRA = ["INICIAL", "AMPLIACION", "PASE"] as const;

export type AdminTipoCompra = (typeof ADMIN_TIPO_COMPRA)[number];

export const AdminTransaccionListItemSchema = z.object({
  id: z.string(),
  status: z.string(),
  amount: z.number(),
  currency: z.string(),
  metodo_pago: z.string().nullable(),
  response_code: z.string().nullable(),
  created_at: z.string(),
});

export type AdminTransaccionListItem = z.infer<
  typeof AdminTransaccionListItemSchema
>;

export const AdminPagoListItemSchema = z.object({
  compra_id: z.string(),
  orden_pago_id: z.string().nullable(),
  numero_orden: z.string().nullable(),
  /** The sports registration of the purchase — `null` for a batch of passes. */
  inscripcion_id: z.string().nullable(),
  /** The pass of the purchase — `null` for a sports purchase. */
  pase_id: z.string().nullable(),
  responsable_nombre: z.string(),
  /** Closed discriminator: INICIAL | AMPLIACION | PASE. */
  tipo: z.enum(ADMIN_TIPO_COMPRA),
  /** Commercial name of the purchased product (package or pass). */
  producto_nombre: z.string(),
  cantidad: z.number(),
  precio_unitario: z.number(),
  total: z.number(),
  estado_compra: z.string(),
  estado_orden: z.string().nullable(),
  pagada_en: z.string().nullable(),
  origen_pago: z.string(),
  monto_orden: z.number().nullable(),
  moneda_orden: z.string().nullable(),
  /** Active nominative rights of the batch — `0` for a sports purchase. */
  beneficiarios_activos: z.number(),
  /** Revoked nominative rights of the batch — `0` for a sports purchase. */
  beneficiarios_revocados: z.number(),
  created_at: z.string(),
});

export type AdminPagoListItem = z.infer<typeof AdminPagoListItemSchema>;

/** One entry of the manual approval history of an order (audit trail). */
export const AdminAprobacionManualSchema = z.object({
  id: z.string(),
  estado: z.string(),
  canal: z.string(),
  referencia: z.string(),
  monto: z.number(),
  moneda: z.string(),
  motivo: z.string(),
  actor: z.string(),
  anulada_por: z.string().nullable(),
  anulada_en: z.string().nullable(),
  motivo_anulacion: z.string().nullable(),
  created_at: z.string(),
});

export type AdminAprobacionManual = z.infer<typeof AdminAprobacionManualSchema>;

/**
 * One nominative right of a pass purchase — backend `AdminPaseBeneficiarioOut`.
 *
 * Only the SLOT, the state and the internal identifier of the holder travel:
 * no names, no documents and never the QR credential.
 */
export const AdminPaseBeneficiarioSchema = z.object({
  persona_id: z.string(),
  slot: z.number().int(),
  estado: z.string(),
});

export type AdminPaseBeneficiario = z.infer<typeof AdminPaseBeneficiarioSchema>;

/** The drilldown of a payment order (A6): the list wrapper plus its attempts. */
export const AdminPagoDetailSchema = AdminPagoListItemSchema.extend({
  transacciones: z.array(AdminTransaccionListItemSchema),
  aprobaciones: z.array(AdminAprobacionManualSchema),
  /** The nominative rights of a batch — empty for a sports purchase. */
  beneficiarios: z.array(AdminPaseBeneficiarioSchema),
});

export type AdminPagoDetail = z.infer<typeof AdminPagoDetailSchema>;

/** Canonical paginated container of the payments table (A5). */
export const AdminPagoListadoSchema = adminPaginadoSchema(
  AdminPagoListItemSchema,
);

export type AdminPagoListado = z.infer<typeof AdminPagoListadoSchema>;

export const AdminPagoListadoEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminPagoListadoSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminPagoListadoEnvelope = z.infer<
  typeof AdminPagoListadoEnvelopeSchema
>;

export const AdminPagoDetalleEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminPagoDetailSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminPagoDetalleEnvelope = z.infer<
  typeof AdminPagoDetalleEnvelopeSchema
>;

// ── Aprobación manual ───────────────────────────────────────────────────────

/**
 * The FORM of the manual approval.
 *
 * It collects what the administrator typed; the API payload is built by the
 * mutation hook (`contract/next-app-architecture-contract.md` §5).
 */
export const AdminPagoAprobarManualFormSchema = z.object({
  canal: z.enum(ADMIN_CANAL_PAGO_MANUAL, {
    message: "Selecciona el canal del pago.",
  }),
  referencia: z
    .string()
    .trim()
    .min(1, "La referencia del pago es obligatoria.")
    .max(100, "La referencia es demasiado larga."),
  monto: z
    .string()
    .trim()
    .min(1, "El monto es obligatorio.")
    .refine(
      (valor) => Number.isFinite(Number(valor)) && Number(valor) > 0,
      "El monto debe ser un número mayor que cero.",
    ),
  moneda: z
    .string()
    .trim()
    .length(3, "La moneda debe tener tres letras (por ejemplo PEN)."),
  motivo: z
    .string()
    .trim()
    .min(1, "El motivo de la aprobación es obligatorio.")
    .max(1000, "El motivo es demasiado largo."),
});

export type AdminPagoAprobarManualFormData = z.infer<
  typeof AdminPagoAprobarManualFormSchema
>;

/** The API body of the manual approval — the 1:1 mirror of the backend. */
export const AdminPagoAprobarManualPayloadSchema = z.object({
  canal: z.enum(ADMIN_CANAL_PAGO_MANUAL),
  referencia: z.string().min(1).max(100),
  monto: z.number().positive(),
  moneda: z.string().length(3),
  motivo: z.string().min(1).max(1000),
});

export type AdminPagoAprobarManualPayload = z.infer<
  typeof AdminPagoAprobarManualPayloadSchema
>;

/** The FORM of the annulment of a manual approval. */
export const AdminPagoAnularManualFormSchema = z.object({
  motivo: z
    .string()
    .trim()
    .min(1, "El motivo de la anulación es obligatorio.")
    .max(1000, "El motivo es demasiado largo."),
});

export type AdminPagoAnularManualFormData = z.infer<
  typeof AdminPagoAnularManualFormSchema
>;

/** The API body of the annulment — the 1:1 mirror of the backend. */
export const AdminPagoAnularManualPayloadSchema = z.object({
  motivo: z.string().min(1).max(1000),
});

export type AdminPagoAnularManualPayload = z.infer<
  typeof AdminPagoAnularManualPayloadSchema
>;

/** The outcome of the manual approval. */
export const AdminPagoAprobarManualSchema = z.object({
  resultado: z.string(),
  settlement_status: z.string(),
  orden_pago_id: z.string(),
  numero_orden: z.string(),
  estado_orden: z.string(),
  aprobacion_id: z.string(),
  estado_aprobacion: z.string(),
  canal: z.string(),
  referencia: z.string(),
  monto: z.number(),
  moneda: z.string(),
  motivo: z.string(),
  actor: z.string(),
  approved_at: z.string(),
});

export type AdminPagoAprobarManual = z.infer<
  typeof AdminPagoAprobarManualSchema
>;

/** The outcome of the annulment of a manual approval. */
export const AdminPagoAnularManualSchema = z.object({
  resultado: z.string(),
  orden_pago_id: z.string(),
  compra_id: z.string(),
  estado_compra: z.string(),
  estado_orden: z.string(),
  estado_aprobacion: z.string(),
  /** Sports assignments revoked by the annulment. */
  asignaciones_revocadas: z.number(),
  /** Nominative rights of a batch revoked by the annulment. */
  beneficiarios_revocados: z.number(),
  personas_afectadas: z.number(),
  anulada_por: z.string(),
  anulada_en: z.string(),
  motivo_anulacion: z.string(),
});

export type AdminPagoAnularManual = z.infer<typeof AdminPagoAnularManualSchema>;

export const AdminPagoAprobarManualEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminPagoAprobarManualSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminPagoAprobarManualEnvelope = z.infer<
  typeof AdminPagoAprobarManualEnvelopeSchema
>;

export const AdminPagoAnularManualEnvelopeSchema = z.object({
  success: z.boolean(),
  data: AdminPagoAnularManualSchema.nullable(),
  error: AdminErrorSchema.nullable(),
  message: z.string().nullable(),
});

export type AdminPagoAnularManualEnvelope = z.infer<
  typeof AdminPagoAnularManualEnvelopeSchema
>;
