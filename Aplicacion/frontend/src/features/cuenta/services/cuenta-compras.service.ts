import { api } from "@/lib/api";
import {
  compraCuentaDesdeWire,
  comprasCuentaEnvelopeSchema,
} from "../schemas/cuenta-compras.schema";
import type { CompraResumen } from "../types/cuenta.types";

/** The route of the commercial history of the account. */
export const RUTA_COMPRAS_CUENTA = "/cuenta/compras";

/** Reads the unified commercial history, including marketplace orders. */
export async function listarComprasCuenta(): Promise<CompraResumen[]> {
  const { data } = await api.get(RUTA_COMPRAS_CUENTA);
  const respuesta = comprasCuentaEnvelopeSchema.parse(data);
  return (respuesta.data ?? []).map(compraCuentaDesdeWire);
}
