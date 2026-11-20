"use client";

import { useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import {
  compraCuentaDesdeWire,
  comprasCuentaEnvelopeSchema,
} from "../schemas/cuenta-compras.schema";
import { RUTA_COMPRAS_CUENTA } from "../services/cuenta-compras.service";

export const cuentaComprasKey = ["cuenta", "compras"] as const;

/**
 * The commercial history of the account.
 *
 * It is the generic read of the area: the URL comes from the client of the
 * account and the answer is the mirror of the wrapper the server publishes.
 */
export function useComprasCuenta() {
  return useApiQuery({
    queryKey: cuentaComprasKey,
    url: RUTA_COMPRAS_CUENTA,
    schema: datosDelEnvelope(comprasCuentaEnvelopeSchema),
    queryOptions: {
      staleTime: STALE_TIME.listadoAdministrativo,
      gcTime: gcTimeFor(STALE_TIME.listadoAdministrativo),
      select: (datos) => datos.map(compraCuentaDesdeWire),
    },
  });
}
