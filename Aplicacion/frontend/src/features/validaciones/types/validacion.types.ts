/**
 * The view models of the validation area (`ADM-16`, `ADM-20`, `ADM-22`).
 *
 * The area has TWO operations that must never be confused:
 *
 * - the ENTRY of the party (`ADM-16`): a right of entry is checked at the
 *   door;
 * - the DELIVERY of the store (`ADM-20`): a paid order is checked at the
 *   counter of the pickup.
 *
 * Both read a credential, both PREVIEW before they confirm and both leave an
 * audit trail. They share the PRESENTATION of the preview and nothing else:
 * the subject of the entry is a right of entry and the subject of the
 * delivery is a paid order (`GOV-02-RB-08c`).
 *
 * THE CONTRACT IS NOT FROZEN YET, and that is a FACT of the backend, not an
 * omission: the module `validaciones` does not exist in the target, so
 * `TicketPreviewOut` and `TicketConfirmadoOut` have no presenter to mirror.
 * These types describe the SHAPE the views expect, and they are the seam
 * where the real wrappers will land (`A0-API05-02`).
 *
 * What IS frozen and IS mirrored — the wire mirror lives in
 * `schemas/validacion.schema.ts` — is:
 *
 * - the RIGHT of entry: `PaseBeneficiarioOut` of `DOM-03`
 *   (`Aplicacion/backend/modules/salesianos_fest/presentation/schemas/pase_schemas.py`),
 *   REUSED from `features/pases`, the owner of that wire shape;
 * - the PENDING DELIVERY: `EntregaPendienteOut` of `DOM-06`
 *   (`Aplicacion/backend/modules/marketplace/presentation/schemas/inventario_schemas.py`);
 * - the ERROR CODES of the two frozen routes `RT-RT-01` and `RT-RT-02`
 *   (`evidence/contracts/route-to-wrapper-ledger.csv`).
 *
 * No business rule lives here. A verdict, a remaining quantity, a
 * permission and a consumption are DECLARED by the backend and never derived
 * in the browser (`SH-01` T-03).
 */

/** The verdict of a validation, with the bucket that paints it. */
export type RolVeredictoValidacion =
  | "permitido"
  | "denegado"
  | "parcial"
  | "consumido"
  | "revocado"
  | "excedido"
  | "desconocido";

/** A fact of the backend with its label. */
export interface EstadoDeclarado {
  /** The machine code, exactly as the backend sent it. */
  codigo: string;
  /** The wording the operator reads. */
  etiqueta: string;
}

/** A verdict with the bucket that paints it. */
export interface VeredictoValidacion {
  estado: EstadoDeclarado;
  rol: RolVeredictoValidacion;
}

/**
 * The person who is the subject of a validation.
 *
 * It mirrors the identity fields of `PaseBeneficiarioOut`: the names, the
 * document and nothing else. The credential itself is NEVER rendered.
 */
export interface TitularValidacion {
  nombres: string;
  apellidos: string;
  tipo_documento: string;
  numero_documento: string;
}

/**
 * The right that a validation consumes.
 *
 * It mirrors the right fields of `PaseBeneficiarioOut`: the type, the state,
 * the units granted, the units consumed and the units still redeemable. The
 * numbers are the ones the backend published; the client never subtracts.
 */
export interface DerechoValidacion {
  /** The type of the right, as the backend named it. */
  tipo: string;
  /** The name of the right, as the backend named it. */
  nombre: string;
  /** The state of the right. */
  estado: string;
  /** The units the right grants. */
  cantidad_total: number;
  /** The units already redeemed. */
  cantidad_consumida: number;
  /** The units still redeemable. */
  cantidad_disponible: number;
  /** The moment the right was revoked, when it was. */
  revocado_en: string | null;
}

/**
 * The previous consumption of a credential.
 *
 * A ticket that was already used refuses a second consumption and shows the
 * previous record when the operator is authorised to see it (`SH-03` §4).
 */
export interface ConsumoPrevio {
  instante: string;
  punto: string;
  operador: string;
}

/**
 * VistaPreviaValidacion - the preview of ONE validation.
 *
 * It is the SAME contract for the entry and for the delivery: the reusable
 * presentation component of the area renders it and the two flows differ
 * only in the subject they read.
 *
 * The preview NEVER consumes. The confirm is a different action, with its
 * own state (`GOV-02-RB-05b` applied to the validation area).
 */
export interface VistaPreviaValidacion {
  /** Whether the backend admits the consumption right now. */
  puede_validar: boolean;
  /** The verdict of the preview, with its reason. */
  veredicto: VeredictoValidacion;
  /** The person the credential belongs to. */
  titular: TitularValidacion;
  /** The right that would be consumed. */
  derecho: DerechoValidacion;
  /** Where it happened: the point of control. */
  punto: string;
  /** Who is operating. */
  operador: string;
  /** When the preview was made. */
  instante: string;
  /** The previous consumption, when there was one and it may be shown. */
  consumo_previo?: ConsumoPrevio;
}

/**
 * ResultadoValidacion - the outcome of a CONFIRMED validation.
 *
 * It is what the audit will record, so it carries the operator, the point
 * and the instant of the confirmation.
 */
export interface ResultadoValidacion {
  /** Whether the credential was consumed. */
  validado: boolean;
  /** The verdict of the confirmation. */
  veredicto: VeredictoValidacion;
  /** The units consumed by this confirmation. */
  cantidad_consumida: number;
  /** The point of control. */
  punto: string;
  /** The operator. */
  operador: string;
  /** The instant of the confirmation. */
  instante: string;
  /**
   * Whether the confirmation was a REPLAY.
   *
   * The confirmation carries an idempotency key: repeating it never consumes
   * twice and the interface says that it was a replay instead of showing a
   * second consumption.
   */
  repetida: boolean;
}

/**
 * The subject of the DELIVERY operation.
 *
 * It mirrors `EntregaPendienteOut` of `DOM-06`: the paid order that still
 * waits for its pickup.
 */
export interface EntregaPendiente {
  pedido_id: string;
  /** Civil identity shown to the store operator. */
  comprador_nombres: string;
  comprador_apellidos: string;
  comprador_documento: string;
  /** The state of the order. */
  estado: string;
  /** The state of the delivery. */
  estado_entrega: string;
  /** The frozen total of the order. */
  total: number;
  /** The currency of the order. */
  moneda: string;
  /** The frozen lines of the order. */
  lineas: LineaPedido[];
  /** The instant the order was created. */
  created_at: string;
}

/** One line of a frozen order (`PedidoLineaOut` of `DOM-05`). */
export interface LineaPedido {
  tipo_concepto: string;
  concepto_id: string;
  concepto_nombre: string;
  cantidad: number;
  precio_unitario: number;
  precio_aplicado: number;
  subtotal: number;
}

/**
 * The two contexts of the audit.
 *
 * The audit is TRANSVERSAL: it lists the entries AND the pickups of the
 * store, and it never mixes them with a payment confirmation
 * (`GOV-02-RB-08c`).
 */
export type TipoValidacion = "ENTRADA" | "ENTREGA";

/**
 * One row of the audit (`AdminValidacionListItemOut`, `RT-VA-01`).
 *
 * The wrapper is PROVISIONAL: there is no `validaciones` module in the
 * target, so the row is the shape the view expects and the seam where the
 * real wrapper will land (`A0-UI05-02`, re-raised as `A0-API05-02`).
 */
export interface RegistroValidacion {
  id: string;
  /** The context of the row: an entry or a pickup. */
  tipo: TipoValidacion;
  /** The verdict of the validation, with its reason. */
  veredicto: VeredictoValidacion;
  /** The person the validation was about. */
  titular: TitularValidacion;
  /** The reference of the operation: the ticket or the order. */
  referencia: string;
  /** The point of control where it happened. */
  punto: string;
  /** The operator. */
  operador: string;
  /** The instant of the validation. */
  instante: string;
  /** The units consumed, when the operation consumed any. */
  cantidad: number;
}

/**
 * The state a route is in.
 *
 * The default of every view is `sin-datos`: the service is not connected
 * yet and the view says so instead of drawing a validation that does not
 * exist.
 */
export type EstadoVistaValidaciones =
  | "sin-datos"
  | "cargando"
  | "listo"
  | "sin-permiso"
  | "error";
