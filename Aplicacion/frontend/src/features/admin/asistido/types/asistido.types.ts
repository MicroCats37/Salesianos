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
}

/** The civil identity of the client of an assisted purchase. */
export interface ClienteCompraIn {
  tipo_documento: string;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  contacto_email: string;
}

/** The evidence of the external payment that the administrator registers. */
export interface EvidenciaPagoManualIn {
  canal: string;
  referencia: string;
  motivo: string;
}

/** The command that adds an existing participant to a team. */
export interface AgregarParticipanteEquipoIn {
  tipo_documento: string;
  numero_documento: string;
  rol: string;
  motivo: string;
}

/** The command that buys passes for a client. */
export interface ComprarPaseClienteIn {
  pase_id: string;
  cantidad: number;
  cliente: ClienteCompraIn;
  evidencia: EvidenciaPagoManualIn;
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
