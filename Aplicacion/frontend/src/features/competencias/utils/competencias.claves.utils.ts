import { createDatasetQueryKeys } from "@/shared/utils/query-keys";
import type { ConsultaCompetenciasParams } from "../types/competencia.types";

/**
 * The query keys of the competitions area.
 *
 * They live HERE and nowhere else: the literals of a key never travel to a
 * component. ONE dataset, ONE namespace: the root of the namespace is the
 * invalidation target of that dataset and of no other.
 *
 * ## What travels in the key
 *
 * EVERY parameter that CHANGES the answer travels in the key, and a
 * parameter that is `undefined` is dropped, so `{estado: undefined}` and `{}`
 * are the SAME cache entry (`src/shared/utils/query-keys.ts`).
 *
 * The list of competitions is FILTER-SCOPED: the filters of the URL
 * (`estado`, `categoria_id`) travel in the key. The edition does NOT travel:
 * the server resolves it (`FR-02` §2.2), so a key with an edition would
 * create a SECOND cache entry for the SAME answer.
 */
export const clavesCompetencias =
  createDatasetQueryKeys<ConsultaCompetenciasParams>("competencias");

export const claveCompetenciaDetalle = (competenciaId: string) =>
  [...clavesCompetencias.all, "detalle", competenciaId] as const;

export const claveCompetenciaCuadro = (competenciaId: string) =>
  [...clavesCompetencias.all, "cuadro", competenciaId] as const;

export const claveEquiposElegibles = (competenciaId: string) =>
  [...clavesCompetencias.all, "equipos-elegibles", competenciaId] as const;
