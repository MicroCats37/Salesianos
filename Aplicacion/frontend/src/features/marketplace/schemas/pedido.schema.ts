import { z } from "zod";
import { apiResponseSchema } from "@/types/api.types";

/**
 * The Zod mirrors of the ORDER of the store (`DOM-05`).
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * **NOT REGISTERED · NOT BOUND · NOT CALLED**
 *
 * `PedidoController` is NOT registered in
 * `Aplicacion/backend/config/api.py` (`A0-RTV-02`), so `POST
 * /marketplace/pedidos` and `GET /marketplace/pedidos/{token}` DO NOT EXIST
 * at runtime. A route that is not registered is dead code by design
 * (`FR-07` §3.1 regla 2).
 *
 * These mirrors exist so the SHAPE is ready and the seam is honest: the day
 * A0 registers the controller, the binding is ONE file and no rewrite of the
 * views. Until then NOTHING in this feature calls these routes and the
 * interface never shows an order it did not read.
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * The shapes are a 1:1 mirror of
 * `Aplicacion/backend/modules/marketplace/presentation/schemas/pedido_schemas.py`:
 * `PedidoItemIn`, `CrearPedidoIn`, `PedidoLineaOut`, `PedidoSeguimientoOut`
 * and `PedidoCreadoOut`.
 */

/** An identifier of the domain: a UUID published by the presenter. */
const id = z.string().uuid();

/** A machine code published by the presenter. */
const codigo = z.string().min(1);

/** An instant published by the presenter. */
const marcaTiempo = z.string().min(1);

/**
 * An article declared by the buyer (`PedidoItemIn`).
 *
 * `tipo` is the discriminant of the ORIGIN of the article: only `PRODUCTO`
 * is admissible. `PASE` and `INSCRIPCION` may be DECLARED so the rejection
 * is explicit (`PEDIDO_ITEMS_MIXTOS` / `PEDIDO_ITEM_NO_PERMITIDO`) and not a
 * generic 422 (`RN-C01`).
 */
export const pedidoItemSchema = z.object({
  tipo: z.string().max(16),
  producto_id: id,
  cantidad: z.number().int(),
});

/**
 * The payload of the order (`CrearPedidoIn`).
 *
 * It admits NO amount: the price is resolved and frozen by the server
 * (`RN-C02`). The edition is not declared either: the server resolves it
 * (`RN-E01`).
 */
export const crearPedidoSchema = z.object({
  items: z.array(pedidoItemSchema).min(1),
  tipo_documento: z.enum(["DNI", "CE", "PAS"]),
  numero_documento: z.string().trim().min(1).max(20),
  nombres: z.string().trim().min(1).max(255),
  apellidos: z.string().trim().max(255),
  contacto_email: z.string().trim().max(255),
});

/** A line of the order with its FROZEN price (`PedidoLineaOut`). */
export const pedidoLineaSchema = z.object({
  tipo_concepto: codigo,
  concepto_id: z.string(),
  concepto_nombre: z.string(),
  cantidad: z.number().int(),
  precio_unitario: z.coerce.number(),
  precio_aplicado: z.coerce.number(),
  subtotal: z.coerce.number(),
});

/**
 * The order with its THREE facts (`PedidoSeguimientoOut`).
 *
 * `estado`, `estado_pago` and `estado_entrega` are DIFFERENT facts: a paid
 * order is still pending of delivery (`RN-M07`, `QA-M04`).
 */
export const pedidoSeguimientoSchema = z.object({
  id,
  estado: codigo,
  estado_pago: codigo,
  estado_entrega: codigo,
  total: z.coerce.number(),
  moneda: z.string().min(1).max(3),
  lineas: z.array(pedidoLineaSchema),
  orden_pago_id: id.nullable(),
  siguientes_acciones: z.array(z.string()),
  created_at: marcaTiempo,
});

/**
 * The answer of the creation of the order (`PedidoCreadoOut`).
 *
 * `token` travels ONLY here: it is the private link of the buyer and it is
 * not published in any listing.
 */
export const pedidoCreadoSchema = pedidoSeguimientoSchema.extend({
  token: z.string().min(1),
  recuperado: z.boolean(),
});

/** The Izipay provider session for a private marketplace order. */
export const izipayPreparacionPedidoSchema = z.object({
  transaction_id: z.string().min(1),
  order_number: z.string().min(1),
  token: z.string().min(1),
  merchant_code: z.string().min(1),
  amount: z.coerce.number().positive(),
  currency: z.string().min(1).max(3),
  buyer_email: z.string(),
  buyer_name: z.string(),
  buyer_surname: z.string(),
});

/** The signed callback relayed from Izipay without browser-side interpretation. */
export const izipayRespuestaPedidoSchema = z
  .object({
    transactionId: z.string().nullable().optional(),
    payMethod: z.string().nullable().optional(),
  })
  .catchall(z.unknown());

export const izipayConfirmacionPedidoSchema = z
  .object({
    transaction_id: z.string().nullable().optional(),
    transactionId: z.string().nullable().optional(),
    code: z.string().nullable().optional(),
    message: z.string().nullable().optional(),
    order_number: z.string().nullable().optional(),
    orderNumber: z.string().nullable().optional(),
    amount: z.string().nullable().optional(),
    currency: z.string().nullable().optional(),
    signature: z.string().nullable().optional(),
    payload_http: z.string().nullable().optional(),
    payloadHttp: z.string().nullable().optional(),
    response: izipayRespuestaPedidoSchema.nullable().optional(),
  })
  .catchall(z.unknown());

export const pagoConfirmadoPedidoSchema = z.object({
  orden_pago_id: id,
  transaccion_id: id.nullable(),
  pagada_en: z.string().nullable(),
  referencia: z.string().min(1),
  estado_orden: z.string().min(1),
  estado_operativo: z.object({
    codigo,
    etiqueta: z.string().min(1),
    descripcion: z.string().min(1),
  }),
  estado_activacion: z
    .object({
      codigo,
      etiqueta: z.string().min(1),
      descripcion: z.string().min(1),
      recuperable: z.boolean(),
      proxima_accion: z.string().nullable(),
    })
    .nullable(),
  ya_confirmado: z.boolean(),
  monto: z.coerce.number(),
  moneda: z.string().min(1).max(3),
});

export const transaccionPedidoSchema = z.object({
  transaction_id: z.string().min(1),
  status: z.string().min(1),
  response_message: z.string().min(1),
});

// ── Envelopes ────────────────────────────────────────────────────────────────

/** The envelope of the creation of the order. */
export const pedidoCreadoEnvelope = apiResponseSchema(pedidoCreadoSchema);

/** The envelope of the tracking of the order. */
export const pedidoSeguimientoEnvelope = apiResponseSchema(
  pedidoSeguimientoSchema,
);
export const izipayPreparacionPedidoEnvelope = apiResponseSchema(
  izipayPreparacionPedidoSchema,
);
export const pagoConfirmadoPedidoEnvelope = apiResponseSchema(
  pagoConfirmadoPedidoSchema,
);
export const transaccionPedidoEnvelope = apiResponseSchema(
  transaccionPedidoSchema,
);

// ── Inferred types ───────────────────────────────────────────────────────────

export type PedidoItem = z.infer<typeof pedidoItemSchema>;
export type CrearPedido = z.infer<typeof crearPedidoSchema>;
export type PedidoLinea = z.infer<typeof pedidoLineaSchema>;
export type PedidoSeguimiento = z.infer<typeof pedidoSeguimientoSchema>;
export type PedidoCreado = z.infer<typeof pedidoCreadoSchema>;
export type IzipayPreparacionPedido = z.infer<
  typeof izipayPreparacionPedidoSchema
>;
export type IzipayConfirmacionPedido = z.infer<
  typeof izipayConfirmacionPedidoSchema
>;
export type PagoConfirmadoPedido = z.infer<typeof pagoConfirmadoPedidoSchema>;
export type TransaccionPedido = z.infer<typeof transaccionPedidoSchema>;
