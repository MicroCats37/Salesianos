/**
 * The query keys of the module — the SINGLE source of truth of the cache.
 *
 * The read hooks build their key with this factory and the mutation hooks
 * invalidate the SAME keys: a write can never leave a stale bracket, a stale
 * detail, a stale list or a stale agenda behind
 * (`contract/next-app-architecture-contract.md` §4).
 */

/** The prefix of EVERY query of the module. */
export const CLAVES_COMPETENCIA_RAIZ = ["admin", "competencias"] as const;

/** The prefix of the queries of the list (its filters are part of the key). */
export const CLAVES_COMPETENCIA_LISTA = [
  ...CLAVES_COMPETENCIA_RAIZ,
  "lista",
] as const;

/** The prefix of the queries of the agenda (its filters are part of the key). */
export const CLAVES_COMPETENCIA_AGENDA = [
  ...CLAVES_COMPETENCIA_RAIZ,
  "agenda",
] as const;

/** The key of the list of competitions. */
export const claveCompetenciasLista = (filtros: Record<string, string>) =>
  [...CLAVES_COMPETENCIA_LISTA, filtros] as const;

/** The key of the detail of ONE competition. */
export const claveCompetenciaDetalle = (competenciaId: string) =>
  [...CLAVES_COMPETENCIA_RAIZ, "detalle", competenciaId] as const;

/** The key of the bracket of ONE competition. */
export const claveCompetenciaCuadro = (competenciaId: string) =>
  [...CLAVES_COMPETENCIA_RAIZ, "cuadro", competenciaId] as const;

/** The key of the agenda of ONE day. */
export const claveAgendaCompetencias = (filtros: Record<string, string>) =>
  [...CLAVES_COMPETENCIA_AGENDA, filtros] as const;
