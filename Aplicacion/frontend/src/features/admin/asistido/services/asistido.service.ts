import {
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import {
  compraAsistidaEnvelope,
  cotizacionPaseClienteEnvelope,
  participanteAsistidoEnvelope,
} from "../schemas/asistido.schema";
import type {
  AgregarParticipanteEquipoIn,
  CompraAsistidaOut,
  ComprarPaseClienteIn,
  ComprarPedidoClienteIn,
  CotizacionPaseClienteOut,
  CotizarPaseClienteIn,
  ParticipanteAsistidoOut,
} from "../types/asistido.types";

/**
 * The client of the ADMINISTRATIVE ASSISTED commands.
 *
 * | Ledger | Method | URL | Wrapper |
 * |---|---|---|---|
 * | `A0-ACP-01` | POST | `/administracion/equipos/{equipo_id}/participantes` | `ParticipanteAsistidoOut` |
 * | `A0-ACP-02` | POST | `/administracion/pases/compras-cliente` | `CompraAsistidaOut` |
 * | `A0-ACP-03` | POST | `/administracion/marketplace/pedidos-cliente` | `CompraAsistidaOut` |
 * | `A0-ACP-04` | POST | `/administracion/pases/cotizacion` | `CotizacionPaseClienteOut` |
 *
 * ## What the browser NEVER does
 *
 * It never computes a price, never decides that a person may enter a team
 * and never declares the buyer: the client identity travels as DATA and the
 * backend resolves it against the padrón.
 */

/**
 * Adds a participant to the roster of a team.
 *
 * The person is identified by her EXACT document. The names, the surnames
 * and the gender travel ONLY when she has to be REGISTERED: when the
 * identity already exists, the padrón is the authority and the server never
 * rewrites its names. The command NEVER creates an ACCOUNT.
 */
export async function agregarParticipanteEquipo(
  equipoId: string,
  payload: AgregarParticipanteEquipoIn,
): Promise<ParticipanteAsistidoOut> {
  return pedirAdmin(
    RUTAS_ADMIN.agregarParticipanteEquipo,
    participanteAsistidoEnvelope,
    {
      pathParams: { equipo_id: equipoId },
      payload: {
        tipo_documento: payload.tipo_documento,
        numero_documento: payload.numero_documento,
        nombres: payload.nombres,
        apellidos: payload.apellidos,
        genero: payload.genero || null,
        rol: payload.rol,
        motivo: payload.motivo,
      },
    },
  );
}

/**
 * Asks the server for the QUOTATION of a pass.
 *
 * The server resolves the current price, derives the TOTAL and publishes the
 * token of that price. The browser NEVER multiplies a price by a quantity and
 * NEVER sends a total (`RN-C02`): the quotation is a READ, and it does not
 * live in the cache of TanStack Query (it is ephemeral: it belongs to the
 * pass AND the quantity that are on the screen right now).
 */
export async function cotizarPaseCliente(
  payload: CotizarPaseClienteIn,
): Promise<CotizacionPaseClienteOut> {
  return pedirAdmin(
    RUTAS_ADMIN.cotizarPaseCliente,
    cotizacionPaseClienteEnvelope,
    {
      payload: {
        pase_id: payload.pase_id,
        cantidad: payload.cantidad,
      },
    },
  );
}

/**
 * Buys a batch of passes FOR A CLIENT and registers its payment.
 *
 * The buyer is the client, never the administrator.
 *
 * The body carries NO price and NO total: the server freezes both against the
 * catalogue. The only amount that travels is the DECLARED one, and it is
 * informative evidence: it never becomes the price nor the total.
 */
export async function comprarPaseCliente(
  payload: ComprarPaseClienteIn,
): Promise<CompraAsistidaOut> {
  const evidencia: Record<string, unknown> = {
    canal: payload.evidencia.canal,
    referencia: payload.evidencia.referencia,
    motivo: payload.evidencia.motivo,
  };

  // An amount that was NOT declared does not travel: its absence already
  // means "not declared" on the server.
  if (payload.evidencia.monto_declarado) {
    evidencia.monto_declarado = payload.evidencia.monto_declarado;
  }

  // The token of the quoted price is the concurrency control of the command.
  if (payload.evidencia.precio_version) {
    evidencia.precio_version = payload.evidencia.precio_version;
  }

  return pedirAdmin(RUTAS_ADMIN.comprarPaseCliente, compraAsistidaEnvelope, {
    payload: {
      pase_id: payload.pase_id,
      cantidad: payload.cantidad,
      cliente: { ...payload.cliente },
      evidencia,
    },
  });
}

/**
 * Orders the store FOR A CLIENT and registers its payment.
 *
 * The buyer is the client, never the administrator.
 *
 * The evidence of the store is the GENERAL one: the declared amount and the
 * token of the price belong to the path of the PASSES and to nothing else
 * (`R6`). The body is built field by field so that nothing travels by
 * accident.
 */
export async function comprarPedidoCliente(
  payload: ComprarPedidoClienteIn,
): Promise<CompraAsistidaOut> {
  return pedirAdmin(RUTAS_ADMIN.comprarPedidoCliente, compraAsistidaEnvelope, {
    payload: {
      items: payload.items.map((item) => ({ ...item })),
      cliente: { ...payload.cliente },
      evidencia: {
        canal: payload.evidencia.canal,
        referencia: payload.evidencia.referencia,
        motivo: payload.evidencia.motivo,
      },
    },
  });
}
