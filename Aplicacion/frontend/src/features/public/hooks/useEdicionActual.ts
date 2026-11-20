"use client";

import { useQuery } from "@tanstack/react-query";
import { datasetQueryOptions } from "@/shared/utils/query-options";
import { obtenerEdicionActual } from "../services/edicion.service";
import { edicionClaves } from "../utils/edicion.claves.utils";

/**
 * The `queryOptions` of the current edition.
 *
 * It is EXPORTED so a prefetch, a server-side hydration and the component read
 * share ONE cache entry (`salesianos-api-data`: "export `queryOptions` for
 * every read").
 *
 * The staleness is the one of a catalogue: the edition changes once per
 * season, so the read is fresh for ten minutes and its cache entry lives for
 * at least as long.
 */
export const edicionActualQueryOptions = datasetQueryOptions({
  queryKey: edicionClaves.actual(),
  queryFn: obtenerEdicionActual,
  kind: "catalogo",
});

/**
 * The current edition, as the backend publishes it.
 *
 * The hook NEVER resolves the edition by itself and it NEVER falls back to a
 * previous edition: the answer of the backend is the only answer. The states
 * (`S-01` loading, `S-02` empty, `S-04` error) belong to the component that
 * draws them.
 */
export function useEdicionActual() {
  return useQuery(edicionActualQueryOptions);
}
