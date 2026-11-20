import { createDatasetQueryKeys } from "@/shared/utils/query-keys";

/**
 * The query keys of the registration area.
 *
 * They live HERE and nowhere else: the literals of a key never travel to a
 * component. ONE dataset, ONE namespace: the root of a namespace is the
 * invalidation target of that dataset and of no other.
 *
 * The area owns FOUR datasets, and they do not share the `list`/`detail`
 * slots of the generic factory:
 *
 * | Dataset | Namespace | What it holds |
 * |---|---|---|
 * | the catalogue of packages | `inscripcion.catalogo.paquetes` | `CatalogoPaquetesOut` |
 * | the catalogue of disciplines | `inscripcion.catalogo.disciplinas` | `CatalogoDisciplinasOut` |
 * | the detail of a registration | `inscripcion.detalle` | `InscripcionDetalleOut` |
 * | the pool of a registration | `inscripcion.pool` | `PoolOut` |
 *
 * ## What travels in the key
 *
 * Every parameter that CHANGES the answer travels in the key, and a
 * parameter that is `undefined` is dropped, so `{edicion_id: undefined}` and
 * `{}` are the SAME cache entry (`src/shared/utils/query-keys.ts`).
 *
 * - The catalogue reads are EDITION-scoped: `edicion_id` travels in the key.
 * - The detail and the pool are REGISTRATION-scoped: the identifier of the
 *   registration travels in the key.
 * - **No filter and no page travel, because no registered endpoint of this
 *   area filters or paginates.** The catalogue is edition-scoped and
 *   complete, and the paginated read of the inscriptions (`RT-IN-01`,
 *   `GET /inscripciones`) is NOT implemented in the target backend. The
 *   `listPage(params)` slot of the generic factory is the reserved place for
 *   the frozen pagination shape when that route is ratified; until then a
 *   `page` in the key would create a SECOND cache entry for the SAME answer.
 */

/** The catalogue of packages of ONE edition. */
export const clavesCatalogoPaquetes = createDatasetQueryKeys<{
  edicion_id?: string;
}>("inscripcion.catalogo.paquetes");

/** The catalogue of disciplines of ONE edition. */
export const clavesCatalogoDisciplinas = createDatasetQueryKeys<{
  edicion_id?: string;
}>("inscripcion.catalogo.disciplinas");

/** The detail of ONE registration. */
export const clavesInscripcionDetalle = createDatasetQueryKeys("inscripcion.detalle");

/** The pool of ONE registration. */
export const clavesInscripcionPool = createDatasetQueryKeys("inscripcion.pool");
