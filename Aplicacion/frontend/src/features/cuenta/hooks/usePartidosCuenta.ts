"use client";

import { useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import { cuentaPartidosEnvelope } from "../schemas/cuenta-partidos.schema";
import { RUTA_PARTIDOS_CUENTA } from "../services/cuenta-partidos.service";

/**
 * The namespace of the matches of the account: `["cuenta", "partidos"]`.
 *
 * It lives with the rest of the account (`["cuenta", "compras"]`) and it is
 * the ONLY owner of this cache: no component spells the key.
 */
export const cuentaPartidosKey = ["cuenta", "partidos"] as const;

/**
 * The matches of the account.
 *
 * The URL comes from the client of the account and the answer is the mirror
 * of the wrapper the server publishes. It is a read of the ACCOUNT: it needs
 * a session and it resolves the identity on the server.
 */
export function usePartidosCuenta() {
  return useApiQuery({
    queryKey: cuentaPartidosKey,
    url: RUTA_PARTIDOS_CUENTA,
    schema: datosDelEnvelope(cuentaPartidosEnvelope),
    queryOptions: {
      staleTime: STALE_TIME.listadoAdministrativo,
      gcTime: gcTimeFor(STALE_TIME.listadoAdministrativo),
    },
  });
}
