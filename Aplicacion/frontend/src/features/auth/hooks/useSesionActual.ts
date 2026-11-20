"use client";

import { useQuery } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import { obtenerSesionActual } from "../services/sesion.service";
import { authClaves } from "../utils/auth.claves.utils";

/**
 * The `queryOptions` of the current session.
 *
 * It is EXPORTED so a prefetch, a server-side hydration and the component read
 * share ONE cache entry.
 *
 * The staleness is the one of a transient state: the backend re-evaluates the
 * role and the capabilities on EVERY request, so the client keeps the facts for
 * a quarter of a minute and never decides them.
 */
export const sesionActualQueryOptions = datasetQueryOptions({
  queryKey: authClaves.sesion(),
  queryFn: obtenerSesionActual,
  kind: "comercial",
});

/**
 * The facts of the session of the authenticated actor.
 *
 * `enabled: false` skips the read when the server already knows that there is
 * no session: a request that is certain to answer `401` is not worth making.
 */
export function useSesionActual(options?: { enabled?: boolean }) {
  return useQuery({
    ...sesionActualQueryOptions,
    enabled: options?.enabled ?? true,
  });
}
