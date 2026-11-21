"use client";

import { apiQueryOptions, useApiQuery } from "@/hooks";
import { datosDelEnvelope } from "@/shared/utils/api-envelope";
import { gcTimeFor, STALE_TIME } from "@/shared/utils/query-options";
import { torneoPublicoEnvelope } from "../schemas/torneo-publico.schema";
import { RUTA_ENCUENTROS_PUBLICOS } from "../services/encuentro-publico.service";
import {
  claveEncuentrosPublicos,
  claveEncuentrosPublicosDe,
} from "../utils/encuentro-publico.claves.utils";

/**
 * The public encounters of the published edition.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * ## The staleness
 *
 * The state of a match changes WHILE the visitor watches: it is a live read,
 * so its staleness is the one of the live previews (`STALE_TIME.vivo`). This
 * batch does NOT poll: the read happens once per visit and the entry is
 * always eligible to be refreshed.
 *
 * ## The cache entry
 *
 * The entry holds the WHOLE public surface — the edition and the three
 * buckets — so a future realtime delta can be applied to the very same key
 * and every reader of the page sees it. The `version` of each encounter
 * travels in the parsed data for that purpose.
 */
export const encuentrosPublicosQueryOptions = () =>
  apiQueryOptions({
    queryKey: claveEncuentrosPublicos,
    url: RUTA_ENCUENTROS_PUBLICOS,
    schema: datosDelEnvelope(torneoPublicoEnvelope),
    kind: "vivo",
  });

/**
 * The read of the public encounters (`GET /publico/competencias/encuentros`).
 *
 * The route is ANONYMOUS: it publishes the state of the published edition to
 * a visitor without a session.
 */
export function useEncuentrosPublicos(competitionId?: string) {
  return useApiQuery({
    queryKey: claveEncuentrosPublicosDe(competitionId),
    url: competitionId
      ? `${RUTA_ENCUENTROS_PUBLICOS}?competition_id=${encodeURIComponent(competitionId)}`
      : RUTA_ENCUENTROS_PUBLICOS,
    schema: datosDelEnvelope(torneoPublicoEnvelope),
    queryOptions: {
      staleTime: STALE_TIME.vivo,
      gcTime: gcTimeFor(STALE_TIME.vivo),
    },
  });
}
