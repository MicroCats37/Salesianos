/**
 * The view models of the ADMINISTRATIVE ASSISTED commands.
 *
 * They mirror 1:1 the presenters of the target backend
 * (`Aplicacion/backend/modules/administracion/presentation/schemas/admin_asistido_schemas.py`):
 * `ParticipanteAsistidoOut` and `CompraAsistidaOut`.
 *
 * No business rule lives here: the eligibility of a person, the price of a
 * purchase and the verdict of the payment are DECLARED by the backend.
 */

/** The participation that the administration just created. */
export interface ParticipanteAsistidoOut {
  participacion_id: string;
  persona_id: string;
  nombre: string;
  documento: string;
  equipo_id: string;
  inscripcion_id: string;
  rol: string;
  estado: string;
}

/**
 * The assisted purchase.
 *
 * `comprador_persona_id` and `comprador_nombre` are the CLIENT: the
 * administrator is the actor of the operation, never the owner of the
 * purchase.
 */
export interface CompraAsistidaOut {
  compra_id: string;
  recurso_id: string;
  orden_pago_id: string;
  /**
   * `PASE` or `PEDIDO`.
   *
   * It is a `string` and NOT an enum: the backend owns the vocabulary and a
   * new value must NOT break the whole read.
   */
  tipo: string;
  concepto: string;
  total: string;
  moneda: string;
  estado: string;
  estado_pago: string;
  comprador_persona_id: string;
  comprador_nombre: string;
  cantidad: number;
  /**
   * The amount the administrator DECLARED having received.
   *
   * It is the ECHO of the audited evidence and `null` means "not declared".
   * It is NOT the total: `total` is the amount the server froze, and the
   * declared amount never changes it.
   */
  monto_declarado: string | null;
}

/**
 * The civil identity of the client of an assisted purchase.
 *
 * `nombres`, `apellidos` and `genero` travel ONLY when the client has to be
 * REGISTERED: when the identity already exists, the padrón is the authority
 * and the server never rewrites its names. An empty string means "not
 * declared": the backend reads it as `null`.
 */
export interface ClienteCompraIn {
  tipo_documento: string;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  /** `""`, `"M"` or `"F"`. */
  genero: string;
  /** A contact datum of the PURCHASE: it never reaches the `Persona`. */
  contacto_email: string;
}

/** The evidence of the external payment that the administrator registers. */
export interface EvidenciaPagoManualIn {
  canal: string;
  referencia: string;
  motivo: string;
}

/**
 * The evidence of the assisted purchase of a PASS.
 *
 * It is the general evidence PLUS the declared amount and the token of the
 * quoted price. The CURRENCY is NOT declared: the server derives it from the
 * order, so the browser never sends one.
 */
export interface EvidenciaPagoCompraPaseIn {
  canal: string;
  referencia: string;
  motivo: string;
  /**
   * The amount the administrator declares having received.
   *
   * It is INFORMATIVE and AUDITED: it never becomes the price, the total,
   * the state of the payment or the state of the purchase. Its absence means
   * "not declared"; `"0"` is a valid declaration.
   */
  monto_declarado?: string | null;
  /**
   * The token of the price that the quotation published.
   *
   * When the server resolves a different price, it answers `409` with
   * `PRECIO_CAMBIADO` and nothing is created.
   */
  precio_version?: string | null;
}

/**
 * The QUOTATION of a pass for the assisted purchase.
 *
 * Every amount is the TEXT that the server published: the browser prints it
 * and NEVER multiplies a price by a quantity (`RN-C02`).
 */
export interface CotizacionPaseClienteOut {
  pase_id: string;
  edicion_id: string;
  pase_nombre: string;
  cantidad: number;
  /** The unit price, as TEXT with two decimals. */
  precio_unitario: string;
  /** The total of the quotation, as TEXT. The server derived it. */
  total: string;
  /** The ISO-4217 currency of the price. */
  moneda: string;
  /** The token of the price: the concurrency control of the quotation. */
  version: string;
  /** The state of the quotation (`ACTIVA`). */
  estado: string;
  /** The moment the quotation stops being valid. */
  validez_hasta: string;
}

/** The command that asks the server for the quotation of a pass. */
export interface CotizarPaseClienteIn {
  pase_id: string;
  cantidad: number;
}

/**
 * The command that adds a participant to a team.
 *
 * The person is identified by her EXACT document. The names, the surnames
 * and the gender are only used when she has to be REGISTERED.
 */
export interface AgregarParticipanteEquipoIn {
  tipo_documento: string;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  /** `""`, `"M"` or `"F"`. */
  genero: string;
  rol: string;
  motivo: string;
}

/** The command that buys passes for a client. */
export interface ComprarPaseClienteIn {
  pase_id: string;
  cantidad: number;
  cliente: ClienteCompraIn;
  evidencia: EvidenciaPagoCompraPaseIn;
}

/** One article of the assisted order of the store. */
export interface ItemPedidoClienteIn {
  tipo: string;
  producto_id: string;
  cantidad: number;
}

/** The command that orders the store for a client. */
export interface ComprarPedidoClienteIn {
  items: ItemPedidoClienteIn[];
  cliente: ClienteCompraIn;
  evidencia: EvidenciaPagoManualIn;
}
