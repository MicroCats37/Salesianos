import { apiSend } from "@/lib/api";
import type {
  EntregaConfirmada,
  EntregaEntregada,
  EntregaPendiente,
  InventarioProducto,
  MovimientoInventario,
  MovimientoInventarioFormData,
} from "../schemas/inventario.schema";
import {
  entregaConfirmadaEnvelope,
  entregasEnvelope,
  inventarioEnvelope,
  movimientoInventarioEnvelope,
} from "../schemas/inventario.schema";

/** The root of the routes of the inventory ledger. */
export const RUTA_INVENTARIO = "/administracion/marketplace/inventario";

/** The root of the routes of the physical handovers. */
export const RUTA_ENTREGAS = "/administracion/marketplace/entregas";

/** The route of the movements of stock. */
export function rutaMovimientosInventario(): string {
  return `${RUTA_INVENTARIO}/movimientos`;
}

/** The route of the confirmation of ONE handover. */
export function rutaConfirmarEntrega(pedidoId: string): string {
  return `${RUTA_ENTREGAS}/${encodeURIComponent(pedidoId)}/confirmar`;
}

async function respuesta<T>(
  promesa: Promise<{ status: number; data: unknown | null }>,
  esquema: {
    safeParse: (valor: unknown) => {
      success: boolean;
      data?: { success: boolean; data: T | null };
    };
  },
): Promise<T> {
  const { status, data } = await promesa;
  if (status === 204 || data === null)
    throw new Error("El servidor respondió sin datos.");
  const resultado = esquema.safeParse(data);
  if (
    !resultado.success ||
    !resultado.data?.success ||
    resultado.data.data === null
  ) {
    throw new Error(
      "La respuesta del servidor no cumple el contrato esperado.",
    );
  }
  return resultado.data.data;
}

export function listarInventario(): Promise<InventarioProducto[]> {
  return respuesta(
    apiSend<unknown>("get", RUTA_INVENTARIO),
    inventarioEnvelope,
  );
}

export function registrarMovimientoInventario(
  datos: MovimientoInventarioFormData,
): Promise<MovimientoInventario> {
  return respuesta(
    apiSend<unknown>("post", rutaMovimientosInventario(), datos),
    movimientoInventarioEnvelope,
  );
}

export function listarEntregas(): Promise<{
  pendientes: EntregaPendiente[];
  entregadas: EntregaEntregada[];
}> {
  return respuesta(apiSend<unknown>("get", RUTA_ENTREGAS), entregasEnvelope);
}

export function confirmarEntrega(pedidoId: string): Promise<EntregaConfirmada> {
  return respuesta(
    apiSend<unknown>("post", rutaConfirmarEntrega(pedidoId)),
    entregaConfirmadaEnvelope,
  );
}
