import { z } from "zod";
import {
  accionOperativaSchema,
  envelopeAdmin,
  envelopeAdminPaginado,
  estadoOperativoSchema,
} from "@/features/admin/operaciones/schemas/operaciones.schema";
import { veredictoDesdeEstadoOperativo } from "@/features/admin/operaciones/utils/veredicto.adapter";
import type {
  AdminPagoDetalleOut,
  AdminPagoListItemOut,
  CompraAdminOut,
  IntentoPagoAdminOut,
  OperacionManualAdminOut,
  PagoOperativoOut,
} from "../types/pagos-admin.types";

/**
 * The Zod mirrors of the ADMINISTRATION OF THE PAYMENTS.
 *
 * ## What they mirror
 *
 * The presenters the ledger declares (`RT-PG-04` -> `AdminPagoPresenter`,
 * `RT-PG-07` -> `AdminPagoDetallePresenter`, `RT-PG-06` ->
 * `PagoIntentosPresenter` and `RT-PG-05` -> `AdminPagoManualPresenter`),
 * with the shapes of the plan (`contratos/01` §4, admin).
 *
 * ## What they are NOT
 *
 * They are NOT the mirror of a live wrapper: `AdminPagoController` is NOT
 * registered in `Aplicacion/backend/config/api.py`, so `RT-PG-04`, `RT-PG-05`
 * and `RT-PG-07` do NOT exist, and `PagosController` does not expose
 * `/intentos`, so `RT-PG-06` does NOT exist either. They are the SEAM of the
 * contract (`A0-API04-05`).
 *
 * ## The THREE levels of the payment
 *
 * 1. the operational list — ONE understandable verdict per row;
 * 2. the commercial detail — what was bought and what it enabled;
 * 3. the diagnosis — the attempts of the provider and the manual operations.
 *
 * The levels are THREE facts and they are never mixed: the provider layer is
 * TEXT inside the diagnosis and it never inherits the verdict of the row
 * (`GOV-02-RB-06a`).
 *
 * ## The verdict is NEVER derived
 *
 * The `estado_operativo` of the wire is the FROZEN `EstadoOperativo` of the
 * backend. The browser NEVER crosses the state of the purchase, the state of
 * the order and the messages of the provider to decide whether a payment is
 * fine: the verdict has ONE owner and it is the backend
 * (`EstadoOperativoPagoService`).
 */

/** A reference to a record of the area. */
export const referenciaPagoSchema = z.object({
  id: z.string().min(1),
  nombre: z.string(),
});

/** The commercial purchase, as the operational presenter composes it. */
export const pagoOperativoSchema = z.object({
  compra_id: z.string().min(1),
  orden_pago_id: z.string().min(1).nullable(),
  tipo_compra: z.string().min(1),
  resumen_concepto: z.string(),
  comprador: z.object({
    persona_id: z.string().min(1),
    nombre: z.string(),
  }),
  monto: z.string(),
  moneda: z.string().min(1),
  estado_operativo: estadoOperativoSchema,
  entrega_derechos: z.object({
    codigo: z.string().min(1),
    etiqueta: z.string(),
  }),
  acciones_disponibles: z.array(z.string().min(1)),
});

/**
 * A row of the operational list (`RT-PG-04`).
 *
 * It is the canonical purchase plus the DATE that the list of the plan
 * requires (`frontend/04` §6).
 */
export const adminPagoListItemSchema = pagoOperativoSchema.extend({
  fecha: z.string().min(1),
});

/** An attempt of the provider, as `IntentoPagoOut` publishes it. */
export const intentoPagoAdminSchema = z.object({
  id: z.string().min(1),
  intento: z.number().int(),
  estado: z.string().min(1),
  verificada: z.boolean(),
  codigo_respuesta: z.string(),
  metodo_pago: z.string(),
  creada_en: z.string().min(1),
});

/** The purchase behind the payment. */
export const compraAdminSchema = z.object({
  id: z.string().min(1),
  estado: z.string().min(1),
  total: z.string(),
  moneda: z.string().min(1),
  reutilizada: z.boolean(),
});

/** A manual operation of an administrator over a payment. */
export const operacionManualAdminSchema = z.object({
  id: z.string().min(1),
  canal: z.string().min(1),
  monto: z.string(),
  moneda: z.string().min(1),
  motivo: z.string(),
  registrada_en: z.string().min(1),
  actor: z.string(),
});

/** The detail of a payment: the commercial level and the diagnosis. */
export const adminPagoDetalleSchema = pagoOperativoSchema.extend({
  compra: compraAdminSchema,
  origen_pago: z.string().min(1),
  intentos: z.array(intentoPagoAdminSchema),
  operaciones_manuales: z.array(operacionManualAdminSchema),
  siguiente_accion: accionOperativaSchema.nullable(),
});

/** The envelope of the operational list of the payments (`RT-PG-04`). */
export const listaPagosAdminEnvelope = envelopeAdminPaginado(
  adminPagoListItemSchema,
);

/** The envelope of the commercial detail of a payment (`RT-PG-07`). */
export const adminPagoDetalleEnvelope = envelopeAdmin(adminPagoDetalleSchema);

/**
 * The envelope of ONE operational payment.
 *
 * It is the answer that the manual approval (`RT-PG-05`) is expected to give:
 * the payment, updated. The wrapper `AdminPagoAprobarManualOut` of the ledger
 * is not published by the backend yet, so the reconciliation of the two is an
 * A0 request (`A0-API04-01`).
 */
export const pagoAdminItemEnvelope = envelopeAdmin(adminPagoListItemSchema);

// ── La proyección del wire al modelo de la vista ─────────────────────────────

/** The wire of a row of the operational list. */
export type AdminPagoListItemWire = z.infer<typeof adminPagoListItemSchema>;

/** The wire of an attempt of the provider. */
export type IntentoPagoAdminWire = z.infer<typeof intentoPagoAdminSchema>;

/** The wire of the purchase behind the payment. */
export type CompraAdminWire = z.infer<typeof compraAdminSchema>;

/** The wire of a manual operation. */
export type OperacionManualAdminWire = z.infer<typeof operacionManualAdminSchema>;

/** The wire of the detail of a payment. */
export type AdminPagoDetalleWire = z.infer<typeof adminPagoDetalleSchema>;

/** An attempt of the provider, as the view expects it. */
export function intentoPagoAdminDesdeWire(
  intento: IntentoPagoAdminWire,
): IntentoPagoAdminOut {
  return intento;
}

/** The purchase behind the payment, as the view expects it. */
export function compraAdminDesdeWire(compra: CompraAdminWire): CompraAdminOut {
  return compra;
}

/** A manual operation, as the view expects it. */
export function operacionManualAdminDesdeWire(
  operacion: OperacionManualAdminWire,
): OperacionManualAdminOut {
  return operacion;
}

/** A row of the operational list, as the view expects it. */
export function pagoAdminListaDesdeWire(
  fila: AdminPagoListItemWire,
): AdminPagoListItemOut {
  return {
    compra_id: fila.compra_id,
    orden_pago_id: fila.orden_pago_id,
    tipo_compra: fila.tipo_compra,
    resumen_concepto: fila.resumen_concepto,
    comprador: fila.comprador,
    monto: fila.monto,
    moneda: fila.moneda,
    estado_operativo: veredictoDesdeEstadoOperativo(fila.estado_operativo),
    entrega_derechos: fila.entrega_derechos,
    acciones_disponibles: fila.acciones_disponibles,
    fecha: fila.fecha,
  };
}

/** The detail of a payment, as the view expects it. */
export function pagoAdminDetalleDesdeWire(
  detalle: AdminPagoDetalleWire,
): AdminPagoDetalleOut {
  return {
    compra_id: detalle.compra_id,
    orden_pago_id: detalle.orden_pago_id,
    tipo_compra: detalle.tipo_compra,
    resumen_concepto: detalle.resumen_concepto,
    comprador: detalle.comprador,
    monto: detalle.monto,
    moneda: detalle.moneda,
    estado_operativo: veredictoDesdeEstadoOperativo(detalle.estado_operativo),
    entrega_derechos: detalle.entrega_derechos,
    acciones_disponibles: detalle.acciones_disponibles,
    compra: compraAdminDesdeWire(detalle.compra),
    origen_pago: detalle.origen_pago,
    intentos: detalle.intentos.map(intentoPagoAdminDesdeWire),
    operaciones_manuales: detalle.operaciones_manuales.map(
      operacionManualAdminDesdeWire,
    ),
    siguiente_accion: detalle.siguiente_accion,
  };
}
