import type { QueryKey } from "@tanstack/react-query";

/**
 * The query keys of the PUBLIC surface of the encounters.
 *
 * Change: `partidos-marcadores-competencias` · Batch 2
 *
 * They live HERE and nowhere else: a component never spells a key. ONE
 * dataset, ONE namespace: the read of the public encounters is a family of
 * its own, INSIDE the namespace of the competitions, so an invalidation of the
 * competitions reaches it and a future realtime delta can be applied to the
 * very same cache entry.
 *
 * The read has NO parameters: the edition is resolved by the server
 * (`FR-02` §2.2), so a key with an edition would create a SECOND cache entry
 * for the SAME answer.
 */

/** The root of the namespace of the competitions. */
const COMPETENCIAS: QueryKey = ["competencias"];

/** The family of the PUBLIC reads of the competitions. */
const PUBLICO: QueryKey = [...COMPETENCIAS, "publico"];

/** The key of the public encounters (`GET /publico/competencias/encuentros`). */
export const claveEncuentrosPublicos = [...PUBLICO, "encuentros"] as const;
