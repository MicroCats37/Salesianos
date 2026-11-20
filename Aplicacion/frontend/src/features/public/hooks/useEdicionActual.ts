"use client";

import { apiQueryOptions, useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import {
  EDICION_ACTUAL_PATH,
  edicionActualResponseSchema,
} from "../services/edicion.service";
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
export const edicionActualQueryOptions = apiQueryOptions({
  queryKey: edicionClaves.actual(),
  url: EDICION_ACTUAL_PATH,
  schema: datosDelEnvelope(edicionActualResponseSchema),
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
  return useApiQuery({
    queryKey: edicionClaves.actual(),
    url: EDICION_ACTUAL_PATH,
    schema: datosDelEnvelope(edicionActualResponseSchema),
    queryOptions: {
      staleTime: STALE_TIME.catalogo,
      gcTime: gcTimeFor(STALE_TIME.catalogo),
    },
  });
}
