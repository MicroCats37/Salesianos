import { z } from "zod";
import { pedidoLineaSchema } from "@/features/marketplace/schemas/pedido.schema";
import { beneficiarioPaseSchema } from "@/features/pases/schemas/pase.schema";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The Zod mirrors of the VALIDATION area (`ADM-16`, `ADM-20`, `ADM-22`).
 *
 * The area has TWO operations that must never be confused:
 *
 * - the ENTRY of the party (`ADM-16`): a right of entry is checked at the
 *   door;
 * - the DELIVERY of the store (`ADM-20`): a paid order is checked at the
 *   counter of the pickup.
 *
 * ## WHAT IS MIRRORED HERE, AND WHY
 *
 * | Shape | Owner of the shape | Mirrored here? |
 * |---|---|---|
 * | `EntregaPendienteOut` (`DOM-06`) | the delivery queue of the store | **YES** — the delivery dataset belongs to this area |
 * | `EntregaConfirmadaOut` (`DOM-06`) | the delivery queue of the store | **YES** |
 * | `PedidoLineaOut` (`DOM-05`) | `features/marketplace` (the order dataset) | **NO** — REUSED from its canonical owner |
 * | `PaseBeneficiarioOut` (`DOM-03`) | `features/pases` (the purchase lot dataset) | **NO** — REUSED from its canonical owner |
 * | `TicketPreviewOut` (`RT-RT-01`) | **does not exist** | **NO** — there is no presenter to mirror |
 * | `TicketConfirmadoOut` (`RT-RT-02`) | **does not exist** | **NO** — there is no presenter to mirror |
 * | `AdminValidacionListItemOut` (`RT-VA-01`) | **does not exist** | **NO** — the route is not even in the ledger |
 *
 * **A mirror is never duplicated.** The order line and the entry right are
 * already mirrored by the features that OWN those datasets; this module
 * REUSES them instead of writing a second copy of the same wire shape
 * (`salesianos-api-data`: one dataset, one owner).
 *
 * ## WHAT IS MISSING, AND IT IS NOT INVENTED
 *
 * The module `validaciones` **does not exist** in the target. The three
 * wrappers of the area are therefore PROVISIONAL and have no presenter:
 *
 * - `TicketPreviewOut` — the preview of an entry (`RT-RT-01`);
 * - `TicketConfirmadoOut` — the confirmed entry (`RT-RT-02`), whose input
 *   the ledger declares as `ConfirmarTicketIn(idempotency_key)` and whose
 *   remaining fields are NOT ratified;
 * - `AdminValidacionListItemOut` — the row of the audit (`RT-VA-01`), a
 *   route that is not even in the frozen ledger.
 *
 * Until A0 ratifies them (`A0-API05-02`), the view models of the area keep
 * their PROVISIONAL shape and the routes keep their honest "not connected"
 * state. Writing a mirror of a wrapper that does not exist would be
 * inventing a contract.
 *
 * ## THIS MIRROR IS NOT BOUND
 *
 * `InventarioController` (the five routes of the inventory and of the
 * deliveries) is **NOT registered** in `Aplicacion/backend/config/api.py`, so
 * `RT-MK-10` and `RT-MK-11` DO NOT EXIST at runtime (`A0-RTV-02`). A client
 * that called them would be calling a route that the API does not serve, so
 * **this package binds none of them** (`FR-07` §3.1 regla 2).
 */

/** An identifier of the domain: `DOM-06` declares its identifiers as `UUID`. */
const id = z.string().uuid();

/** A machine code published by the presenter. */
const codigo = z.string().min(1);

/** An instant published by the presenter (`datetime`). */
const marcaTiempo = z.string().min(1);

// ── Salidas ───────────────────────────────────────────────────────────────────

/**
 * A paid order that still waits for its pickup (`EntregaPendienteOut`).
 *
 * The lines are the FROZEN lines of the order: the mirror reuses
 * `pedidoLineaSchema` from `features/marketplace`, the owner of the order
 * dataset, instead of repeating it.
 */
export const entregaPendienteSchema = z.object({
  pedido_id: id,
  comprador_nombres: z.string().min(1),
  comprador_apellidos: z.string().min(1),
  comprador_documento: z.string().min(1),
  /** The state of the order. */
  estado: codigo,
  /** The state of the delivery. */
  estado_entrega: codigo,
  /** The frozen total of the order. */
  total: z.number(),
  /** The currency of the order. */
  moneda: z.string(),
  /** The frozen lines of the order. */
  lineas: z.array(pedidoLineaSchema),
  /** The moment the order was created. */
  created_at: marcaTiempo,
});

/** A delivery act already registered for a marketplace order. */
export const entregaEntregadaSchema = z.object({
  pedido_id: id,
  comprador_nombres: z.string().min(1),
  comprador_apellidos: z.string().min(1),
  comprador_documento: z.string().min(1),
  total: z.number(),
  moneda: z.string(),
  lineas: z.array(pedidoLineaSchema),
  entregada_en: marcaTiempo,
});

/**
 * The recorded delivery (`EntregaConfirmadaOut`).
 *
 * It is the ACT of the delivery: the operator, the instant and the units
 * delivered. The payment and the order are NOT touched by it (`RN-M07`).
 */
export const entregaConfirmadaSchema = z.object({
  pedido_id: id,
  /** The state of the delivery after the confirmation. */
  estado_entrega: codigo,
  /** The units delivered. */
  cantidad_total: z.number().int(),
  /** The operator who made the delivery. */
  actor_id: id,
  /** The moment of the delivery. */
  entregada_en: marcaTiempo,
  /** The frozen lines of the order. */
  lineas: z.array(pedidoLineaSchema),
});

// ── Envelopes ────────────────────────────────────────────────────────────────

/** The pending and completed pickups (`GET /administracion/marketplace/entregas`). */
export const entregasPendientesEnvelope = apiResponseSchema(
  z.object({
    pendientes: z.array(entregaPendienteSchema),
    entregadas: z.array(entregaEntregadaSchema),
  }),
);

/** The recorded delivery (`POST …/entregas/{pedido_id}/confirmar`). */
export const entregaConfirmadaEnvelope = apiResponseSchema(
  entregaConfirmadaSchema,
);

// ── Inferred types ───────────────────────────────────────────────────────────

export type EntregaPendiente = z.infer<typeof entregaPendienteSchema>;
export type EntregaConfirmada = z.infer<typeof entregaConfirmadaSchema>;

/**
 * The entry right of a person (`PaseBeneficiarioOut`).
 *
 * It is REUSED from `features/pases`, the canonical owner of that wire
 * shape: the validation console does not own the purchase lot and does not
 * publish a second mirror of it.
 */
export { beneficiarioPaseSchema as paseBeneficiarioSchema };
export type PaseBeneficiario = z.infer<typeof beneficiarioPaseSchema>;

// ── La consola de validación (`RT-RT-01` / `RT-RT-02`) ──────────────────────
//
// El módulo `validaciones` YA EXISTE en el objetivo (paquete `XCT-01`), así que
// `TicketPreviewOut` y `TicketConfirmadoOut` tienen presenter y estos espejos
// son el espejo EXACTO de sus wrappers.
//
// `Aplicacion/backend/modules/validaciones/presentation/schemas/validacion_schemas.py`
// → `TicketPreviewOut` · `TicketConfirmadoOut`.
//
// La forma está CONGELADA en `FR-05` §3.1 y §3.2. La CREDENCIAL nunca vuelve.

/** La persona que sostiene el derecho (`TicketTitularOut`). */
export const ticketTitularSchema = z.object({
  persona_id: id,
  nombre: codigo,
});

/** La cuenta que operó el canje (`TicketActorOut`). */
export const ticketActorSchema = z.object({
  usuario_id: id.nullable(),
  persona_id: id.nullable(),
});

/** La vista previa de una credencial (`TicketPreviewOut`). */
export const ticketPreviewSchema = z.object({
  edicion_id: id,
  tipo_derecho: codigo,
  codigo,
  estado: codigo,
  cantidad_total: z.number().int(),
  cantidad_disponible: z.number().int(),
  cantidad_consumida: z.number().int(),
  puede_canjear: z.boolean(),
  motivo_codigo: z.string().nullable(),
  motivo_mensaje: z.string().nullable(),
  titular: ticketTitularSchema,
});

/** El canje confirmado de una credencial (`TicketConfirmadoOut`). */
export const ticketConfirmadoSchema = z.object({
  validacion_id: id,
  tipo_derecho: codigo,
  cantidad_consumida: z.number().int(),
  cantidad_restante: z.number().int(),
  estado: codigo,
  consumido_en: marcaTiempo,
  actor: ticketActorSchema,
  repetido: z.boolean(),
});

/** La respuesta de la comprobación (`POST /validaciones/preview`). */
export const ticketPreviewEnvelope = apiResponseSchema(ticketPreviewSchema);

/** La respuesta del canje (`POST /validaciones/confirmar`). */
export const ticketConfirmadoEnvelope = apiResponseSchema(
  ticketConfirmadoSchema,
);

/** El cuerpo de la comprobación (`RT-RT-01`). */
export const previewTicketSchema = z.object({
  codigo: z.string().min(1).max(64),
});

/** El cuerpo del canje (`RT-RT-02`). */
export const confirmarTicketSchema = z.object({
  codigo: z.string().min(1).max(64),
  idempotency_key: z.string().min(1).max(128),
  cantidad: z.number().int().min(1).optional(),
});

export type TicketTitular = z.infer<typeof ticketTitularSchema>;
export type TicketActor = z.infer<typeof ticketActorSchema>;
export type TicketPreview = z.infer<typeof ticketPreviewSchema>;
export type TicketConfirmado = z.infer<typeof ticketConfirmadoSchema>;
export type PreviewTicketDatos = z.infer<typeof previewTicketSchema>;
export type ConfirmarTicketDatos = z.infer<typeof confirmarTicketSchema>;

/**
 * The version of the contract of this feature.
 *
 * It is the SAME version the backend declares in
 * `modules/validaciones/presentation/schemas/__init__.py` → `SCHEMA_VERSION`
 * and that `core/contract_versions.py` freezes for `validaciones` (`FR-07`).
 */
export const SCHEMA_VERSION = "1.0.0";
