import type {
  AccionOperativa,
  EstadoSuperficie,
  Veredicto,
} from "@/features/admin/operaciones";

/**
 * The view models of the administration of the payments.
 *
 * They mirror the PROPOSED presenters of the plan, which do NOT exist in the
 * target backend yet:
 *
 * - `AdminPagoPresenter` -> `AdminPagoListItemOut` (`RT-PG-04`,
 *   `GET /administracion/pagos`), FROZEN in GOV-01.
 * - `AdminPagoDetallePresenter` -> `AdminPagoDetalleOut` (`RT-PG-07`,
 *   `GET /administracion/pagos/{compra_id}`), provisional.
 * - `AdminPagoManualPresenter` -> `AdminPagoAprobarManualOut` (`RT-PG-05`,
 *   `POST /administracion/pagos/{orden_pago_id}/aprobar-manual`), FROZEN.
 * - `PagoIntentosPresenter` -> `PagoIntentosOut` (`RT-PG-06`,
 *   `GET /pagos/ordenes/{orden_id}/intentos`), provisional.
 *
 * NONE of the controllers is registered in `Aplicacion/backend/config/api.py`,
 * so these types are the SEAM where the real wrappers land in API-04.
 *
 * The verdict NEVER crosses the raw fields: the browser does not read the
 * state of the purchase, the state of the order and the messages of the
 * provider to decide whether a payment is fine (`GOV-02-RB-06a` ·
 * `contratos/01` §1.4).
 */

/**
 * A purchase, as the operational presenter composes it.
 *
 * `contratos/01` §4 · `FR-08` §2.4.
 */
export interface PagoOperativoOut {
  compra_id: string;
  orden_pago_id: string | null;
  /** The linked registration when the purchase originated in Inscripciones. */
  inscripcion_id: string | null;
  /** `INSCRIPCION`, `PASE` or `MARKETPLACE`. */
  tipo_compra: string;
  resumen_concepto: string;
  comprador: { persona_id: string; nombre: string };
  /** The amount as the server sends it: a string, never a number. */
  monto: string;
  /** The ISO-4217 code of the currency. */
  moneda: string;
  /** The verdict of the operator, with its cause. */
  estado_operativo: Veredicto;
  /** What the purchase granted. */
  entrega_derechos: { codigo: string; etiqueta: string };
  /** The codes of the actions the presenter projects. */
  acciones_disponibles: readonly string[];
}

/**
 * A row of the operational list (`RT-PG-04`).
 *
 * It is the canonical purchase plus the DATE that the list of the plan
 * requires (`frontend/04` §6: "Compra/orden, comprador, concepto, total,
 * fecha y un único estado comprensible").
 */
export interface AdminPagoListItemOut extends PagoOperativoOut {
  /** The date of the purchase, as the presenter formats it. */
  fecha: string;
}

/**
 * An attempt of the provider, as `IntentoPagoOut` publishes it.
 *
 * The reference of the provider does NOT travel: it is technical detail and
 * it belongs to the diagnosis (`FREEZE-PS-1.0.0`).
 */
export interface IntentoPagoAdminOut {
  id: string;
  /** The position of the attempt in its order. */
  intento: number;
  /** `PENDIENTE`, `EXITO`, `FALLIDO` or `CANCELADO`. */
  estado: string;
  /** Whether the evidence of the attempt was verified. */
  verificada: boolean;
  codigo_respuesta: string;
  metodo_pago: string;
  creada_en: string;
}

/** The purchase behind the payment, as the server publishes it. */
export interface CompraAdminOut {
  id: string;
  /** `PENDIENTE`, `PAGADA` or `CANCELADA`. */
  estado: string;
  total: string;
  moneda: string;
}

/** A manual operation of an administrator over a payment. */
export interface OperacionManualAdminOut {
  id: string;
  /** The channel of the manual confirmation. */
  canal: string;
  monto: string;
  moneda: string;
  motivo: string;
  registrada_en: string;
  actor: string;
}

/** The detail of a payment: the commercial level and the diagnosis. */
export interface AdminPagoDetalleOut extends PagoOperativoOut {
  /** The purchase behind the payment. It is NULLABLE: the backend may not have it. */
  compra: CompraAdminOut | null;
  /** `IZIPAY`, `MANUAL` or `SIN_PAGO`. */
  origen_pago: string;
  /** The attempts of the provider. Only visible under the diagnosis. */
  intentos: readonly IntentoPagoAdminOut[];
  /** The manual operations. Only visible under the diagnosis. */
  operaciones_manuales: readonly OperacionManualAdminOut[];
  /** The next permitted action, as the presenter named it. */
  siguiente_accion: AccionOperativa | null;
}

/** The state of the administrative list of payments. */
export type EstadoPagosAdmin = EstadoSuperficie<
  readonly AdminPagoListItemOut[]
>;

/** The state of the administrative detail of a payment. */
export type EstadoDetallePagoAdmin = EstadoSuperficie<AdminPagoDetalleOut>;
