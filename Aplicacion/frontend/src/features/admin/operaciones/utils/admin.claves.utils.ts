import type { QueryKey } from "@tanstack/react-query";
import {
  buildQueryKey,
  createDatasetQueryKeys,
} from "@/shared/utils/query-keys";

/**
 * The query keys of the administration area.
 *
 * They live HERE and nowhere else: a component never spells a key. ONE
 * dataset, ONE namespace: the root of a namespace is the invalidation target
 * of that dataset and of no other (`FND-08` §3 regla 1).
 *
 * | Dataset | Namespace | What it holds |
 * |---|---|---|
 * | the registrations | `admin.inscripciones` | `AdminInscripcionListItemOut` |
 * | the teams | `admin.equipos` | `AdminEquipoListItemOut` |
 * | the participants | `admin.participantes` | `AdminParticipanteListItemOut` |
 * | the payments | `admin.pagos` | `AdminPagoListItemOut` |
 *
 * ## What travels in the key
 *
 * EVERY parameter that changes the answer travels in the key, and a parameter
 * that is `undefined` is dropped, so `{page: 1}` and `{page: 1, q: undefined}`
 * are the SAME cache entry (`src/shared/utils/query-keys.ts`).
 *
 * The names of the parameters are the FROZEN query of `RT-PG-04`
 * (`page, page_size, q, ordering, estado_operativo, estado_compra,
 * estado_orden, tipo, desde, hasta`) plus the edition that scopes the area
 * (`path_o_edicion_id` in the ledger).
 *
 * The identifier of the RECORD travels in the key of a detail and the VERSION
 * travels in the key of a sensitive action: two versions of the same record
 * are two entries and never one.
 */

/**
 * The parameters that change the answer of an administrative list.
 *
 * It is a TYPE ALIAS and not an interface on purpose: the factory of the
 * shared query keys requires `Record<string, unknown>` and an interface
 * without an index signature does not satisfy it.
 */
export type ParamsListaAdmin = {
  /** The edition that scopes the list. */
  edicion_id?: string;
  /** The free text of the search. */
  q?: string;
  /** The ordering of the list. */
  ordering?: string;
  /** The filter by the operational verdict. */
  estado_operativo?: string;
  /** The filter by the state of the purchase. */
  estado_compra?: string;
  /** The filter by the state of the payment order. */
  estado_orden?: string;
  /** The filter by the origin of the purchase. */
  tipo?: string;
  /** The beginning of the range of dates. */
  desde?: string;
  /** The end of the range of dates. */
  hasta?: string;
  /**
   * The commercial balance of the inscription (`PENDIENTE` | `PAGADO`).
   *
   * Declared by the transversal summary (`XCT-02`): it is the drilldown that
   * takes an issue of the summary to the filtered records.
   */
  estado_pago?: string;
  /**
   * The completeness of the roster of the team (`INCOMPLETA` | `COMPLETA`).
   *
   * Declared by the transversal summary (`XCT-02`), for the same reason.
   */
  plantilla?: string;
  /**
   * The code of the audited action that scopes the acta.
   *
   * Declared by the transversal acta (`XCT-02`): it is the filter that
   * narrows the trail to one kind of sensitive action.
   */
  accion?: string;
  /** The page, 1-based. */
  page?: number;
  /** The size of the page. */
  page_size?: number;
};

/** The datasets of the administration area. */
export type DatasetAdmin =
  | "inscripciones"
  | "equipos"
  | "participantes"
  | "pagos"
  | "personas"
  | "resumen"
  | "auditoria";

export const adminClaves = {
  /** The root of the WHOLE area: the invalidation target of every dataset. */
  todas: ["admin"] as const,

  /** The registrations of the area. */
  inscripciones: createDatasetQueryKeys<ParamsListaAdmin>(
    "admin.inscripciones",
  ),

  /** The teams of the area. */
  equipos: createDatasetQueryKeys<ParamsListaAdmin>("admin.equipos"),

  /** The participants of the area. */
  participantes: createDatasetQueryKeys<ParamsListaAdmin>(
    "admin.participantes",
  ),

  /** The payments of the area. */
  pagos: createDatasetQueryKeys<ParamsListaAdmin>("admin.pagos"),

  /**
   * The administrative search of PEOPLE (`RT-ID-07` · `RT-ID-08`).
   *
   * It is ONE dataset with ONE namespace: the invalidation target of the
   * search is `admin.personas` and of nothing else.
   */
  personas: createDatasetQueryKeys<ParamsListaAdmin>("admin.personas"),

  /**
   * The transversal summary of the edition (`ADM-01`).
   *
   * It is ONE dataset with ONE namespace: the invalidation target of the
   * summary is `admin.resumen` and of nothing else.
   */
  resumen: createDatasetQueryKeys<ParamsListaAdmin>("admin.resumen"),

  /** The audit trail of the sensitive actions. */
  auditoria: createDatasetQueryKeys<ParamsListaAdmin>("admin.auditoria"),

  /**
   * The key of ONE sensitive action.
   *
   * The RECORD and its VERSION travel in it: an action over a record is not
   * the same entry as an action over another version of that record.
   */
  accion: (
    dataset: DatasetAdmin,
    registroId: string,
    version?: string,
  ): QueryKey =>
    buildQueryKey(["admin", dataset, "accion"], {
      registro_id: registroId,
      version,
    }),
} as const;
