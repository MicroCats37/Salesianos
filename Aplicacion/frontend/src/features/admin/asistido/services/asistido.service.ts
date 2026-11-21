import {
  pedirAdmin,
  RUTAS_ADMIN,
} from "@/features/admin/operaciones/services/admin.service";
import {
  compraAsistidaEnvelope,
  participanteAsistidoEnvelope,
} from "../schemas/asistido.schema";
import type {
  AgregarParticipanteEquipoIn,
  CompraAsistidaOut,
  ComprarPaseClienteIn,
  ComprarPedidoClienteIn,
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
 * Buys a batch of passes FOR A CLIENT and registers its payment.
 *
 * The buyer is the client, never the administrator.
 */
export async function comprarPaseCliente(
  payload: ComprarPaseClienteIn,
): Promise<CompraAsistidaOut> {
  return pedirAdmin(RUTAS_ADMIN.comprarPaseCliente, compraAsistidaEnvelope, {
    payload: {
      pase_id: payload.pase_id,
      cantidad: payload.cantidad,
      cliente: { ...payload.cliente },
      evidencia: { ...payload.evidencia },
    },
  });
}

/**
 * Orders the store FOR A CLIENT and registers its payment.
 *
 * The buyer is the client, never the administrator.
 */
export async function comprarPedidoCliente(
  payload: ComprarPedidoClienteIn,
): Promise<CompraAsistidaOut> {
  return pedirAdmin(RUTAS_ADMIN.comprarPedidoCliente, compraAsistidaEnvelope, {
    payload: {
      items: payload.items.map((item) => ({ ...item })),
      cliente: { ...payload.cliente },
      evidencia: { ...payload.evidencia },
    },
  });
}
