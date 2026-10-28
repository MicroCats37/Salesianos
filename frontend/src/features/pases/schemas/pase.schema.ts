/**
 * TypeScript mirrors of the backend party-pass HTTP contracts.
 *
 * Source of truth (backend):
 *   - `modules/salesianos_fest/presentation/schemas/pase_schemas.py`
 *   - `modules/salesianos_fest/presentation/controllers/pase_controller.py`
 *
 * These schemas mirror the backend wrappers 1:1 — no `z.any()` and no
 * `Record<string, unknown>` for a whole payload
 * (see `contract/api-wrapper-presenter-contract.md` §7).
 */

import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";
import { PASE_CANTIDAD_MAXIMA_POR_COMPRA } from "../utils/pase.precio";

// ── Catalogue (GET /api/pases/) ──────────────────────────────────────────────

/** One row of the price calendar of a pass — backend `PasePrecioOut`. */
export const pasePrecioSchema = z.object({
  /** Commercial stage of the row (PREVENTA, REGULAR, ...). */
  etapa: z.string(),
  /** Unit price of the stage. */
  precio_unitario: z.number(),
  /** First day the price is in force — ISO date (YYYY-MM-DD). */
  vigente_desde: z.string(),
  /** Last day the price is in force — ISO date, `null` while it is open. */
  vigente_hasta: z.string().nullable(),
});

export type PasePrecio = z.infer<typeof pasePrecioSchema>;

/** One pass of the public catalogue — backend `PaseListOut`. */
export const paseCatalogoSchema = z.object({
  /** `Pase.id`. */
  id: z.string(),
  /** `Evento.id` the pass belongs to. */
  evento_id: z.string(),
  /** Commercial name of the pass. */
  nombre: z.string(),
  /** Public copy of the pass — `null` when it has none. */
  descripcion: z.string().nullable(),
  /** Whether the pass is published. */
  activo: z.boolean(),
  /** Price of the preventa stage while it is in force. */
  precio_preventa: z.number().nullable(),
  /** Price of the regular stage while it is in force. */
  precio_regular: z.number().nullable(),
  /** Effective unit price right now — `null` when no price is in force. */
  precio_vigente: z.number().nullable(),
  /** Maximum inventory of the pass — `0` means unlimited. */
  cantidad_maxima: z.number().int(),
  /** Full calendar of the ACTIVE price rows of the pass. */
  precios: z.array(pasePrecioSchema),
});

export type PaseCatalogo = z.infer<typeof paseCatalogoSchema>;

/** Envelope of the catalogue — backend `ApiResponse[list[PaseListOut]]`. */
export const paseCatalogoEnvelopeSchema = apiResponseSchema(
  z.array(paseCatalogoSchema),
);

export type PaseCatalogoEnvelope = z.infer<typeof paseCatalogoEnvelopeSchema>;

// ── Purchase (POST /api/pases/comprar) ───────────────────────────────────────

/**
 * Body of the purchase — backend `PaseComprarIn`.
 *
 * The client sends ONLY the pass and the quantity: the price and the total are
 * always computed by the server.
 */
export const paseComprarInSchema = z.object({
  /** UUID of the pass to buy. */
  pase_id: z
    .string()
    .min(1, "El pase es obligatorio")
    .max(64, "El identificador del pase es inválido"),
  /** Number of passes to buy. */
  cantidad: z.number().int().min(1, "La cantidad mínima es 1"),
});

export type PaseComprarIn = z.infer<typeof paseComprarInSchema>;

/**
 * Origin of the payment evidence of the order — backend `OrigenPago`.
 *
 * The value is DERIVED by the backend from the payment evidence: the client
 * never sends it and the provider never imposes it.
 */
export const paseOrigenPagoSchema = z.enum(["IZIPAY", "MANUAL", "SIN_PAGO"]);

export type PaseOrigenPago = z.infer<typeof paseOrigenPagoSchema>;

/** Identity of the purchase and of the purchased pass — `PaseCompraBaseOut`. */
export const paseCompraBaseSchema = z.object({
  /** `commerce.Compra.id`. */
  compra_id: z.string(),
  /** `OrdenPago.id` that funds the purchase. */
  orden_pago_id: z.string(),
  /** Human readable number of the payment order. */
  numero_orden: z.string(),
  /** `Pase.id` of the purchased pass. */
  pase_id: z.string(),
  /** Commercial name of the purchased pass. */
  pase_nombre: z.string(),
});

/** The amounts FROZEN at purchase time — backend `PaseCompraMontosOut`. */
export const paseCompraMontosSchema = z.object({
  /** Number of passes of the batch. */
  cantidad: z.number().int(),
  /** Unit price frozen at purchase time. */
  precio_unitario: z.number(),
  /** Total frozen at purchase time. */
  total: z.number(),
});

/** Identity + frozen amounts + commercial state. */
export const paseCompraEstadoBaseSchema = paseCompraBaseSchema
  .merge(paseCompraMontosSchema)
  .extend({
    /** `Compra.estado`: PENDIENTE | PAGADA | CANCELADA. */
    estado_compra: z.string(),
    /** `OrdenPago.estado`: PENDIENTE | PAGADA | CANCELADA | VENCIDA. */
    estado_orden: z.string(),
  });

/** Output of creating a pass purchase — backend `PaseCompraCreadaOut`. */
export const paseCompraCreadaSchema = paseCompraEstadoBaseSchema;

export type PaseCompraCreada = z.infer<typeof paseCompraCreadaSchema>;

/**
 * Output of reading a pass purchase — backend `PaseCompraEstadoOut`.
 *
 * `origen_pago` is derived by the backend and `beneficiarios_asignados` /
 * `beneficiarios_pendientes` describe the nominative rights of the batch: a
 * revoked slot is consumed forever and is never restored.
 */
export const paseCompraEstadoSchema = paseCompraEstadoBaseSchema.extend({
  /** Currency of the frozen amounts. */
  moneda: z.string(),
  /** Origin of the payment evidence of the order. */
  origen_pago: paseOrigenPagoSchema,
  /** Creation instant of the purchase. */
  created_at: z.string(),
  /** Active rights already assigned. */
  beneficiarios_asignados: z.number().int(),
  /** Free slots of the batch. */
  beneficiarios_pendientes: z.number().int(),
});

export type PaseCompraEstado = z.infer<typeof paseCompraEstadoSchema>;

/** Envelope of the creation of a purchase. */
export const paseCompraCreadaEnvelopeSchema = apiResponseSchema(
  paseCompraCreadaSchema,
);

export type PaseCompraCreadaEnvelope = z.infer<
  typeof paseCompraCreadaEnvelopeSchema
>;

/** Envelope of the state of a purchase. */
export const paseCompraEstadoEnvelopeSchema = apiResponseSchema(
  paseCompraEstadoSchema,
);

export type PaseCompraEstadoEnvelope = z.infer<
  typeof paseCompraEstadoEnvelopeSchema
>;

// ── Browser form ─────────────────────────────────────────────────────────────

/**
 * Schema of the purchase form of the browser.
 *
 * The form carries EXACTLY the two fields of the body: the pass and the
 * quantity. The price and the total are never typed by the buyer.
 */
export const paseCompraFormSchema = z.object({
  /** UUID of the selected pass. */
  pase_id: z.string().min(1, "Selecciona un pase de fiesta"),
  /** Number of passes of the batch. */
  cantidad: z
    .number()
    .int()
    .min(1, "La cantidad mínima es 1")
    .max(
      PASE_CANTIDAD_MAXIMA_POR_COMPRA,
      `La cantidad máxima por compra es ${PASE_CANTIDAD_MAXIMA_POR_COMPRA}`,
    ),
});

export type PaseCompraFormData = z.infer<typeof paseCompraFormSchema>;
